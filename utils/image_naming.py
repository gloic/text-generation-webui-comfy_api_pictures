"""Utility functions for image naming with timestamps."""

import time
from pathlib import Path


def generate_image_filename(conversation_index=None, prompt=None):
    """Generate a unique filename for an image.

    Args:
        conversation_index: Index of image in conversation (optional)
        prompt: Prompt text (optional, used for additional uniqueness)

    Returns:
        Filename string like "comfy_20260307_143050_001.png"
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    if conversation_index is not None:
        # Use index if available
        filename = f"comfy_{timestamp}_{conversation_index:03d}.png"
    else:
        # Fallback to timestamp only
        filename = f"comfy_{timestamp}.png"

    return filename


def get_conversation_image_count(state):
    """Get the number of images already in the conversation.

    Args:
        state: Current chat state object

    Returns:
        Integer count of images
    """
    if not state:
        return 0

    # Count <img> tags in history or messages
    try:
        if hasattr(state, "history") and state.history:
            # Count images in last message
            last_message = state.history[-1] if state.history else ""
            if isinstance(last_message, list) and len(last_message) >= 2:
                text_content = last_message[1] if len(last_message) > 1 else ""
                return text_content.count("<img")

        if hasattr(state, "messages"):
            # Count images in all messages
            total = 0
            for message in state.messages:
                if hasattr(message, "content"):
                    total += message.content.count("<img")
            return total
    except:
        pass

    return 0
