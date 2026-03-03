import json
import uuid
import websocket
import urllib.request
import urllib.parse
from pathlib import Path
import gradio as gr
from modules import shared
import re
import time
import base64
import io
from PIL import Image

# Default params
params = {
    "comfyui_url": "http://127.0.0.1:8188",
    "selected_workflow": "Qwen-image-Rapid-AIO.json",
    "mode": 0,  # modes of operation: 0 (Manual only), 1 (Immersive/Interactive - looks for words to trigger), 2 (Picturebook Adventure - Always on)
    "prompt_prefix": "",
    "textgen_prefix": "Please provide a detailed and vivid description of [subject]",
}

picture_response = (
    False  # specifies if the next model response should appear as a picture
)


class ComfyUIClient:
    def __init__(self, server_address):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.ws = None

    def queue_prompt(self, prompt, client_id):
        p = {"prompt": prompt, "client_id": client_id}
        data = json.dumps(p).encode("utf-8")
        req = urllib.request.Request(f"{self.server_address}/prompt", data=data)
        return json.loads(urllib.request.urlopen(req).read())

    def get_image(self, filename, subfolder, folder_type):
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(
            f"{self.server_address}/view?{url_values}"
        ) as response:
            return response.read()

    def get_history(self, prompt_id):
        with urllib.request.urlopen(
            f"{self.server_address}/history/{prompt_id}"
        ) as response:
            return json.loads(response.read())

    def connect(self):
        ws_url = (
            self.server_address.replace("http://", "ws://")
            + f"/ws?clientId={self.client_id}"
        )
        self.ws = websocket.WebSocket()
        self.ws.connect(ws_url)

    def generate_image(self, workflow, text_input):
        try:
            import random

            if not self.ws or not self.ws.connected:
                self.connect()

            # 1. Inject Prompt
            prompt_id_node = None
            for key, node in workflow.items():
                if "inputs" in node:
                    for input_key, input_val in node["inputs"].items():
                        if (
                            isinstance(input_val, str)
                            and "YOUR PROMPT HERE" in input_val
                        ):
                            prompt_id_node = key
                            break
                if prompt_id_node:
                    break

            if prompt_id_node:
                workflow[prompt_id_node]["inputs"]["prompt"] = text_input
            else:
                raise ValueError(
                    "No node with 'YOUR PROMPT HERE' found in workflow. "
                    "Please add this placeholder to the desired prompt node in your workflow JSON."
                )

            # 2. Fix Seed
            for key, node in workflow.items():
                if "inputs" in node and "seed" in node["inputs"]:
                    # Always randomize seed to ensure new images
                    workflow[key]["inputs"]["seed"] = random.randint(1, 1000000000)

            prompt_id = self.queue_prompt(workflow, self.client_id)["prompt_id"]

            output_images = []
            while True:
                out = self.ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message["type"] == "executing":
                        data = message["data"]
                        if data["node"] is None and data["prompt_id"] == prompt_id:
                            break  # Execution is done
                else:
                    continue

            history = self.get_history(prompt_id)[prompt_id]
            for o in history["outputs"]:
                for node_id in history["outputs"]:
                    node_output = history["outputs"][node_id]
                    if "images" in node_output:
                        for image in node_output["images"]:
                            image_data = self.get_image(
                                image["filename"], image["subfolder"], image["type"]
                            )
                            output_images.append(image_data)

            return output_images[0] if output_images else None

        except Exception as e:
            print(f"Error calling ComfyUI: {e}")
            return None


def get_workflows():
    workflow_path = Path(__file__).parent / "workflows"
    if not workflow_path.exists():
        return []
    return [f.name for f in workflow_path.glob("*.json")]


