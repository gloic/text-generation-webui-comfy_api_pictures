"""Tag parsing service for processing <image>...</image> tags."""

import re
import html


def parse_image_tags(text):
    """Parse <image>...</image> tags from text.

    If tags are HTML-escaped (&lt;image&gt;), unescape them first to get correct positions.

    Args:
        text: Input text potentially containing image tags

    Returns:
        list of tuples: [(prompt1, start_pos1, end_pos1), (prompt2, start_pos2, end_pos2), ...]
    """
    # Check if text contains escaped tags
    if "&lt;image&gt;" in text:
        # Unescape the entire text to get correct positions
        unescaped_text = html.unescape(text)
        pattern = r"<image>(.*?)</image>"
        matches = list(re.finditer(pattern, unescaped_text, re.DOTALL))
        from ..utils.helpers import debug_log

        debug_log(f"[MODE 3] Found {len(matches)} tags in unescaped text", debug=False)
    else:
        pattern = r"<image>(.*?)</image>"
        matches = list(re.finditer(pattern, text, re.DOTALL))
        from ..utils.helpers import debug_log

        debug_log(f"[MODE 3] Found {len(matches)} tags in text", debug=False)

    results = []
    for match in matches:
        prompt = match.group(1).strip()
        start_pos = match.start()
        end_pos = match.end()
        results.append((prompt, start_pos, end_pos))

    return results
