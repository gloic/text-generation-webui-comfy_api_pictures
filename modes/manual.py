"""Manual mode - generates images only when forced via button."""

from .base import Mode
from ..utils.helpers import generate_webui
from ..global_state import toggle_generation


class ManualMode(Mode):
    """Mode 0: Manual - only generates when forced."""

    def __init__(self, params, picture_response=None, debug=False):
        super().__init__(params, picture_response, debug)

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
        if not self.picture_response:
            from ..utils.helpers import debug_log

            debug_log(
                "[MANUAL MODE] picture_response is False, returning text unchanged",
                debug=self.debug,
            )
            return text

        workflow_name = self.params["selected_workflow"]
        url = self.params["comfyui_url"]

        from ..utils.helpers import debug_log

        debug_log(f"[MANUAL MODE] Generating image...", debug=self.debug)
        debug_log(f"[MANUAL MODE] Using workflow: '{workflow_name}'", debug=self.debug)
        debug_log(f"[MANUAL MODE] Using URL: {url}", debug=self.debug)
        debug_log(f"[MANUAL MODE] Last text: '{text[:100]}...'", debug=self.debug)

        image_html = generate_webui(text, workflow_name, url)

        # Consume picture_response after generation
        toggle_generation(False)

        from ..utils.helpers import debug_log

        if image_html:
            debug_log("[MANUAL MODE] Image generated successfully", debug=self.debug)
            return f"{text}\n\n{image_html}"
        else:
            debug_log("[MANUAL MODE] Image generation failed", debug=self.debug)
            return text
