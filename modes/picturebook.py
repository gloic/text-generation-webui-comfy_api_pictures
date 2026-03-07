"""Picturebook mode - always generates images for every response."""

from .base import Mode
from ..utils.helpers import generate_webui


class PicturebookMode(Mode):
    """Mode 2: Picturebook/Adventure - always generates images."""

    def __init__(self, params, picture_response=None):
        self.params = params

    def process_input(self, text):
        """Picturebook mode doesn't modify input.

        Args:
            text: Input text

        Returns:
            Unmodified text
        """
        return text

    def process_output(self, text, state):
        """Process output - generates image for every response.

        Args:
            text: LLM output text
            state: Current state object

        Returns:
            Modified text with image
        """
        from ..global_state import picture_response

        if not picture_response:
            print(
                "[PICTUREBOOK MODE] picture_response is False, returning text unchanged"
            )
            return text

        workflow_name = self.params["selected_workflow"]
        url = self.params["comfyui_url"]

        print(f"[PICTUREBOOK MODE] Generating image...")
        print(f"[PICTUREBOOK MODE] Using workflow: '{workflow_name}'")
        print(f"[PICTUREBOOK MODE] Using URL: {url}")
        print(f"[PICTUREBOOK MODE] Last text: '{text[:100]}...'")

        image_html = generate_webui(text, workflow_name, url)

        if image_html:
            print("[PICTUREBOOK MODE] Image generated successfully")
            from ..global_state import toggle_generation

            toggle_generation(False)
            print("[PICTUREBOOK MODE] picture_response consumed, set to False")
            return f"{text}\n\n{image_html}"
        else:
            print("[PICTUREBOOK MODE] Image generation failed")
            return text
