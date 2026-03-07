"""ComfyUI client for generating images via API."""

import json
import uuid
import websocket
import urllib.request
import urllib.parse


class ComfyUIClient:
    """Client for communicating with ComfyUI server."""

    def __init__(self, server_address):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.ws = None

    def queue_prompt(self, prompt, client_id):
        """Queue a prompt for generation.

        Args:
            prompt: Workflow dict to execute
            client_id: Client identifier

        Returns:
            Response dict with prompt_id
        """
        p = {"prompt": prompt, "client_id": client_id}
        data = json.dumps(p).encode("utf-8")
        req = urllib.request.Request(f"{self.server_address}/prompt", data=data)
        return json.loads(urllib.request.urlopen(req).read())

    def get_image(self, filename, subfolder, folder_type):
        """Get generated image data.

        Args:
            filename: Image filename
            subfolder: Subfolder path
            folder_type: Image type (output, input, etc.)

        Returns:
            Image data as bytes
        """
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(
            f"{self.server_address}/view?{url_values}"
        ) as response:
            return response.read()

    def get_history(self, prompt_id):
        """Get generation history.

        Args:
            prompt_id: Prompt ID to get history for

        Returns:
            History dict
        """
        with urllib.request.urlopen(
            f"{self.server_address}/history/{prompt_id}"
        ) as response:
            return json.loads(response.read())

    def connect(self):
        """Connect to ComfyUI WebSocket."""
        ws_url = (
            self.server_address.replace("http://", "ws://")
            + f"/ws?clientId={self.client_id}"
        )
        self.ws = websocket.WebSocket()
        self.ws.connect(ws_url)

    def generate_image(self, workflow, text_input):
        """Generate an image from workflow and prompt.

        Args:
            workflow: ComfyUI workflow dict
            text_input: Prompt text to inject

        Returns:
            Image data as bytes or None if failed
        """
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
