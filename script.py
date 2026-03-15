"""ComfyUI API Pictures Extension - Main entry point."""

from pathlib import Path
import gradio as gr
from modules import shared

from .core.client import ComfyUIClient
from .core.workflow import get_workflows, load_workflow
from .utils.helpers import generate_webui
from .modes import Mode, ManualMode, ImmersiveMode, PicturebookMode, TagProcessorMode
from .global_state import (
    picture_response,
    toggle_generation,
    debug_enabled,
    toggle_debug,
)

# Default params
params = {
    "comfyui_url": "http://127.0.0.1:8188",
    "selected_workflow": "",
    "mode": 0,  # modes of operation: 0 (Manual), 1 (Immersive), 2 (Picturebook), 3 (Process Tags)
    "debug": False,
}


def get_mode_instance(mode_index):
    """Get mode instance by index.

    Args:
        mode_index: Mode index (0-3)

    Returns:
        Mode instance
    """
    mode_classes = [
        ManualMode,
        ImmersiveMode,
        PicturebookMode,
        TagProcessorMode,
    ]
    return mode_classes[mode_index](
        params, picture_response, params.get("debug", False)
    )


def input_modifier(string):
    """Modify input text before sending to LLM.

    Args:
        string: Input text

    Returns:
        Modified text
    """
    mode = get_mode_instance(params["mode"])
    return mode.process_input(string)


def output_modifier(string, state):
    """Modify output text from LLM.

    Args:
        string: Output text
        state: Current state object

    Returns:
        Modified text (possibly with images)
    """
    mode = get_mode_instance(params["mode"])
    result = mode.process_output(string, state)

    from .utils.helpers import debug_log

    debug_log(
        f"[OUTPUT_MOD] Mode: {params['mode']}, picture_response: {picture_response}, result type: {type(result)}",
        debug=params.get("debug", False),
    )

    return result


def custom_css():
    """Load custom CSS."""
    with open(Path(__file__).parent / "style.css", "r", encoding="utf-8") as f:
        return f.read()


def custom_js():
    """Load custom JavaScript for gallery overlay."""
    with open(
        Path(__file__).parent / "javascript/gallery.js", "r", encoding="utf-8"
    ) as f:
        return f.read()


def ui():
    """Create UI components."""
    from pathlib import Path
    from .ui.components import create_ui_components

    components = create_ui_components(params)

    # Event handlers
    def on_refresh_workflows():
        new_list = get_workflows()
        return gr.Dropdown.update(
            choices=new_list, value=new_list[0] if new_list else None
        )

    components["refresh_btn"].click(
        on_refresh_workflows, outputs=components["selected_workflow"]
    )

    def on_generate_test(prompt, wf_name, url):
        from .utils.helpers import debug_log

        debug_log(
            f"[TEST CLICK] Workflow: '{wf_name}', URL: {url}, Prompt: '{prompt[:50]}...'",
            debug=params.get("debug", False),
        )
        return generate_webui(prompt, wf_name, url)

    components["generate_btn"].click(
        on_generate_test,
        inputs=[
            components["test_prompt"],
            components["selected_workflow"],
            components["comfy_url"],
        ],
        outputs=components["output_image"],
    )

    # Update params
    components["comfy_url"].change(
        lambda x: params.update({"comfyui_url": x}), components["comfy_url"], None
    )
    components["selected_workflow"].change(
        lambda x: params.update({"selected_workflow": x}),
        components["selected_workflow"],
        None,
    )

    def on_mode_select(x):
        params.update({"mode": x})
        return gr.update()

    components["mode"].select(on_mode_select, components["mode"], None)
    components["mode"].select(
        lambda x: toggle_generation(x > 1 and x < 3),
        inputs=components["mode"],
        outputs=None,
    )

    components["force_pic"].click(
        lambda x: toggle_generation(True), inputs=components["force_pic"], outputs=None
    )
    components["suppr_pic"].click(
        lambda x: toggle_generation(False), inputs=components["suppr_pic"], outputs=None
    )
    components["debug_checkbox"].change(
        lambda x: params.update({"debug": x}), components["debug_checkbox"], None
    )

    from .utils.helpers import debug_log

    debug_log(
        f"[INIT] Extension initialized. Mode: {params['mode']}, Workflow: '{params['selected_workflow']}'",
        debug=params.get("debug", False),
    )

    return [
        components["comfy_url"],
        components["selected_workflow"],
        components["refresh_btn"],
        components["mode"],
        components["force_pic"],
        components["suppr_pic"],
        components["test_prompt"],
        components["generate_btn"],
        components["output_image"],
        components["debug_checkbox"],
    ]
