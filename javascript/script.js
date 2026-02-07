
console.log('Comment feature extension loaded');

// Create and inject the popup HTML if it doesn't exist
if (!document.getElementById('comment-popup')) {
    const popupHtml = `
    <div id="comment-popup">
        <textarea id="comment-text" placeholder="Add your comment here..."></textarea>
        <div class="buttons">
            <button class="comfy">Comfy</button>
            <button class="cancel">Cancel</button>
            <button class="submit">Add Comment</button>
        </div>
    </div>
    <button id="comment-trigger-btn">Comment</button>
    `;
    document.body.insertAdjacentHTML('beforeend', popupHtml);
}

const popup = document.getElementById('comment-popup');
const triggerBtn = document.getElementById('comment-trigger-btn');
const commentText = document.getElementById('comment-text');
const submitBtn = popup.querySelector('.submit');
const cancelBtn = popup.querySelector('.cancel');
const comfyBtn = popup.querySelector('.comfy');

let selectedText = '';

// Handle text selection
document.addEventListener('mouseup', (e) => {
    // Ignore if clicking inside the popup or trigger button
    if (popup.contains(e.target) || triggerBtn.contains(e.target)) {
        return;
    }

    const selection = window.getSelection();
    if (selection.isCollapsed) {
        triggerBtn.style.display = 'none';
        return;
    }

    const text = selection.toString().trim();
    if (!text) {
        triggerBtn.style.display = 'none';
        return;
    }

    let node = selection.anchorNode;
    // If text node, get parent
    if (node.nodeType === 3) {
        node = node.parentElement;
    }

    // Check if selection is within the chat area or a message
    // We check for #chat OR .message class to be safe
    const isChat = node.closest('#chat') || node.closest('.message') || node.closest('.message-body');

    if (isChat) {
        console.log('Selection detected in chat:', text);
        selectedText = text;

        // Position the trigger button near the selection
        // We use getRangeAt(0) to get the bounding rect of the selection
        try {
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();

            // Account for scroll
            const top = window.scrollY + rect.bottom + 5;
            const left = window.scrollX + rect.right;

            triggerBtn.style.display = 'block';
            triggerBtn.style.top = `${top}px`;
            triggerBtn.style.left = `${left}px`;

            // Hide popup if open (to reset)
            popup.style.display = 'none';
        } catch (err) {
            console.error('Error getting selection rect:', err);
        }
    } else {
        triggerBtn.style.display = 'none';
    }
});

// Show popup when trigger button is clicked
triggerBtn.addEventListener('click', (e) => {
    e.stopPropagation(); // Prevent document click from hiding it immediately if we had that logic
    triggerBtn.style.display = 'none';
    popup.style.display = 'flex';

    // Position popup where the button was
    popup.style.top = triggerBtn.style.top;
    popup.style.left = triggerBtn.style.left;

    commentText.value = '';
    commentText.focus();
});

// Handle cancel
cancelBtn.addEventListener('click', () => {
    popup.style.display = 'none';
});

// Handle submit
submitBtn.addEventListener('click', () => {
    const comment = commentText.value.trim();
    if (comment) {
        const formattedComment = `[Assistant said] ${selectedText}\nComment: ${comment}\n`;

        // Find the chat input textarea
        // Gradio structure can vary, usually it's inside #chat-input or has a specific class
        // We try multiple selectors
        const chatInput = document.querySelector('#chat-input textarea') || document.querySelector('textarea[data-testid="textbox"]');

        if (chatInput) {
            const currentVal = chatInput.value;
            // Append or set? Usually append if user typed something, but here we might want to just set or prepend.
            // Let's append with a newline if not empty
            chatInput.value = currentVal ? `${currentVal}\n\n${formattedComment}` : formattedComment;

            // Trigger input event to update Gradio state
            chatInput.dispatchEvent(new Event('input', { bubbles: true }));
            chatInput.focus();
        } else {
            console.error('Chat input textarea not found');
            alert('Could not find chat input box to insert comment.');
        }
    }
    popup.style.display = 'none';
});

// Handle ComfyUI generation
comfyBtn.addEventListener('click', () => {
    if (selectedText) {
        // Find hidden gradio elements
        const hiddenPrompt = document.querySelector('#comfy_hidden_prompt textarea');
        const hiddenTrigger = document.querySelector('#comfy_hidden_trigger');

        if (hiddenPrompt && hiddenTrigger) {
            // Set the value
            hiddenPrompt.value = selectedText;
            hiddenPrompt.dispatchEvent(new Event('input', { bubbles: true }));

            // Trigger click
            hiddenTrigger.click();

            // Show feedback
            const originalText = comfyBtn.innerText;
            comfyBtn.innerText = 'Generating...';
            setTimeout(() => {
                comfyBtn.innerText = originalText;
                popup.style.display = 'none';
            }, 2000); // Feedback duration
        } else {
            console.error('Hidden ComfyUI elements not found');
            alert('ComfyUI integration elements not found. Make sure the extension is loaded correctly.');
        }
    }
});
