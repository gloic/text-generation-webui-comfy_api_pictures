"""Tests for ComfyUI client functionality."""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from script import ComfyUIClient


class TestComfyUIClient:
    """Test cases for ComfyUIClient class."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = ComfyUIClient("http://127.0.0.1:8188")

        assert client.server_address == "http://127.0.0.1:8188"
        assert client.client_id is not None
        assert len(client.client_id) > 0

    def test_client_different_urls(self):
        """Test client with different URLs."""
        client1 = ComfyUIClient("http://localhost:8188")
        client2 = ComfyUIClient("http://192.168.1.100:8188")

        assert client1.server_address == "http://localhost:8188"
        assert client2.server_address == "http://192.168.1.100:8188"
        assert client1.client_id != client2.client_id  # Different IDs

    @patch("script.urllib.request.urlopen")
    def test_queue_prompt(self, mock_urlopen):
        """Test queue_prompt method."""
        client = ComfyUIClient("http://127.0.0.1:8188")

        mock_response = Mock()
        mock_response.read.return_value = b'{"prompt_id": "12345"}'
        mock_urlopen.return_value = mock_response

        workflow = {"1": {"inputs": {"prompt": "test"}}}
        result = client.queue_prompt(workflow, "test_client_id")

        assert result["prompt_id"] == "12345"
        mock_urlopen.assert_called_once()

    @patch("script.urllib.request.urlopen")
    def test_get_image(self, mock_urlopen):
        """Test get_image method."""
        client = ComfyUIClient("http://127.0.0.1:8188")

        mock_response = Mock()
        mock_response.read.return_value = b"fake_image_data"
        mock_urlopen.return_value = mock_response

        image_data = client.get_image("test.png", "output", "output")

        assert image_data == b"fake_image_data"
        mock_urlopen.assert_called_once()

    @patch("script.websocket.WebSocket")
    def test_connect(self, mock_websocket):
        """Test connect method."""
        client = ComfyUIClient("http://127.0.0.1:8188")

        mock_ws = Mock()
        mock_websocket.return_value = mock_ws

        client.connect()

        mock_ws.connect.assert_called_once()
        assert client.ws is not None

    @patch("script.websocket.WebSocket")
    @patch("script.urllib.request.urlopen")
    def test_generate_image_success(self, mock_urlopen, mock_websocket):
        """Test successful image generation."""
        client = ComfyUIClient("http://127.0.0.1:8188")

        # Mock websocket
        mock_ws = Mock()
        mock_ws.connected = True
        mock_ws.recv = Mock(
            side_effect=[
                '{"type": "executing", "data": {"node": null, "prompt_id": "12345"}}',
            ]
        )
        client.ws = mock_ws

        # Mock prompt queue
        mock_prompt_response = Mock()
        mock_prompt_response.read.return_value = b'{"prompt_id": "12345"}'

        # Mock history
        mock_history_response = Mock()
        mock_history_response.read.return_value = json.dumps(
            {
                "12345": {
                    "outputs": {
                        "1": {
                            "images": [
                                {
                                    "filename": "test.png",
                                    "subfolder": "output",
                                    "type": "output",
                                }
                            ]
                        }
                    }
                }
            }
        ).encode()

        mock_urlopen.side_effect = [mock_prompt_response, mock_history_response]

        # Mock get_image
        client.get_image = Mock(return_value=b"fake_image_data")

        workflow = {
            "1": {
                "inputs": {"prompt": "YOUR PROMPT HERE", "clip": ["2", 0]},
                "class_type": "CLIPTextEncode",
            }
        }

        result = client.generate_image(workflow, "test prompt")

        assert result == b"fake_image_data"

    @patch("script.urllib.request.urlopen")
    def test_generate_image_no_prompt_placeholder(self, mock_urlopen):
        """Test generation fails without prompt placeholder."""
        client = ComfyUIClient("http://127.0.0.1:8188")

        workflow = {
            "1": {
                "inputs": {
                    "prompt": "actual prompt",  # No placeholder
                    "clip": ["2", 0],
                },
                "class_type": "CLIPTextEncode",
            }
        }

        result = client.generate_image(workflow, "test prompt")

        assert result is None

    @patch("script.urllib.request.urlopen")
    def test_generate_image_exception(self, mock_urlopen):
        """Test generation handles exceptions gracefully."""
        client = ComfyUIClient("http://127.0.0.1:8188")

        mock_urlopen.side_effect = Exception("Connection error")

        workflow = {
            "1": {
                "inputs": {"prompt": "YOUR PROMPT HERE", "clip": ["2", 0]},
                "class_type": "CLIPTextEncode",
            }
        }

        result = client.generate_image(workflow, "test prompt")

        assert result is None


class TestWorkflowPromptInjection:
    """Test cases for prompt injection in workflow."""

    @patch("script.urllib.request.urlopen")
    def test_prompt_injection(self, mock_urlopen):
        """Test that prompt is correctly injected into workflow."""
        client = ComfyUIClient("http://127.0.0.1:8188")

        # Track what workflow is sent
        sent_workflows = []

        def capture_queue(prompt, client_id):
            sent_workflows.append(prompt)
            return {"prompt_id": "12345"}

        client.queue_prompt = Mock(side_effect=capture_queue)

        workflow = {
            "1": {
                "inputs": {"prompt": "YOUR PROMPT HERE", "clip": ["2", 0]},
                "class_type": "CLIPTextEncode",
            }
        }

        test_prompt = "A beautiful sunset"
        client.generate_image(workflow, test_prompt)

        # Verify prompt was injected
        assert len(sent_workflows) > 0
        injected_workflow = sent_workflows[0]
        assert injected_workflow["1"]["inputs"]["prompt"] == test_prompt

    @patch("script.urllib.request.urlopen")
    def test_seed_randomization(self, mock_urlopen):
        """Test that seed is randomized for each generation."""
        client = ComfyUIClient("http://127.0.0.1:8188")

        # Track what workflow is sent
        sent_workflows = []

        def capture_queue(prompt, client_id):
            sent_workflows.append(prompt)
            return {"prompt_id": "12345"}

        client.queue_prompt = Mock(side_effect=capture_queue)

        workflow = {
            "1": {
                "inputs": {"prompt": "YOUR PROMPT HERE", "clip": ["2", 0]},
                "class_type": "CLIPTextEncode",
            },
            "2": {"inputs": {"seed": 12345, "steps": 20}, "class_type": "KSampler"},
        }

        # Generate twice
        client.generate_image(workflow, "Prompt 1")
        client.generate_image(workflow, "Prompt 2")

        # Seeds should be different (randomized)
        seed1 = sent_workflows[0]["2"]["inputs"]["seed"]
        seed2 = sent_workflows[1]["2"]["inputs"]["seed"]

        assert seed1 != seed2
