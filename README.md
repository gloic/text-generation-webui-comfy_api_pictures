# Comment Feature Extension

This extension allows you to select text in the chat history and add a comment. The commented text and your comment are automatically inserted into the chat input, ready to be sent to the LLM.

## Features

- **Text Selection**: Select any text in the chat to trigger the comment button.
- **Comment Popup**: A simple popup to enter your comment.
- **Auto-Formatting**: Inserts `[Assistant said] "..." Comment: "..."` into the input box.

## Installation

1.  Copy the `comment_feature` folder to your `extensions/` directory.
2.  Install requirements (none for this extension).

## Usage

1.  Enable the extension via the **Session** tab or by launching with `--extensions comment_feature`.
2.  Select text in the chat.
3.  Click the "Comment" button.
4.  Enter your comment and click "Add Comment".