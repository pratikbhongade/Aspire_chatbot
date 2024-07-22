function setupObserver() {
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {
        const observer = new MutationObserver(function(mutationsList, observer) {
            for (let mutation of mutationsList) {
                if (mutation.type === 'childList') {
                    console.log("Auto-scrolling to the bottom");  // Debugging output
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }
        });
        observer.observe(chatContainer, { childList: true });
    } else {
        console.error("Chat container not found, retrying...");  // Debugging output
        setTimeout(setupObserver, 500);  // Retry after 500ms
    }
}

document.addEventListener('DOMContentLoaded', setupObserver);
