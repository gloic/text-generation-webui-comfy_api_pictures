"""Tests for tag parsing functionality."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from script import parse_image_tags


class TestParseImageTags:
    """Test cases for parse_image_tags function."""

    def test_single_tag(self, single_tag_text):
        """Test parsing a single image tag."""
        tags = parse_image_tags(single_tag_text)

        assert len(tags) == 1
        assert tags[0][0] == "a beautiful sunset over the ocean"
        assert tags[0][1] >= 0  # start_pos
        assert tags[0][2] > tags[0][1]  # end_pos > start_pos

    def test_multiple_tags(self, sample_tags_text):
        """Test parsing multiple image tags."""
        tags = parse_image_tags(sample_tags_text)

        assert len(tags) == 2
        assert tags[0][0] == "a cat sitting on a mat"
        assert tags[1][0] == "a dog playing nearby"

    def test_escaped_tags(self, sample_escaped_tags_text):
        """Test parsing HTML-escaped image tags."""
        tags = parse_image_tags(sample_escaped_tags_text)

        assert len(tags) == 2
        assert tags[0][0] == "a cat sitting on a mat"
        assert tags[1][0] == "a dog playing nearby"

    def test_no_tags(self, no_tag_text):
        """Test parsing text with no image tags."""
        tags = parse_image_tags(no_tag_text)

        assert len(tags) == 0

    def test_empty_tag(self, empty_tag_text):
        """Test parsing empty image tag."""
        tags = parse_image_tags(empty_tag_text)

        assert len(tags) == 1
        assert tags[0][0] == ""  # Empty prompt

    def test_multiline_tag(self, multi_line_tag_text):
        """Test parsing multi-line image tag."""
        tags = parse_image_tags(multi_line_tag_text)

        assert len(tags) == 1
        # Should capture the entire multi-line content
        assert "a cat" in tags[0][0]
        assert "sitting on a mat" in tags[0][0]
        assert "with a hat" in tags[0][0]

    def test_tag_with_whitespace(self):
        """Test parsing tags with extra whitespace."""
        text = "<image>   a prompt with spaces   </image>"
        tags = parse_image_tags(text)

        assert len(tags) == 1
        assert tags[0][0] == "a prompt with spaces"  # Should be stripped

    def test_tag_positions_correct(self, sample_tags_text):
        """Test that tag positions are correct for replacement."""
        tags = parse_image_tags(sample_tags_text)

        # Verify positions don't overlap
        for i in range(len(tags) - 1):
            assert tags[i][2] <= tags[i + 1][1], "Tags should not overlap"

        # Verify positions are within text bounds
        for tag in tags:
            assert 0 <= tag[1] < len(sample_tags_text)
            assert 0 < tag[2] <= len(sample_tags_text)

    def test_escaped_tag_positions(self, sample_escaped_tags_text):
        """Test that escaped tag positions work correctly."""
        tags = parse_image_tags(sample_escaped_tags_text)

        assert len(tags) == 2
        # Positions should be valid
        for tag in tags:
            assert tag[1] >= 0
            assert tag[2] > tag[1]

    def test_special_characters_in_tag(self):
        """Test tags with special characters."""
        text = "<image>a cat with #hash, $dollar, @symbol</image>"
        tags = parse_image_tags(text)

        assert len(tags) == 1
        assert "#hash" in tags[0][0]
        assert "$dollar" in tags[0][0]
        assert "@symbol" in tags[0][0]

    def test_unicode_in_tag(self):
        """Test tags with unicode characters."""
        text = "<image>un résumé en français: café, naïve, élève</image>"
        tags = parse_image_tags(text)

        assert len(tags) == 1
        assert "café" in tags[0][0]
        assert "naïve" in tags[0][0]

    def test_nested_like_tags(self):
        """Test text that looks like nested tags (should not happen but test safety)."""
        text = "<image>text with &lt; not a tag &gt; more text</image>"
        tags = parse_image_tags(text)

        assert len(tags) == 1
        assert "&lt; not a tag &gt;" in tags[0][0]

    def test_mixed_escaped_and_normal(self):
        """Test text with both escaped and normal tags."""
        text = "<image>normal tag</image> and &lt;image&gt;escaped tag&lt;/image&gt;"
        tags = parse_image_tags(text)

        assert len(tags) == 2

    def test_tag_at_end(self):
        """Test tag at end of text."""
        text = "This is the end <image>final prompt</image>"
        tags = parse_image_tags(text)

        assert len(tags) == 1
        assert tags[0][0] == "final prompt"

    def test_tag_at_start(self):
        """Test tag at start of text."""
        text = "<image>first prompt</image> and more text"
        tags = parse_image_tags(text)

        assert len(tags) == 1
        assert tags[0][0] == "first prompt"
        assert tags[0][1] == 0  # Start at position 0
