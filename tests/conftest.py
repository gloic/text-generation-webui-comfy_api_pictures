"""Pytest fixtures for comfy_api_pictures tests."""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_workflow():
    """Sample workflow JSON with YOUR PROMPT HERE placeholder."""
    return {
        "1": {
            "inputs": {"prompt": "YOUR PROMPT HERE", "clip": ["2", 0]},
            "class_type": "CLIPTextEncode",
        },
        "2": {
            "inputs": {
                "seed": 123456,
                "steps": 20,
                "cfg": 8.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["3", 0],
                "positive": ["1", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
            },
            "class_type": "KSampler",
        },
        "3": {
            "inputs": {"ckpt_name": "model.safetensors"},
            "class_type": "CheckpointLoaderSimple",
        },
        "4": {
            "inputs": {"text": "negative prompt", "clip": ["2", 0]},
            "class_type": "CLIPTextEncode",
        },
        "5": {
            "inputs": {"width": 512, "height": 512, "batch_size": 1},
            "class_type": "EmptyLatentImage",
        },
    }


@pytest.fixture
def sample_workflow_json(sample_workflow):
    """Sample workflow as JSON string."""
    return json.dumps(sample_workflow)


@pytest.fixture
def mock_comfy_client():
    """Mock ComfyUIClient for testing."""
    client = Mock()
    client.generate_image = Mock(return_value=b"fake_image_data")
    return client


@pytest.fixture
def sample_tags_text():
    """Text with multiple image tags."""
    return "Here is a scene: <image>a cat sitting on a mat</image> and <image>a dog playing nearby</image>."


@pytest.fixture
def sample_escaped_tags_text():
    """Text with HTML-escaped image tags."""
    return "Here is a scene: &lt;image&gt;a cat sitting on a mat&lt;/image&gt; and &lt;image&gt;a dog playing nearby&lt;/image&gt;."


@pytest.fixture
def single_tag_text():
    """Text with single image tag."""
    return "The image shows: <image>a beautiful sunset over the ocean</image>."


@pytest.fixture
def no_tag_text():
    """Text without image tags."""
    return "This is just regular text with no tags."


@pytest.fixture
def empty_tag_text():
    """Text with empty image tag."""
    return "Empty tag: <image></image>."


@pytest.fixture
def multi_line_tag_text():
    """Text with multi-line image tag."""
    return """Description:
<image>a cat
sitting on a mat
with a hat</image>
End of description."""


@pytest.fixture
def mock_image_data():
    """Mock image data for testing."""
    return b"PNG_fake_image_data_12345"


@pytest.fixture
def mock_history_output():
    """Mock ComfyUI history response."""
    return {
        "12345": {
            "outputs": {
                "2": {
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


@pytest.fixture
def mock_ws_connection():
    """Mock websocket connection."""
    ws = Mock()
    ws.connected = True
    ws.recv = Mock(
        side_effect=[
            '{"type": "executing", "data": {"node": null, "prompt_id": "12345"}}',
            '{"type": "executing", "data": {"node": "2", "prompt_id": "12345"}}',
            '{"type": "executing", "data": {"node": null, "prompt_id": "12345"}}',
        ]
    )
    return ws


@pytest.fixture
def params():
    """Default params dictionary."""
    return {
        "comfyui_url": "http://127.0.0.1:8188",
        "selected_workflow": "test_workflow.json",
        "mode": 0,
        "prompt_prefix": "",
    }
