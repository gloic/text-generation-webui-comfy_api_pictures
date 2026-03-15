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


