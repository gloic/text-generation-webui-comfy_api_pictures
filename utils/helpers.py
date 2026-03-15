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

    result = client.generate_image(workflow, prompt)
    if result:
        if isinstance(result, tuple):
            img_data, original_filename = result
        else:
            img_data = result
            original_filename = None

        # Create a base64 string for display
        base64_img = base64.b64encode(img_data).decode("utf-8")

        # Generate filename with timestamp
        from ..utils.image_naming import generate_image_filename

        filename = generate_image_filename()

        return f'<img src="data:image/png;base64,{base64_img}" alt="{filename}" data-filename="{filename}" data-index="0" class="comfy-generated-image" style="max-width: 100%; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); cursor: pointer; transition: transform 0.2s;" />'
    return None
