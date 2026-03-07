"""Workflow management service for loading and listing ComfyUI workflows."""

import json
from pathlib import Path


def get_workflows():
    """Get list of available workflow JSON files.

    Returns:
        list of workflow filenames
    """
    # Get the extension root directory (parent of core/)
    extension_root = Path(__file__).parent.parent
    workflow_path = extension_root / "workflows"
    if not workflow_path.exists():
        return []
    return [f.name for f in workflow_path.glob("*.json")]


def load_workflow(workflow_name):
    """Load a workflow JSON file.

    Args:
        workflow_name: Name of the workflow file

    Returns:
        workflow dict or None if not found
    """
    # Get the extension root directory (parent of core/)
    extension_root = Path(__file__).parent.parent
    workflow_path = extension_root / "workflows" / workflow_name
    if not workflow_path.exists():
        return None
    with open(workflow_path, "r", encoding="utf-8") as f:
        return json.load(f)
