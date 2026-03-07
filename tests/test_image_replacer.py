"""Tests for image replacement functionality."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from script import replace_image_tags_with_images


class TestReplaceImageTagsWithImages:
    """Test cases for replace_image_tags_with_images function."""

    def test_replace_single_tag_success(self, single_tag_text, mock_image_data):
        """Test replacing a single tag with successful image."""
        results = [
            {
                "prompt": "a beautiful sunset over the ocean",
                "image_data": mock_image_data,
                "success": True,
                "start_pos": 18,
                "end_pos": 65,
            }
        ]

        result = replace_image_tags_with_images(single_tag_text, results)

        assert "<img src=" in result
        assert "data:image/png;base64," in result
        assert "<image>" not in result  # Original tag should be removed

    def test_replace_single_tag_failure(self, single_tag_text):
        """Test replacing a single tag with failed generation."""
        results = [
            {
                "prompt": "a beautiful sunset over the ocean",
                "image_data": None,
                "success": False,
                "start_pos": 18,
                "end_pos": 65,
            }
        ]

        result = replace_image_tags_with_images(single_tag_text, results)

        # Original tag should be preserved
        assert "<image>" in result
        assert "a beautiful sunset over the ocean" in result

    def test_replace_multiple_tags_success(self, sample_tags_text, mock_image_data):
        """Test replacing multiple tags with successful images."""
        results = [
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

        result = replace_image_tags_with_images(sample_tags_text, results)

        # Both tags should be replaced
        assert result.count("<img src=") == 2
        assert result.count("<image>") == 0

    def test_replace_mixed_success_failure(self, sample_tags_text, mock_image_data):
        """Test replacing tags with mixed success/failure."""
        results = [
            {
                "prompt": "a cat sitting on a mat",
                "image_data": mock_image_data,
                "success": True,
                "start_pos": 20,
                "end_pos": 49,
            },
            {
                "prompt": "a dog playing nearby",
                "image_data": None,
                "success": False,
                "start_pos": 54,
                "end_pos": 81,
            },
        ]

        result = replace_image_tags_with_images(sample_tags_text, results)

        # First tag replaced, second preserved
        assert result.count("<img src=") == 1
        assert result.count("<image>") == 1
        assert "a dog playing nearby" in result

    def test_replace_no_tags(self, no_tag_text):
        """Test replacing with no tags to replace."""
        results = []

        result = replace_image_tags_with_images(no_tag_text, results)

        # Text should remain unchanged
        assert result == no_tag_text

    def test_replace_empty_results(self, sample_tags_text):
        """Test replacing with empty results list."""
        result = replace_image_tags_with_images(sample_tags_text, [])

        # Text should remain unchanged
        assert result == sample_tags_text

    def test_replace_preserves_surrounding_text(
        self, sample_tags_text, mock_image_data
    ):
        """Test that surrounding text is preserved."""
        results = [
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

        result = replace_image_tags_with_images(sample_tags_text, results)

        # Surrounding text should be preserved
        assert "Here is a scene:" in result
        assert "and" in result
        assert "." in result

    def test_replace_escaped_tags(self, sample_escaped_tags_text, mock_image_data):
        """Test replacing HTML-escaped tags."""
        results = [
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

        result = replace_image_tags_with_images(sample_escaped_tags_text, results)

        # Tags should be replaced (unescaped version)
        assert result.count("<img src=") == 2
        assert "&lt;image&gt;" not in result

    def test_replace_multiline_tag(self, multi_line_tag_text, mock_image_data):
        """Test replacing multi-line tags."""
        results = [
            {
                "prompt": "a cat\nsitting on a mat\nwith a hat",
                "image_data": mock_image_data,
                "success": True,
                "start_pos": 14,
                "end_pos": 65,
            }
        ]

        result = replace_image_tags_with_images(multi_line_tag_text, results)

        assert "<img src=" in result
        assert "<image>" not in result

    def test_replace_adds_newlines(self, single_tag_text, mock_image_data):
        """Test that newlines are added around images."""
        results = [
            {
                "prompt": "a beautiful sunset over the ocean",
                "image_data": mock_image_data,
                "success": True,
                "start_pos": 18,
                "end_pos": 65,
            }
        ]

        result = replace_image_tags_with_images(single_tag_text, results)

        # Check for newline formatting
        assert "\n<img src=" in result or "<img src=\n" in result

    def test_replace_order_preserved(self, sample_tags_text, mock_image_data):
        """Test that replacement order is preserved correctly."""
        results = [
            {
                "prompt": "a cat sitting on a mat",
                "image_data": mock_image_data,
                "success": True,
                "start_pos": 54,  # Out of order
                "end_pos": 81,
            },
            {
                "prompt": "a dog playing nearby",
                "image_data": mock_image_data,
                "success": True,
                "start_pos": 20,  # Out of order
                "end_pos": 49,
            },
        ]

        result = replace_image_tags_with_images(sample_tags_text, results)

        # Should still work correctly despite out-of-order input
        assert result.count("<img src=") == 2

    def test_replace_with_special_chars(self, mock_image_data):
        """Test replacing tags with special characters in prompts."""
        text = "<image>a cat with #hash $dollar @symbol</image>"
        results = [
            {
                "prompt": "a cat with #hash $dollar @symbol",
                "image_data": mock_image_data,
                "success": True,
                "start_pos": 0,
                "end_pos": 52,
            }
        ]

        result = replace_image_tags_with_images(text, results)

        assert "<img src=" in result
        assert "<image>" not in result

    def test_replace_unicode_prompts(self, mock_image_data):
        """Test replacing tags with unicode prompts."""
        text = "<image>un résumé: café, naïve, élève</image>"
        results = [
            {
                "prompt": "un résumé: café, naïve, élève",
                "image_data": mock_image_data,
                "success": True,
                "start_pos": 0,
                "end_pos": 45,
            }
        ]

        result = replace_image_tags_with_images(text, results)

        assert "<img src=" in result
        assert (
            "café" in result or "<image>" not in result
        )  # Either replaced or preserved
