"""Global state management for picture generation."""

picture_response = False


def toggle_generation(*args):
    """Toggle picture generation on/off.

    Args:
        *args: Optional boolean argument to set specific value
    """
    global picture_response

    if not args:
        picture_response = not picture_response
    else:
        picture_response = args[0]
