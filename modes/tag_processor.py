"""Tag processor mode for automatic <image> tag generation."""

import time
from .base import Mode
from ..services.tag_parser import parse_image_tags
from ..services.image_replacer import replace_image_tags_with_images
from ..core.client import ComfyUIClient
from ..core.workflow import load_workflow


class TagProcessorMode(Mode):
    """Mode 3: Process Tags - automatically parse and generate <image> tags."""

    def __init__(self, params, picture_response=None, debug=False):
        super().__init__(params, picture_response, debug)

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
        from ..utils.helpers import debug_log

        debug_log(
            f"[MODE 3] Processing image tags. Workflow: '{self.params['selected_workflow']}', URL: {self.params['comfyui_url']}",
            debug=self.debug,
        )
        debug_log(f"[MODE 3] Raw string preview: {text[:200]}", debug=self.debug)
        debug_log(
            f"[MODE 3] String contains '<image>': {'<image>' in text}", debug=self.debug
        )
        debug_log(
            f"[MODE 3] String contains '&lt;image&gt;': {'&lt;image&gt;' in text}",
            debug=self.debug,
        )

        tags = parse_image_tags(text)
        debug_log(f"[MODE 3] Found {len(tags)} tags in response", debug=self.debug)

        if tags:
            prompts = [tag[0] for tag in tags]
            debug_log(
                f"[MODE 3] Will generate {len(prompts)} image(s)", debug=self.debug
            )

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
            from ..utils.helpers import debug_log

            debug_log(
                f"[MODE 3] Completed processing {len(results)} images", debug=self.debug
            )

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
        from ..utils.helpers import debug_log

        debug_log(f"[MODE 3] Loading workflow: {workflow_name}", debug=self.debug)
        results = []
        client = ComfyUIClient(url)
        workflow = load_workflow(workflow_name)

        if not workflow:
            debug_log(
                f"[MODE 3] ERROR: Workflow '{workflow_name}' not found!",
                debug=self.debug,
            )
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

        debug_log(
            f"[MODE 3] Workflow loaded successfully with {len(workflow)} nodes",
            debug=self.debug,
        )

        # Verify workflow has prompt placeholder
        has_prompt_placeholder = False
        for key, node in workflow.items():
            if "inputs" in node:
                for input_key, input_val in node["inputs"].items():
                    if isinstance(input_val, str) and "YOUR PROMPT HERE" in input_val:
                        has_prompt_placeholder = True
                        debug_log(
                            f"[MODE 3] Found prompt placeholder in node {key}",
                            debug=self.debug,
                        )
                        break
            if has_prompt_placeholder:
                break

        if not has_prompt_placeholder:
            debug_log(
                f"[MODE 3] WARNING: No 'YOUR PROMPT HERE' placeholder found in workflow!",
                debug=self.debug,
            )

        for idx, prompt in enumerate(prompts):
            debug_log(
                f"[MODE 3] Generating image {idx + 1}/{len(prompts)}: '{prompt[:80]}...'",
                debug=self.debug,
            )

            # Reload workflow for each generation to avoid modifying the same object
            workflow = load_workflow(workflow_name)
            if not workflow:
                debug_log(
                    f"[MODE 3] ERROR: Could not reload workflow '{workflow_name}'",
                    debug=self.debug,
                )
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
                debug_log(
                    f"[MODE 3] Image {idx + 1} generated successfully ({len(img_data)} bytes)",
                    debug=self.debug,
                )
                # Add small delay for better UX
                time.sleep(0.3)
            else:
                debug_log(
                    f"[MODE 3] Image {idx + 1} generation FAILED", debug=self.debug
                )

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
