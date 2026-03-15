"""Image replacement service for replacing <image> tags with generated images."""

import base64


def replace_image_tags_with_images(text, image_results):
    """Replace <image>...</image> tags with generated images.

    image_results: list of dicts with keys: 'prompt', 'image_data' (or None), 'success', 'start_pos', 'end_pos'
    Returns text with tags replaced by <img> tags or original text if failed.
    """
    if not image_results:
        return text

    # Check if text contains escaped tags - if so, work with unescaped version
    if "&lt;image&gt;" in text:
        import html

        unescaped_text = html.unescape(text)
        working_text = unescaped_text
    else:
        working_text = text

    # Sort results by position
    sorted_results = sorted(image_results, key=lambda x: x["start_pos"])

    # Build replacements with progress updates
    replacements = []
    for result in sorted_results:
        if result["image_data"]:
            base64_img = base64.b64encode(result["image_data"]).decode("utf-8")
            # Generate filename with timestamp
            from ..utils.image_naming import generate_image_filename

            filename = generate_image_filename()
            # Add image with newline for better display
            replacement = f'\n<img src="data:image/png;base64,{base64_img}" alt="{filename}" data-filename="{filename}" data-index="0" class="comfy-generated-image" style="max-width: 100%; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); cursor: pointer; transition: transform 0.2s;" />\n'
        else:
            # Keep original text if generation failed
            replacement = f"<image>{result['prompt']}</image>"
        replacements.append((result["start_pos"], result["end_pos"], replacement))

    # Apply replacements from end to start to preserve positions
    result_text = working_text
    for start_pos, end_pos, replacement in reversed(replacements):
        result_text = result_text[:start_pos] + replacement + result_text[end_pos:]

    return result_text
