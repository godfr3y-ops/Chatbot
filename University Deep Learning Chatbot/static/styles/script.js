const questionInput = document.getElementById('question');
const chatMessages = document.getElementById('chat-messages');

questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        const question = questionInput.value.trim();
        if (question !== '') {
            appendUserQuestion(question);
            questionInput.value = '';
            sendQuestionToBackend(question);
        }
    }
});

function appendUserQuestion(question) {
    const userBubble = document.createElement('div');
    userBubble.className = 'msg right-msg';
    userBubble.innerHTML = `
        <div class="msg-bubble">
            <div class="msg-info">
                <div class="msg-info-name"><b>You</b></div>
            </div>
            <div class="msg-text">${question}</div>
        </div>
    `;
    chatMessages.appendChild(userBubble);
}

function sendQuestionToBackend(question) {
    fetch('/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
    })
    .then((response) => response.json())
    .then((data) => appendBotResponse(data.response))
    .catch((error) => console.error('Error:', error));
}

function appendBotResponse(response) {
    const botBubble = document.createElement('div');
    botBubble.className = 'msg left-msg';
    botBubble.innerHTML = `
        <div class="msg-bubble">
            <div class="msg-info">
                <div class="msg-info-name"><b>BUSE Bot</b></div>
            </div>
            <div class="msg-text">${response}</div>
        </div>
    `;
    chatMessages.appendChild(botBubble);
}