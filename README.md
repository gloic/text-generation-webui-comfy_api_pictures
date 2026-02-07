# ComfyUI API Pictures Extension

This extension integrates ComfyUI with text-generation-webui, allowing the LLM to generate images based on its responses. It functions similarly to the `sd_api_pictures` extension but uses ComfyUI as the backend.

## Features

- **ComfyUI Integration**: Connects to a local ComfyUI instance to generate images.
- **In-Chat Generation**: The extension can automatically generate images and display them in the chat based on the LLM's response.
- **Interactive Modes**:
    - **Manual**: Only generates images when forced via the "Force the picture response" button.
    - **Immersive/Interactive**: Watches for trigger words (e.g., "send me a picture", "show me") in your input to automatically trigger image generation for the next response.
    - **Picturebook/Adventure**: Always generates an image for every response.
- **Workflow Support**: Select from available ComfyUI workflows (in JSON format) stored in the `extensions/comfy_api_pictures/comfyui/workflows` directory.

## Installation

1.  Ensure you have ComfyUI installed and running (default URL: `http://127.0.0.1:8188`).
2.  Copy this folder `comfy_api_pictures` to your `extensions/` directory in text-generation-webui.
3.  Install requirements (if any).

## Usage

1.  Enable the extension via the **Session** tab or by launching with `--extensions comfy_api_pictures`.
2.  In the "ComfyUI Generation" section of the UI:
    - **ComfyUI Server URL**: Set your ComfyUI address.
    - **Workflow**: Select a workflow JSON file. The workflow MUST have a node with an input named `prompt` or be a standard TextEncode node to receive the prompt from the LLM.
    - **Mode**: Choose how you want the generation to be triggered.
3.  **Modes**:
    - **Manual**: Click "Force the picture response" before sending a message to get an image.
    - **Interactive**: Say "send me a picture of a cat" to trigger generation.
    - **Picturebook**: Every message will have an accompanying image.