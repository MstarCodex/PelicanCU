const socket = io.connect('http://' + document.domain + ':' + location.port);

function sendMessage() {
    const messageInput = document.getElementById("message");
    const message = messageInput.value;

    socket.emit('send_message', {
        sender: '{{ session["username"] }}',
        receiver: 'Mayor',
        message: message
    });

    messageInput.value = '';  // Clear the input field
}

socket.on('receive_message', function(data) {
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML += `<p><strong>${data.sender}:</strong> ${data.message}</p>`;
    chatBox.scrollTop = chatBox.scrollHeight;  // Auto-scroll to the latest message
});