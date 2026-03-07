"""Utility functions for image generation and conversion."""

import json
import base64
from ..core.workflow import load_workflow


def debug_log(message, debug=False):
    """Print debug message if debug mode is enabled.

    Args:
        message: Message to print
        debug: Debug flag
    """
    if debug:
        print(message)


def generate_webui(prompt, workflow_name, url):
    """Generate an image via ComfyUI and return HTML img tag.

    Args:
        prompt: Image generation prompt
        workflow_name: Workflow JSON filename
        url: ComfyUI server URL

    Returns:
        HTML img tag string or None if generation failed
    """
    from ..core.client import ComfyUIClient

    debug_log(
        f"[TEST MODE] Generating image with workflow: {workflow_name}", debug=False
    )
    client = ComfyUIClient(url)
    workflow = load_workflow(workflow_name)
    if not workflow:
        debug_log(
            f"[TEST MODE] ERROR: Workflow '{workflow_name}' not found", debug=False
        )
        return None

    img_data = client.generate_image(workflow, prompt)
    if img_data:
        # Create a base64 string for display
        base64_img = base64.b64encode(img_data).decode("utf-8")
        return f'<img src="data:image/png;base64,{base64_img}" alt="Generated Image" />'
    return None
