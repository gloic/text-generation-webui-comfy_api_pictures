"""Tag processor mode for automatic <image> tag generation."""

import time
from .base import Mode
from ..services.tag_parser import parse_image_tags
from ..services.image_replacer import replace_image_tags_with_images
from ..core.client import ComfyUIClient
from ..core.workflow import load_workflow


class TagProcessorMode(Mode):
    """Mode 3: Process Tags - automatically parse and generate <image> tags."""

    def __init__(self, params, picture_response=None):
        self.params = params

    def process_input(self, text):
        """Mode 3 doesn't modify input.

        Args:
            text: Input text

        Returns:
            Unmodified text
        """
        return text

    def process_output(self, text, state):
        """Process output and generate images for <image> tags.

        Args:
            text: LLM output text
            state: Current state object

        Returns:
            Text with tags replaced by images
        """
        print(
            f"[MODE 3] Processing image tags. Workflow: '{self.params['selected_workflow']}', URL: {self.params['comfyui_url']}"
        )
        print(f"[MODE 3] Raw string preview: {text[:200]}")
        print(f"[MODE 3] String contains '<image>': {'<image>' in text}")
        print(f"[MODE 3] String contains '&lt;image&gt;': {'&lt;image&gt;' in text}")

        tags = parse_image_tags(text)
        print(f"[MODE 3] Found {len(tags)} tags in response")

        if tags:
            prompts = [tag[0] for tag in tags]
            print(f"[MODE 3] Will generate {len(prompts)} image(s)")

            # Generate images sequentially
            results = self._generate_multiple_images_sequential(
                prompts, self.params["selected_workflow"], self.params["comfyui_url"]
            )

            # Update positions in results
            for i, (prompt, start_pos, end_pos) in enumerate(tags):
                results[i]["start_pos"] = start_pos
                results[i]["end_pos"] = end_pos

            # Replace tags with images
            text = replace_image_tags_with_images(text, results)
            print(f"[MODE 3] Completed processing {len(results)} images")

        return text

    def _generate_multiple_images_sequential(self, prompts, workflow_name, url):
        """Generate multiple images sequentially.

        Args:
            prompts: List of prompt strings
            workflow_name: Workflow JSON filename
            url: ComfyUI server URL

        Returns:
            List of result dicts with prompt, image_data, success, start_pos, end_pos
        """
        print(f"[MODE 3] Loading workflow: {workflow_name}")
        results = []
        client = ComfyUIClient(url)
        workflow = load_workflow(workflow_name)

        if not workflow:
            print(f"[MODE 3] ERROR: Workflow '{workflow_name}' not found!")
            for i, prompt in enumerate(prompts):
                results.append(
                    {
                        "prompt": prompt,
                        "image_data": None,
                        "success": False,
                        "start_pos": 0,
                        "end_pos": 0,
                    }
                )
            return results

        print(f"[MODE 3] Workflow loaded successfully with {len(workflow)} nodes")

        # Verify workflow has prompt placeholder
        has_prompt_placeholder = False
        for key, node in workflow.items():
            if "inputs" in node:
                for input_key, input_val in node["inputs"].items():
                    if isinstance(input_val, str) and "YOUR PROMPT HERE" in input_val:
                        has_prompt_placeholder = True
                        print(f"[MODE 3] Found prompt placeholder in node {key}")
                        break
            if has_prompt_placeholder:
                break

        if not has_prompt_placeholder:
            print(
                f"[MODE 3] WARNING: No 'YOUR PROMPT HERE' placeholder found in workflow!"
            )

        for idx, prompt in enumerate(prompts):
            print(
                f"[MODE 3] Generating image {idx + 1}/{len(prompts)}: '{prompt[:80]}...'"
            )

            # Reload workflow for each generation to avoid modifying the same object
            workflow = load_workflow(workflow_name)
            if not workflow:
                print(f"[MODE 3] ERROR: Could not reload workflow '{workflow_name}'")
                results.append(
                    {
                        "prompt": prompt,
                        "image_data": None,
                        "success": False,
                        "start_pos": 0,
                        "end_pos": 0,
                    }
                )
                continue

            img_data = client.generate_image(workflow, prompt)

            if img_data:
                print(
                    f"[MODE 3] Image {idx + 1} generated successfully ({len(img_data)} bytes)"
                )
                # Add small delay for better UX
                time.sleep(0.3)
            else:
                print(f"[MODE 3] Image {idx + 1} generation FAILED")

            results.append(
                {
                    "prompt": prompt,
                    "image_data": img_data,
                    "success": img_data is not None,
                    "start_pos": 0,  # Will be updated by caller
                    "end_pos": 0,  # Will be updated by caller
                }
            )

        return results
