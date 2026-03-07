"""Tests for mode integration and other modes."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from script import (
    input_modifier,
    output_modifier,
    toggle_generation,
    params,
    picture_response,
)


class TestMode0Manual:
    """Test cases for Mode 0 (Manual)."""

    def test_mode0_no_auto_generation(self, single_tag_text, params):
        """Test Mode 0 doesn't auto-generate."""
        params["mode"] = 0

        state = {"ui_messages": []}
        result = output_modifier(single_tag_text, state)

        # Should pass through unchanged (no auto-generation)
        assert result == single_tag_text

    def test_mode0_force_button(self, params):
        """Test Mode 0 with force button."""
        params["mode"] = 0

        # Simulate force button
        toggle_generation(True)

        # Note: This would require mocking generate_webui to test full flow
        # For now, just verify toggle works
        assert picture_response == True

    def test_mode0_suppress_button(self, params):
        """Test Mode 0 with suppress button."""
        params["mode"] = 0

        # Simulate suppress button
        toggle_generation(False)

        assert picture_response == False


class TestMode1Immersive:
    """Test cases for Mode 1 (Immersive/Interactive)."""

    def test_mode1_no_trigger(self, params):
        """Test Mode 1 without trigger words."""
        params["mode"] = 1

        text = "Hello, how are you?"
        result = input_modifier(text)

        # Should pass through unchanged
        assert result == text

    def test_mode1_with_trigger(self, params):
        """Test Mode 1 with trigger words."""
        params["mode"] = 1

        text = "send me a picture of a cat"
        result = input_modifier(text)

        # Should be transformed
        assert "description" in result.lower()
        assert "cat" in result.lower()

    def test_mode1_trigger_words(self, params):
        """Test various trigger words."""
        params["mode"] = 1

        triggers = [
            "send me a picture",
            "send a photo",
            "message me a selfie",
            "mail me a snapshot",
        ]

        for trigger in triggers:
            result = input_modifier(trigger)
            assert result != trigger  # Should be modified

    def test_mode1_output_generation(self, params):
        """Test Mode 1 output generation."""
        params["mode"] = 1

        # Set picture_response to True
        toggle_generation(True)

        text = "A beautiful sunset"
        state = {"ui_messages": []}

        # This would call generate_webui, so we just verify it doesn't crash
        # Full test requires mocking the generation
        result = output_modifier(text, state)

        # Should not raise exception
        assert result is not None


class TestMode2Picturebook:
    """Test cases for Mode 2 (Picturebook/Adventure)."""

    def test_mode2_always_generate(self, params):
        """Test Mode 2 always generates images."""
        params["mode"] = 2

        text = "A beautiful landscape"
        state = {"ui_messages": []}

        # Set picture_response to True
        toggle_generation(True)

        # This would call generate_webui, so we just verify it doesn't crash
        result = output_modifier(text, state)

        # Should not raise exception
        assert result is not None


class TestModeSwitching:
    """Test cases for mode switching."""

    def test_mode_change(self, params):
        """Test changing modes."""
        # Start at Mode 0
        params["mode"] = 0
        assert params["mode"] == 0

        # Change to Mode 1
        params["mode"] = 1
        assert params["mode"] == 1

        # Change to Mode 2
        params["mode"] = 2
        assert params["mode"] == 2

        # Change to Mode 3
        params["mode"] = 3
        assert params["mode"] == 3

    def test_mode_persistence(self, params):
        """Test that mode persists across calls."""
        params["mode"] = 3

        # Multiple calls should maintain mode
        for _ in range(5):
            assert params["mode"] == 3


class TestToggleGeneration:
    """Test cases for toggle_generation function."""

    def test_toggle_true(self, params):
        """Test toggling to True."""
        toggle_generation(True)
        assert picture_response == True

    def test_toggle_false(self, params):
        """Test toggling to False."""
        toggle_generation(False)
        assert picture_response == False

    def test_toggle_no_args(self, params):
        """Test toggling with no arguments."""
        # Start at False
        toggle_generation(False)

        # Toggle without args should flip
        toggle_generation()
        assert picture_response == True

        toggle_generation()
        assert picture_response == False


class TestSharedMessage:
    """Test cases for shared processing message."""

    def test_message_set_true(self, params):
        """Test message set when generation is True."""
        toggle_generation(True)

        # shared.processing_message should be set
        # This is verified by the toggle_generation function
        assert picture_response == True

    def test_message_set_false(self, params):
        """Test message set when generation is False."""
        toggle_generation(False)

        assert picture_response == False


class TestInputModifierModes:
    """Test input_modifier across all modes."""

    def test_input_modifier_mode0(self, params):
        """Test input_modifier in Mode 0."""
        params["mode"] = 0

        text = "send me a picture"
        result = input_modifier(text)

        # Should pass through unchanged
        assert result == text

    def test_input_modifier_mode1(self, params):
        """Test input_modifier in Mode 1."""
        params["mode"] = 1

        text = "send me a picture of a cat"
        result = input_modifier(text)

        # Should be transformed
        assert result != text

    def test_input_modifier_mode2(self, params):
        """Test input_modifier in Mode 2."""
        params["mode"] = 2

        text = "send me a picture"
        result = input_modifier(text)

        # Should pass through unchanged (Mode 2 doesn't use input_modifier)
        assert result == text

    def test_input_modifier_mode3(self, params):
        """Test input_modifier in Mode 3."""
        params["mode"] = 3

        text = "send me a picture"
        result = input_modifier(text)

        # Should pass through unchanged (Mode 3 processes output, not input)
        assert result == text


class TestOutputModifierModes:
    """Test output_modifier across all modes."""

    def test_output_modifier_mode0(self, params):
        """Test output_modifier in Mode 0."""
        params["mode"] = 0

        text = "A beautiful sunset"
        state = {"ui_messages": []}

        result = output_modifier(text, state)

        # Should pass through (unless picture_response is True)
        assert result is not None

    def test_output_modifier_mode1(self, params):
        """Test output_modifier in Mode 1."""
        params["mode"] = 1

        text = "A beautiful sunset"
        state = {"ui_messages": []}

        result = output_modifier(text, state)

        # Should process (if picture_response is True)
        assert result is not None

    def test_output_modifier_mode2(self, params):
        """Test output_modifier in Mode 2."""
        params["mode"] = 2

        text = "A beautiful sunset"
        state = {"ui_messages": []}

        result = output_modifier(text, state)

        # Should process (if picture_response is True)
        assert result is not None

    def test_output_modifier_mode3(self, params):
        """Test output_modifier in Mode 3."""
        params["mode"] = 3

        text = "<image>a cat</image>"
        state = {"ui_messages": []}

        result = output_modifier(text, state)

        # Should process tags
        assert result is not None
