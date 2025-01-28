document.getElementById("sendButton").addEventListener("click", sendMessage);
document.getElementById("userInput").addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
        sendMessage();
    }
});

function sendMessage() {
    const input = document.getElementById("userInput");
    const messageText = input.value.trim();
    if (!messageText) return;

    // Dodanie wiadomości użytkownika
    const chatboxMessages = document.querySelector(".chatbox-messages");
    addMessage(messageText, "sent");

    // Wysłanie wiadomości do serwera Flask
    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: messageText, language: "pl" })
    })
    .then(response => response.json())
    .then(data => {
        if (data.response) {
            addMessage(data.response, "received");
        }
    })
    .catch(error => console.error("Błąd:", error));

    input.value = "";
    chatboxMessages.scrollTop = chatboxMessages.scrollHeight;
}

function addMessage(text, type) {
    const messageElement = document.createElement("div");
    messageElement.className = `message ${type}`;
    messageElement.textContent = text;
    document.querySelector(".chatbox-messages").appendChild(messageElement);
}
