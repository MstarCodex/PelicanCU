function toggleChatbox() {
    const chatbox = document.getElementById('chatbox-container');
    if (chatbox.style.display === 'none' || chatbox.style.display === '') {
        chatbox.style.display = 'block';
    } else {
        chatbox.style.display = 'none';
    }
}

function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    if (message !== '') {
        const chatMessages = document.getElementById('chatbox-messages');
        const newMessage = document.createElement('p');
        newMessage.textContent = 'You: ' + message;
        chatMessages.appendChild(newMessage);
        messageInput.value = '';

        // Example admin reply (replace this with dynamic reply from the admin dashboard)
        setTimeout(() => {
            const adminReply = document.createElement('p');
            adminReply.textContent = 'Admin: This is a reply from the admin!';
            chatMessages.appendChild(adminReply);
            chatMessages.scrollTop = chatMessages.scrollHeight; // Auto scroll to bottom
        }, 1000); // Simulate a delay for admin reply
    }
}
