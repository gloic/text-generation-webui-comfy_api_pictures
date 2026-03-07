"""Tests for Mode 3 - Process Tags functionality."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from script import (
    parse_image_tags,
    replace_image_tags_with_images,
    generate_multiple_images_sequential,
    output_modifier,
    params,
)


class TestMode3TagProcessing:
    """Test cases for Mode 3 tag processing."""

    def test_parse_and_replace_single_tag(self, single_tag_text, mock_image_data):
        """Test complete flow: parse tag, generate image, replace."""
        # Parse tags
        tags = parse_image_tags(single_tag_text)
        assert len(tags) == 1

        # Generate mock results
        results = [
            {
                "prompt": tags[0][0],
                "image_data": mock_image_data,
                "success": True,
                "start_pos": tags[0][1],
                "end_pos": tags[0][2],
            }
        ]

        # Replace tags
        result = replace_image_tags_with_images(single_tag_text, results)

        # Verify replacement
        assert "<img src=" in result
        assert "<image>" not in result

    def test_parse_and_replace_multiple_tags(self, sample_tags_text, mock_image_data):
        """Test complete flow with multiple tags."""
        # Parse tags
        tags = parse_image_tags(sample_tags_text)
        assert len(tags) == 2

        # Generate mock results
        results = []
        for tag in tags:
            results.append(
                {
                    "prompt": tag[0],
                    "image_data": mock_image_data,
                    "success": True,
                    "start_pos": tag[1],
                    "end_pos": tag[2],
                }
            )

        # Replace tags
        result = replace_image_tags_with_images(sample_tags_text, results)

        # Verify both tags replaced
        assert result.count("<img src=") == 2
        assert result.count("<image>") == 0


class TestMode3SequentialGeneration:
    """Test cases for sequential image generation."""

    @patch("script.load_workflow")
    @patch("script.ComfyUIClient")
    def test_sequential_generation(
        self, mock_client_class, mock_load_workflow, mock_image_data
    ):
        """Test that images are generated sequentially."""
        mock_load_workflow.return_value = {
            "1": {"inputs": {"prompt": "YOUR PROMPT HERE"}}
        }

        mock_client = Mock()
        mock_client.generate_image = Mock(
            side_effect=[mock_image_data, mock_image_data, mock_image_data]
        )
        mock_client_class.return_value = mock_client

        prompts = ["prompt 1", "prompt 2", "prompt 3"]
        results = generate_multiple_images_sequential(
            prompts, "test.json", "http://127.0.0.1:8188"
        )

        # Verify sequential generation
        assert len(results) == 3
        assert all(r["success"] for r in results)
        assert mock_client.generate_image.call_count == 3

    @patch("script.load_workflow")
    @patch("script.ComfyUIClient")
    def test_workflow_reload_per_generation(
        self, mock_client_class, mock_load_workflow, mock_image_data
    ):
        """Test that workflow is reloaded for each generation."""
        mock_load_workflow.return_value = {
            "1": {"inputs": {"prompt": "YOUR PROMPT HERE"}}
        }

        mock_client = Mock()
        mock_client.generate_image = Mock(return_value=mock_image_data)
        mock_client_class.return_value = mock_client

        prompts = ["prompt 1", "prompt 2"]
        generate_multiple_images_sequential(
            prompts, "test.json", "http://127.0.0.1:8188"
        )

        # Verify workflow was loaded multiple times
        assert mock_load_workflow.call_count >= 2

    @patch("script.load_workflow")
    @patch("script.ComfyUIClient")
    def test_partial_failure(
        self, mock_client_class, mock_load_workflow, mock_image_data
    ):
        """Test handling of partial failures."""
        mock_load_workflow.return_value = {
            "1": {"inputs": {"prompt": "YOUR PROMPT HERE"}}
        }

        mock_client = Mock()
        mock_client.generate_image = Mock(
            side_effect=[
                mock_image_data,  # Success
                None,  # Failure
                mock_image_data,  # Success
            ]
        )
        mock_client_class.return_value = mock_client

        prompts = ["prompt 1", "prompt 2", "prompt 3"]
        results = generate_multiple_images_sequential(
            prompts, "test.json", "http://127.0.0.1:8188"
        )

        # Verify partial success
        assert len(results) == 3
        assert results[0]["success"] == True
        assert results[1]["success"] == False
        assert results[2]["success"] == True


class TestMode3OutputModifier:
    """Test cases for output_modifier with Mode 3."""

    def test_mode3_process_tags(self, single_tag_text, mock_image_data, params):
        """Test output_modifier with Mode 3 processing tags."""
        # Set Mode 3
        params["mode"] = 3
        params["selected_workflow"] = "test.json"
        params["comfyui_url"] = "http://127.0.0.1:8188"

        # Mock generate_multiple_images_sequential
        with patch("script.generate_multiple_images_sequential") as mock_gen:
            mock_gen.return_value = [
                {
                    "prompt": "a beautiful sunset over the ocean",
                    "image_data": mock_image_data,
                    "success": True,
                    "start_pos": 18,
                    "end_pos": 65,
                }
            ]

            state = {"ui_messages": []}
            result = output_modifier(single_tag_text, state)

            # Verify tag was replaced
            assert "<img src=" in result
            assert "<image>" not in result

    def test_mode3_preserve_failed_tag(self, single_tag_text, params):
        """Test that failed generation preserves original tag."""
        # Set Mode 3
        params["mode"] = 3
        params["selected_workflow"] = "test.json"
        params["comfyui_url"] = "http://127.0.0.1:8188"

        # Mock failed generation
        with patch("script.generate_multiple_images_sequential") as mock_gen:
            mock_gen.return_value = [
                {
                    "prompt": "a beautiful sunset over the ocean",
                    "image_data": None,
                    "success": False,
                    "start_pos": 18,
                    "end_pos": 65,
                }
            ]

            state = {"ui_messages": []}
            result = output_modifier(single_tag_text, state)

            # Verify original tag preserved
            assert "<image>" in result
            assert "a beautiful sunset over the ocean" in result

    def test_mode3_no_tags(self, no_tag_text, params):
        """Test Mode 3 with no tags (should pass through)."""
        # Set Mode 3
        params["mode"] = 3

        state = {"ui_messages": []}
        result = output_modifier(no_tag_text, state)

        # Text should pass through unchanged
        assert result == no_tag_text

    def test_mode3_multiple_tags(self, sample_tags_text, mock_image_data, params):
        """Test Mode 3 with multiple tags."""
        # Set Mode 3
        params["mode"] = 3

        # Mock multiple successful generations
        with patch("script.generate_multiple_images_sequential") as mock_gen:
            mock_gen.return_value = [
                {
                    "prompt": "a cat sitting on a mat",
                    "image_data": mock_image_data,
                    "success": True,
                    "start_pos": 20,
                    "end_pos": 49,
                },
                {
                    "prompt": "a dog playing nearby",
                    "image_data": mock_image_data,
                    "success": True,
                    "start_pos": 54,
                    "end_pos": 81,
                },
            ]

            state = {"ui_messages": []}
            result = output_modifier(sample_tags_text, state)

            # Verify both tags replaced
            assert result.count("<img src=") == 2
            assert result.count("<image>") == 0

    def test_mode_not_3(self, single_tag_text, params):
        """Test that other modes don't process tags."""
        # Set Mode 0 (Manual)
        params["mode"] = 0

        state = {"ui_messages": []}
        result = output_modifier(single_tag_text, state)

        # Tag should not be processed in Mode 0
        assert result == single_tag_text