def load_workflow(workflow_name):
    workflow_path = Path(__file__).parent / "workflows" / workflow_name
    if not workflow_path.exists():
        return None
    with open(workflow_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_webui(prompt, workflow_name, url):
    client = ComfyUIClient(url)
    workflow = load_workflow(workflow_name)
    if not workflow:
        return None

    img_data = client.generate_image(workflow, prompt)
    if img_data:
        # Create a base64 string for display
        base64_img = base64.b64encode(img_data).decode("utf-8")
        return f'<img src="data:image/png;base64,{base64_img}" alt="Generated Image" />'
    return None


def remove_surrounded_chars(string):
    # this expression matches to 'as few symbols as possible (0 upwards) between any asterisks' OR
    # 'as few symbols as possible (0 upwards) between an asterisk and the end of the string'
    return re.sub("\*[^\*]*?(\*|$)", "", string)


def triggers_are_in(string):
    string = remove_surrounded_chars(string)
    # regex searches for send|main|message|me (at the end of the word) followed by
    # a whole word of image|pic|picture|photo|snap|snapshot|selfie|meme(s),
    # (?aims) are regex parser flags
    return bool(
        re.search(
            "(?aims)(send|mail|message|me)\\b.+ ?\\b(image|pic(ture)?|photo|snap(shot)?|selfie|meme)s?\\b",
            string,
        )
    )


def toggle_generation(*args):
    global picture_response, shared

    if not args:
        picture_response = not picture_response
    else:
        picture_response = args[0]

    shared.processing_message = (
        "*Is sending a picture...*" if picture_response else "*Is typing...*"
    )


def input_modifier(string):
    global params

    if not params["mode"] == 1:  # if not in immersive/interactive mode, do nothing
        return string

    if triggers_are_in(string):  # if we're in it, check for trigger words
        toggle_generation(True)
        string = string.lower()
        if "of" in string:
            subject = string.split(
                "of", 1
            )[
                1
            ]  # subdivide the string once by the first 'of' instance and get what's coming after it
            string = params["textgen_prefix"].replace("[subject]", subject)
        else:
            string = params["textgen_prefix"].replace(
                "[subject]",
                "your appearance, your surroundings and what you are doing right now",
            )

    return string


def output_modifier(string, state):
    global picture_response, params

    if not picture_response:
        return string

    cleaned_string = remove_surrounded_chars(string)
    cleaned_string = cleaned_string.replace('"', "")
    cleaned_string = cleaned_string.replace("“", "")
    cleaned_string = cleaned_string.replace("\n", " ")
    cleaned_string = cleaned_string.strip()

    if cleaned_string == "":
        cleaned_string = "no viable description in reply, try regenerating"
        return string

    text = ""
    if params["mode"] < 2:
        toggle_generation(False)
        text = f"*Sends a picture which portrays: “{cleaned_string}”*"
    else:
        text = cleaned_string

    img_tag = generate_webui(
        cleaned_string, params["selected_workflow"], params["comfyui_url"]
    )
    if img_tag:
        string = img_tag + "\n" + text

    return string


def custom_css():
    with open(Path(__file__).parent / "style.css", "r", encoding="utf-8") as f:
        return f.read()


def ui():
    with gr.Column():
        gr.Markdown("## ComfyUI Generation")
        with gr.Row():
            comfy_url = gr.Textbox(
                label="ComfyUI Server URL", value=params["comfyui_url"]
            )
            workflow_list = get_workflows()
            selected_workflow = gr.Dropdown(
                label="Workflow",
                choices=workflow_list,
                value=params["selected_workflow"]
                if params["selected_workflow"] in workflow_list
                else (workflow_list[0] if workflow_list else None),
            )
            refresh_btn = gr.Button("Refresh Workflows")

        with gr.Row():
            modes_list = ["Manual", "Immersive/Interactive", "Picturebook/Adventure"]
            mode = gr.Dropdown(
                modes_list,
                value=modes_list[params["mode"]],
                label="Mode of operation",
                type="index",
            )

        with gr.Row():
            force_pic = gr.Button("Force the picture response")
            suppr_pic = gr.Button("Suppress the picture response")

        with gr.Row():
            test_prompt = gr.Textbox(
                label="Test Prompt", placeholder="Enter prompt here..."
            )
            generate_btn = gr.Button("Generate Test Image")

        output_image = gr.HTML(label="Generated Image")

        # Event handlers
        def update_workflows():
            new_list = get_workflows()
            return gr.Dropdown.update(
                choices=new_list, value=new_list[0] if new_list else None
            )

        refresh_btn.click(update_workflows, outputs=selected_workflow)

        def on_generate_test(prompt, wf_name, url):
            return generate_webui(prompt, wf_name, url)

        generate_btn.click(
            on_generate_test,
            inputs=[test_prompt, selected_workflow, comfy_url],
            outputs=output_image,
        )

        # Update params
        comfy_url.change(lambda x: params.update({"comfyui_url": x}), comfy_url, None)
        selected_workflow.change(
            lambda x: params.update({"selected_workflow": x}), selected_workflow, None
        )
        mode.select(lambda x: params.update({"mode": x}), mode, None)
        mode.select(lambda x: toggle_generation(x > 1), inputs=mode, outputs=None)

        force_pic.click(
            lambda x: toggle_generation(True), inputs=force_pic, outputs=None
        )
        suppr_pic.click(
            lambda x: toggle_generation(False), inputs=suppr_pic, outputs=None
        )
