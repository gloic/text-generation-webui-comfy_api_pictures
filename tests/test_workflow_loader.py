"""Tests for workflow loading functionality."""

import pytest
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from script import get_workflows, load_workflow


class TestGetWorkflows:
    """Test cases for get_workflows function."""

    def test_get_workflows_returns_list(self):
        """Test that get_workflows returns a list."""
        workflows = get_workflows()

        assert isinstance(workflows, list)

    def test_get_workflows_contains_json_files(self):
        """Test that get_workflows contains JSON files."""
        workflows = get_workflows()

        # Should contain at least the test workflows
        assert any(w.endswith(".json") for w in workflows)

    def test_get_workflows_filenames_only(self):
        """Test that get_workflows returns filenames only, not paths."""
        workflows = get_workflows()

        for w in workflows:
            assert "/" not in w  # Should not contain path separators
            assert "\\" not in w  # Should not contain path separators


class TestLoadWorkflow:
    """Test cases for load_workflow function."""

    def test_load_existing_workflow(self):
        """Test loading an existing workflow."""
        workflows = get_workflows()

        if workflows:
            workflow = load_workflow(workflows[0])

            assert workflow is not None
            assert isinstance(workflow, dict)

    def test_load_nonexistent_workflow(self):
        """Test loading a non-existent workflow."""
        workflow = load_workflow("nonexistent_workflow.json")

        assert workflow is None

    def test_load_workflow_is_valid_json(self):
        """Test that loaded workflow is valid JSON structure."""
        workflows = get_workflows()

        if workflows:
            workflow = load_workflow(workflows[0])

            # Should be a dictionary with node IDs as keys
            assert isinstance(workflow, dict)

            # Each value should have class_type
            for node_id, node_data in workflow.items():
                assert "class_type" in node_data

    def test_load_workflow_has_prompt_placeholder(self, sample_workflow):
        """Test that workflow with placeholder is detected."""
        # Create a temporary workflow file
        workflow_path = (
            Path(__file__).parent.parent / "workflows" / "test_placeholder.json"
        )

        try:
            with open(workflow_path, "w", encoding="utf-8") as f:
                json.dump(sample_workflow, f)

            # Load and verify
            workflow = load_workflow("test_placeholder.json")

            assert workflow is not None
            assert "1" in workflow  # Should have the prompt node
            assert "YOUR PROMPT HERE" in workflow["1"]["inputs"]["prompt"]
        finally:
            # Clean up
            if workflow_path.exists():
                workflow_path.unlink()

    def test_load_workflow_without_placeholder(self):
        """Test loading a workflow without prompt placeholder."""
        # Create a workflow without placeholder
        workflow_no_placeholder = {
            "1": {
                "inputs": {"prompt": "actual prompt text", "clip": ["2", 0]},
                "class_type": "CLIPTextEncode",
            }
        }

        workflow_path = (
            Path(__file__).parent.parent / "workflows" / "test_no_placeholder.json"
        )

        try:
            with open(workflow_path, "w", encoding="utf-8") as f:
                json.dump(workflow_no_placeholder, f)

            # Load and verify
            workflow = load_workflow("test_no_placeholder.json")

            assert workflow is not None
            assert "YOUR PROMPT HERE" not in workflow["1"]["inputs"]["prompt"]
        finally:
            # Clean up
            if workflow_path.exists():
                workflow_path.unlink()

    def test_load_workflow_with_multiple_nodes(self, sample_workflow):
        """Test loading a workflow with multiple nodes."""
        workflow_path = (
            Path(__file__).parent.parent / "workflows" / "test_multi_node.json"
        )

        try:
            with open(workflow_path, "w", encoding="utf-8") as f:
                json.dump(sample_workflow, f)

            workflow = load_workflow("test_multi_node.json")

            assert len(workflow) == 5  # Should have 5 nodes
            assert "1" in workflow
            assert "2" in workflow
            assert "3" in workflow
            assert "4" in workflow
            assert "5" in workflow
        finally:
            # Clean up
            if workflow_path.exists():
                workflow_path.unlink()

    def test_load_workflow_encoding(self):
        """Test that workflow is loaded with correct encoding."""
        # Create a workflow with unicode characters
        workflow_unicode = {
            "1": {
                "inputs": {
                    "prompt": "YOUR PROMPT HERE",
                    "description": "Résumé en français: café, naïve, élève",
                },
                "class_type": "CLIPTextEncode",
            }
        }

        workflow_path = Path(__file__).parent.parent / "workflows" / "test_unicode.json"

        try:
            with open(workflow_path, "w", encoding="utf-8") as f:
                json.dump(workflow_unicode, f, ensure_ascii=False)

            workflow = load_workflow("test_unicode.json")

            assert workflow is not None
            assert "café" in workflow["1"]["inputs"]["description"]
        finally:
            # Clean up
            if workflow_path.exists():
                workflow_path.unlink()
