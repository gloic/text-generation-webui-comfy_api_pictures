"""Immersive mode - watches for trigger words in input."""

import re
from .base import Mode
from ..utils.helpers import generate_webui
from ..global_state import toggle_generation


class ImmersiveMode(Mode):
    """Mode 1: Immersive/Interactive - trigger words activate generation."""

    def __init__(self, params, picture_response=None):
        self.params = params

    def process_input(self, text):
        """Check for trigger words and modify input.

        Args:
            text: Input text

        Returns:
            Modified text if trigger detected
        """
        if not self._triggers_are_in(text):
            return text

        from ..global_state import toggle_generation

        toggle_generation(True)
        print("[IMMERSIVE MODE] Trigger detected, picture_response set to True")

        # Trigger detected - modify text
        text = text.lower()
        if "of" in text:
            subject = text.split("of", 1)[1]
            text = (
                "Please provide a detailed and vivid description of [subject]".replace(
                    "[subject]", subject
                )
            )
        else:
            text = "Please provide a detailed and vivid description of [subject]".replace(
                "[subject]",
                "your appearance, your surroundings and what you are doing right now",
            )

        return text

    def process_output(self, text, state):
        """Process output - generates image if picture_response is True.

        Args:
            text: LLM output text
            state: Current state object

        Returns:
            Modified text with image if triggered
        """
        from ..global_state import picture_response

        if not picture_response:
            print(
                "[IMMERSIVE MODE] picture_response is False, returning text unchanged"
            )
            return text

        # Immersive mode: generate image when picture_response is True
        # and trigger was detected in input (already handled by process_input)

        workflow_name = self.params["selected_workflow"]
        url = self.params["comfyui_url"]

        print(f"[IMMERSIVE MODE] Generating image...")
        print(f"[IMMERSIVE MODE] Using workflow: '{workflow_name}'")
        print(f"[IMMERSIVE MODE] Using URL: {url}")
        print(f"[IMMERSIVE MODE] Last text: '{text[:100]}...'")

        image_html = generate_webui(text, workflow_name, url)

        # Consume picture_response after generation
        toggle_generation(False)

        if image_html:
            print("[IMMERSIVE MODE] Image generated successfully")
            return f"{text}\n\n{image_html}"
        else:
            print("[IMMERSIVE MODE] Image generation failed")
            return text

    def _triggers_are_in(self, string):
        """Check if trigger words are present.

        Args:
            string: Input text

        Returns:
            True if triggers found
        """
        string = self._remove_surrounded_chars(string)
        return bool(
            re.search(
                "(?aims)(send|mail|message|me|fais)\\b.+ ?\\b(image|pic(ture)?|photo|snap(shot)?|selfie|meme)s?\\b",
                string,
            )
        )

    def _remove_surrounded_chars(self, string):
        """Remove characters surrounded by asterisks."""
        return re.sub("\*[^\*]*?(\*|$)", "", string)
