import json
import uuid
import websocket
import urllib.request
import urllib.parse
from pathlib import Path
import gradio as gr
from modules import shared

# Default params
params = {
    'comfyui_url': 'http://127.0.0.1:8188',
    'selected_workflow': 'Qwen-image-Rapid-AIO.json',
}

class ComfyUIClient:
    def __init__(self, server_address):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.ws = None

    def queue_prompt(self, prompt, client_id):
        p = {"prompt": prompt, "client_id": client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(f"{self.server_address}/prompt", data=data)
        return json.loads(urllib.request.urlopen(req).read())

    def get_image(self, filename, subfolder, folder_type):
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(f"{self.server_address}/view?{url_values}") as response:
            return response.read()

    def get_history(self, prompt_id):
        with urllib.request.urlopen(f"{self.server_address}/history/{prompt_id}") as response:
            return json.loads(response.read())

    def connect(self):
        ws_url = self.server_address.replace("http://", "ws://") + f"/ws?clientId={self.client_id}"
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
                        if isinstance(input_val, str) and "YOUR PROMPT HERE" in input_val:
                            # Found the placeholder
                            prompt_id_node = key
                            pass
            
            if prompt_id_node:
                # Replace exact string or just set it
                # Assuming the user wants the whole prompt replaced
                workflow[prompt_id_node]["inputs"]["prompt"] = text_input
            else:
                # Fallback to heuristic
                for key, node in workflow.items():
                    if "inputs" in node and "prompt" in node["inputs"]:
                         if "TextEncode" in node["class_type"]:
                            prompt_id_node = key
                            workflow[prompt_id_node]["inputs"]["prompt"] = text_input
                            break
                if not prompt_id_node:
                    print("Could not find a node to inject prompt into.")

            # 2. Fix Seed
            for key, node in workflow.items():
                if "inputs" in node and "seed" in node["inputs"]:
                    # Always randomize seed to ensure new images
                    workflow[key]["inputs"]["seed"] = random.randint(1, 1000000000)

            prompt_id = self.queue_prompt(workflow, self.client_id)['prompt_id']

            prompt_id = self.queue_prompt(workflow, self.client_id)['prompt_id']
            
            output_images = []
            while True:
                out = self.ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            break # Execution is done
                else:
                    continue

            history = self.get_history(prompt_id)[prompt_id]
            for o in history['outputs']:
                for node_id in history['outputs']:
                    node_output = history['outputs'][node_id]
                    if 'images' in node_output:
                        for image in node_output['images']:
                            image_data = self.get_image(image['filename'], image['subfolder'], image['type'])
                            output_images.append(image_data)
            
            return output_images[0] if output_images else None

        except Exception as e:
            print(f"Error calling ComfyUI: {e}")
            return None

def get_workflows():
    workflow_path = Path(__file__).parent / 'comfyui' / 'workflows'
    if not workflow_path.exists():
        return []
    return [f.name for f in workflow_path.glob('*.json')]

def load_workflow(workflow_name):
    workflow_path = Path(__file__).parent / 'comfyui' / 'workflows' / workflow_name
    if not workflow_path.exists():
        return None
    with open(workflow_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_webui(prompt, workflow_name, url):
    client = ComfyUIClient(url)
    workflow = load_workflow(workflow_name)
    if not workflow:
        return None
    
    img_data = client.generate_image(workflow, prompt)
    if img_data:
        # Save temporarily or return bytes directly if gradio supports it (it usually expects file path or numpy/PIL)
        # Using a temp file for safety
        temp_path = Path('extensions/comment_feature/last_generated.png')
        with open(temp_path, 'wb') as f:
            f.write(img_data)
        return str(temp_path)
    return None


#def custom_js():
#    with open(Path(__file__).parent / 'javascript' / 'script.js', 'r', encoding='utf-8') as f:
#        return f.read()

def custom_css():
    with open(Path(__file__).parent / 'style.css', 'r', encoding='utf-8') as f:
        return f.read()

def ui():
    with gr.Column():
        gr.Markdown("## ComfyUI Generation")
        with gr.Row():
            comfy_url = gr.Textbox(label="ComfyUI Server URL", value=params['comfyui_url'])
            workflow_list = get_workflows()
            selected_workflow = gr.Dropdown(label="Workflow", choices=workflow_list, value=params['selected_workflow'] if params['selected_workflow'] in workflow_list else (workflow_list[0] if workflow_list else None))
            refresh_btn = gr.Button("Refresh Workflows")
        
        with gr.Row():
            test_prompt = gr.Textbox(label="Test Prompt", placeholder="Enter prompt here...")
            generate_btn = gr.Button("Generate")
        
        output_image = gr.Image(label="Generated Image", type="filepath", elem_id="comfy_output_image")

        # Hidden elements for JS interaction
        hidden_prompt = gr.Textbox(elem_id="comfy_hidden_prompt", visible=False)
        hidden_trigger = gr.Button(elem_id="comfy_hidden_trigger", visible=False)
        
        # Event handlers
        def update_workflows():
            new_list = get_workflows()
            return gr.Dropdown.update(choices=new_list, value=new_list[0] if new_list else None)

        refresh_btn.click(update_workflows, outputs=selected_workflow)
        
        def on_generate(prompt, wf_name, url):
            return generate_webui(prompt, wf_name, url)

        generate_btn.click(on_generate, inputs=[test_prompt, selected_workflow, comfy_url], outputs=output_image)
        hidden_trigger.click(on_generate, inputs=[hidden_prompt, selected_workflow, comfy_url], outputs=output_image)

        # Update params
        comfy_url.change(lambda x: params.update({'comfyui_url': x}), comfy_url, None)
        selected_workflow.change(lambda x: params.update({'selected_workflow': x}), selected_workflow, None)
