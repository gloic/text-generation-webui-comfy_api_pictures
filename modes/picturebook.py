"""Picturebook mode - always generates images for every response."""

from .base import Mode
from ..utils.helpers import generate_webui


class PicturebookMode(Mode):
    """Mode 2: Picturebook/Adventure - always generates images."""

    def __init__(self, params, picture_response=None, debug=False):
        super().__init__(params, picture_response, debug)

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
            from ..utils.helpers import debug_log

            debug_log(
                "[PICTUREBOOK MODE] picture_response is False, returning text unchanged",
                debug=self.debug,
            )
            return text

        workflow_name = self.params["selected_workflow"]
        url = self.params["comfyui_url"]

        from ..utils.helpers import debug_log

        debug_log(f"[PICTUREBOOK MODE] Generating image...", debug=self.debug)
        debug_log(
            f"[PICTUREBOOK MODE] Using workflow: '{workflow_name}'", debug=self.debug
        )
        debug_log(f"[PICTUREBOOK MODE] Using URL: {url}", debug=self.debug)
        debug_log(f"[PICTUREBOOK MODE] Last text: '{text[:100]}...'", debug=self.debug)

        image_html = generate_webui(text, workflow_name, url)

        from ..utils.helpers import debug_log

        if image_html:
            debug_log(
                "[PICTUREBOOK MODE] Image generated successfully", debug=self.debug
            )
            from ..global_state import toggle_generation

            toggle_generation(False)
            debug_log(
                "[PICTUREBOOK MODE] picture_response consumed, set to False",
                debug=self.debug,
            )
            return f"{text}\n\n{image_html}"
        else:
            debug_log("[PICTUREBOOK MODE] Image generation failed", debug=self.debug)
            return text
