"""UI event handlers for Gradio interface."""

import gradio as gr
from ..core.workflow import get_workflows
from ..utils.helpers import generate_webui


def create_update_workflows_handler(selected_workflow):
    """Create handler for workflow refresh button.

    Args:
        selected_workflow: Dropdown component reference

    Returns:
        Handler function
    """

    def update_workflows():
        new_list = get_workflows()
        return gr.Dropdown.update(
            choices=new_list, value=new_list[0] if new_list else None
        )

    return update_workflows


def create_on_generate_test_handler():
    """Create handler for test image generation button."""

    def on_generate_test(prompt, wf_name, url):
        print(
            f"[TEST CLICK] Workflow: '{wf_name}', URL: {url}, Prompt: '{prompt[:50]}...'"
        )
        return generate_webui(prompt, wf_name, url)

    return on_generate_test
