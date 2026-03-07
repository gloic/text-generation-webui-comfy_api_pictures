"""Manual mode - generates images only when forced via button."""

from .base import Mode
from ..utils.helpers import generate_webui
from ..global_state import toggle_generation, picture_response


class ManualMode(Mode):
    """Mode 0: Manual - only generates when forced."""

    def __init__(self, params, picture_response=None):
        self.params = params

    def process_input(self, text):
        """Manual mode doesn't modify input.

        Args:
            text: Input text

        Returns:
            Unmodified text
        """
        return text

    def process_output(self, text, state):
        """Manual mode only generates if picture_response is True.

        Args:
            text: LLM output text
            state: Current state object

        Returns:
            Modified text with image if forced
        """
        if not picture_response:
            print("[MANUAL MODE] picture_response is False, returning text unchanged")
            return text

        workflow_name = self.params["selected_workflow"]
        url = self.params["comfyui_url"]

        print(f"[MANUAL MODE] Generating image...")
        print(f"[MANUAL MODE] Using workflow: '{workflow_name}'")
        print(f"[MANUAL MODE] Using URL: {url}")
        print(f"[MANUAL MODE] Last text: '{text[:100]}...'")

        image_html = generate_webui(text, workflow_name, url)

        # Consume picture_response after generation
        toggle_generation(False)

        if image_html:
            print("[MANUAL MODE] Image generated successfully")
            return f"{text}\n\n{image_html}"
        else:
            print("[MANUAL MODE] Image generation failed")
            return text