class TestMode3EdgeCases:
    """Test edge cases for Mode 3."""

    def test_empty_tag(self, empty_tag_text, mock_image_data, params):
        """Test handling of empty tags."""
        params["mode"] = 3

        with patch("script.generate_multiple_images_sequential") as mock_gen:
            mock_gen.return_value = [
                {
                    "prompt": "",
                    "image_data": mock_image_data,
                    "success": True,
                    "start_pos": 0,
                    "end_pos": 18,
                }
            ]

            state = {"ui_messages": []}
            result = output_modifier(empty_tag_text, state)

            # Should still process (even if prompt is empty)
            assert "<img src=" in result

    def test_escaped_tags(self, sample_escaped_tags_text, mock_image_data, params):
        """Test handling of HTML-escaped tags."""
        params["mode"] = 3

        with patch("script.parse_image_tags") as mock_parse:
            mock_parse.return_value = [
                ("a cat sitting on a mat", 20, 49),
                ("a dog playing nearby", 54, 81),
            ]

            with patch("script.generate_multiple_images_sequential") as mock_gen:
                mock_gen.return_value = [
                    {
                        "prompt": "a cat sitting on a mat",
                        "image_data": mock_image_data,
                        "success": True,
                        "start_pos": 20,
                        "end_pos": 49,
                    },
                    {
                        "prompt": "a dog playing nearby",
                        "image_data": mock_image_data,
                        "success": True,
                        "start_pos": 54,
                        "end_pos": 81,
                    },
                ]

                state = {"ui_messages": []}
                result = output_modifier(sample_escaped_tags_text, state)

                # Should process escaped tags correctly
                assert result.count("<img src=") == 2

    def test_multiline_tag(self, multi_line_tag_text, mock_image_data, params):
        """Test handling of multi-line tags."""
        params["mode"] = 3

        with patch("script.generate_multiple_images_sequential") as mock_gen:
            mock_gen.return_value = [
                {
                    "prompt": "a cat\nsitting on a mat\nwith a hat",
                    "image_data": mock_image_data,
                    "success": True,
                    "start_pos": 14,
                    "end_pos": 65,
                }
            ]

            state = {"ui_messages": []}
            result = output_modifier(multi_line_tag_text, state)

            # Should replace successfully
            assert "<img src=" in result
