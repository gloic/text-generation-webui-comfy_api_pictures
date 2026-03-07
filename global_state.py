"""Global state management for picture generation."""

picture_response = False
debug_enabled = False


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


def toggle_debug(*args):
    """Toggle debug mode on/off.

    Args:
        *args: Optional boolean argument to set specific value
    """
    global debug_enabled

    if not args:
        debug_enabled = not debug_enabled
    else:
        debug_enabled = args[0]
