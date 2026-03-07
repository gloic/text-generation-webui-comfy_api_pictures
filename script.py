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
import html
from PIL import Image

# Default params
params = {
    "comfyui_url": "http://127.0.0.1:8188",
    "selected_workflow": "",
    "mode": 0,  # modes of operation: 0 (Manual only), 1 (Immersive/Interactive - looks for words to trigger), 2 (Picturebook Adventure - Always on), 3 (Process Tags - parse and generate <image> tags)
    "prompt_prefix": "",
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
    print(f"[TEST MODE] Generating image with workflow: {workflow_name}")
    client = ComfyUIClient(url)
    workflow = load_workflow(workflow_name)
    if not workflow:
        print(f"[TEST MODE] ERROR: Workflow '{workflow_name}' not found")
        return None

    img_data = client.generate_image(workflow, prompt)
    if img_data:
        # Create a base64 string for display
        base64_img = base64.b64encode(img_data).decode("utf-8")
        return f'<img src="data:image/png;base64,{base64_img}" alt="Generated Image" />'
    return None


def parse_image_tags(text):
    """Parse <image>...</image> tags from text.

    If tags are HTML-escaped (&lt;image&gt;), unescape them first to get correct positions.

    Returns a list of tuples: [(prompt1, start_pos1, end_pos1), (prompt2, start_pos2, end_pos2), ...]
    """
    # Check if text contains escaped tags
    if "&lt;image&gt;" in text:
        # Unescape the entire text to get correct positions
        unescaped_text = html.unescape(text)
        pattern = r"<image>(.*?)</image>"
        matches = list(re.finditer(pattern, unescaped_text, re.DOTALL))
        print(f"[MODE 3] Found {len(matches)} tags in unescaped text")
    else:
        pattern = r"<image>(.*?)</image>"
        matches = list(re.finditer(pattern, text, re.DOTALL))
        print(f"[MODE 3] Found {len(matches)} tags in text")

    results = []
    for match in matches:
        prompt = match.group(1).strip()
        start_pos = match.start()
        end_pos = match.end()
        results.append((prompt, start_pos, end_pos))

    return results


def replace_image_tags_with_images(text, image_results):
    """Replace <image>...</image> tags with generated images.

    image_results: list of dicts with keys: 'prompt', 'image_data' (or None), 'success', 'start_pos', 'end_pos'
    Returns text with tags replaced by <img> tags or original text if failed.
    """
    if not image_results:
        return text

    # Check if text contains escaped tags - if so, work with unescaped version
    if "&lt;image&gt;" in text:
        import html

        unescaped_text = html.unescape(text)
        working_text = unescaped_text
    else:
        working_text = text

    # Sort results by position
    sorted_results = sorted(image_results, key=lambda x: x["start_pos"])

    # Build replacements with progress updates
    replacements = []
    for result in sorted_results:
        if result["image_data"]:
            base64_img = base64.b64encode(result["image_data"]).decode("utf-8")
            # Add image with newline for better display
            replacement = f'\n<img src="data:image/png;base64,{base64_img}" alt="Generated Image" />\n'
        else:
            # Keep original text if generation failed
            replacement = f"<image>{result['prompt']}</image>"
        replacements.append((result["start_pos"], result["end_pos"], replacement))

    # Apply replacements from end to start to preserve positions
    result_text = working_text
    for start_pos, end_pos, replacement in reversed(replacements):
        result_text = result_text[:start_pos] + replacement + result_text[end_pos:]

    return result_text


def generate_multiple_images_sequential(prompts, workflow_name, url):
    """Generate multiple images sequentially with progress updates.

    Args:
        prompts: list of prompt strings
        workflow_name: workflow JSON filename
        url: ComfyUI server URL

    Returns:
        list of dicts: [{'prompt': str, 'image_data': bytes or None, 'success': bool, 'start_pos': int, 'end_pos': int}, ...]
    """
    print(f"[MODE 3] Loading workflow: {workflow_name}")
    results = []
    client = ComfyUIClient(url)
    workflow = load_workflow(workflow_name)

    if not workflow:
        print(f"[MODE 3] ERROR: Workflow '{workflow_name}' not found!")
        for i, prompt in enumerate(prompts):
            results.append(
                {
                    "prompt": prompt,
                    "image_data": None,
                    "success": False,
                    "start_pos": 0,
                    "end_pos": 0,
                }
            )
        return results

    print(f"[MODE 3] Workflow loaded successfully with {len(workflow)} nodes")

    # Verify workflow has prompt placeholder
    has_prompt_placeholder = False
    for key, node in workflow.items():
        if "inputs" in node:
            for input_key, input_val in node["inputs"].items():
                if isinstance(input_val, str) and "YOUR PROMPT HERE" in input_val:
                    has_prompt_placeholder = True
                    print(f"[MODE 3] Found prompt placeholder in node {key}")
                    break
        if has_prompt_placeholder:
            break

    if not has_prompt_placeholder:
        print(f"[MODE 3] WARNING: No 'YOUR PROMPT HERE' placeholder found in workflow!")

    for idx, prompt in enumerate(prompts):
        print(f"[MODE 3] Generating image {idx + 1}/{len(prompts)}: '{prompt[:80]}...'")

        # Reload workflow for each generation to avoid modifying the same object
        workflow = load_workflow(workflow_name)
        if not workflow:
            print(f"[MODE 3] ERROR: Could not reload workflow '{workflow_name}'")
            results.append(
                {
                    "prompt": prompt,
                    "image_data": None,
                    "success": False,
                    "start_pos": 0,
                    "end_pos": 0,
                }
            )
            continue

        img_data = client.generate_image(workflow, prompt)

        if img_data:
            print(
                f"[MODE 3] Image {idx + 1} generated successfully ({len(img_data)} bytes)"
            )
            # Add small delay for better UX
            time.sleep(0.3)
        else:
            print(f"[MODE 3] Image {idx + 1} generation FAILED")

        results.append(
            {
                "prompt": prompt,
                "image_data": img_data,
                "success": img_data is not None,
                "start_pos": 0,  # Will be updated by caller
                "end_pos": 0,  # Will be updated by caller
            }
        )

    return results


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
            string = (
                "Please provide a detailed and vivid description of [subject]".replace(
                    "[subject]", subject
                )
            )
        else:
            string = "Please provide a detailed and vivid description of [subject]".replace(
                "[subject]",
                "your appearance, your surroundings and what you are doing right now",
            )

    return string


def output_modifier(string, state):
    global picture_response, params

    print(f"[DEBUG] output_modifier called. Current mode: {params['mode']}")

    # Mode 3: Process Tags - parse and generate <image> tags
    if params["mode"] == 3:
        print(
            f"[MODE 3] Processing image tags. Workflow: '{params['selected_workflow']}', URL: {params['comfyui_url']}"
        )
        print(f"[MODE 3] Raw string preview: {string[:200]}")
        print(f"[MODE 3] String contains '<image>': {'<image>' in string}")
        print(f"[MODE 3] String contains '&lt;image&gt;': {'&lt;image&gt;' in string}")

        tags = parse_image_tags(string)
        print(f"[MODE 3] Found {len(tags)} tags in response")

        if tags:
            prompts = [tag[0] for tag in tags]
            print(f"[MODE 3] Will generate {len(prompts)} image(s)")

            # Generate images sequentially
            results = generate_multiple_images_sequential(
                prompts, params["selected_workflow"], params["comfyui_url"]
            )

            # Update positions in results
            for i, (prompt, start_pos, end_pos) in enumerate(tags):
                results[i]["start_pos"] = start_pos
                results[i]["end_pos"] = end_pos

            # Replace tags with images
            string = replace_image_tags_with_images(string, results)
            print(f"[MODE 3] Completed processing {len(results)} images")

        return string

    # Existing modes (0, 1, 2)
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
        text = f"*Sends a picture which portrays: '{cleaned_string}'*"
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
            modes_list = [
                "Manual",
                "Immersive/Interactive",
                "Picturebook/Adventure",
                "Process Tags",
            ]
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

        print(
            f"[INIT] Extension initialized. Mode: {params['mode']}, Workflow: '{params['selected_workflow']}'"
        )

        # Event handlers
        def update_workflows():
            new_list = get_workflows()
            return gr.Dropdown.update(
                choices=new_list, value=new_list[0] if new_list else None
            )

        refresh_btn.click(update_workflows, outputs=selected_workflow)

        def on_generate_test(prompt, wf_name, url):
            print(
                f"[TEST CLICK] Workflow: '{wf_name}', URL: {url}, Prompt: '{prompt[:50]}...'"
            )
            return generate_webui(prompt, wf_name, url)

        generate_btn.click(
            on_generate_test,
            inputs=[test_prompt, selected_workflow, comfy_url],
            outputs=output_image,
        )

        # Log current workflow on test generation
        def log_workflow_on_test(prompt, wf_name, url):
            print(
                f"[TEST CLICK] Workflow: '{wf_name}', URL: {url}, Prompt: '{prompt[:50]}...'"
            )
            return generate_webui(prompt, wf_name, url)

        generate_btn.click(
            log_workflow_on_test,
            inputs=[test_prompt, selected_workflow, comfy_url],
            outputs=output_image,
        )

        # Update params
        comfy_url.change(lambda x: params.update({"comfyui_url": x}), comfy_url, None)
        selected_workflow.change(
            lambda x: params.update({"selected_workflow": x}), selected_workflow, None
        )
        mode.select(lambda x: params.update({"mode": x}), mode, None)
        mode.select(
            lambda x: toggle_generation(x > 1 and x < 3), inputs=mode, outputs=None
        )

        def on_mode_change(x):
            params.update({"mode": x})
            print(f"[UI MODE CHANGE] Mode set to {x} ({modes_list[x]})")
            print(f"[UI DEBUG] Current params: {params}")
            return gr.update()

        mode.select(on_mode_change, mode, None)

        force_pic.click(
            lambda x: toggle_generation(True), inputs=force_pic, outputs=None
        )
        suppr_pic.click(
            lambda x: toggle_generation(False), inputs=suppr_pic, outputs=None
        )
