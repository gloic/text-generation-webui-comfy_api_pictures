"""UI components for Gradio interface."""

import gradio as gr
from ..core.workflow import get_workflows


def create_ui_components(params):
    """Create all UI components.

    Args:
        params: Parameters dictionary

    Returns:
        Tuple of component references
    """
    workflows = get_workflows()
    with gr.Accordion("ComfyUI Generation", open=True):
        with gr.Column():
            with gr.Row():
                comfy_url = gr.Textbox(
                    label="ComfyUI Server URL", value=params["comfyui_url"]
                )
                selected_workflow = gr.Dropdown(
                    label="Workflow",
                    choices=workflows,
                    value=params["selected_workflow"]
                    if params["selected_workflow"]
                    and params["selected_workflow"] in workflows
                    else (workflows[0] if workflows else None),
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

            debug_checkbox = gr.Checkbox(label="Debug Mode", value=False)

            output_image = gr.HTML(label="Generated Image")

            return {
                "comfy_url": comfy_url,
                "selected_workflow": selected_workflow,
                "refresh_btn": refresh_btn,
                "mode": mode,
                "force_pic": force_pic,
                "suppr_pic": suppr_pic,
                "test_prompt": test_prompt,
                "generate_btn": generate_btn,
                "output_image": output_image,
                "debug_checkbox": debug_checkbox,
            }
