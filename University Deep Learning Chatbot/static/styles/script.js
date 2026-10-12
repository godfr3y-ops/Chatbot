(function () {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("question");
  const sendButton = document.getElementById("submit-button");
  const chatMessages = document.getElementById("chat-messages");
  const aboutModal = document.getElementById("about-modal");
  const feedbackModal = document.getElementById("feedback-modal");
  const feedbackStatus = document.getElementById("feedback-status");
  const suggestionInput = document.getElementById("suggestion");

  function escapeHtml(value) {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function linkify(text) {
    const escaped = escapeHtml(text);
    return escaped
      .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>')
      .replace(/\n/g, "<br>");
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendMessage(role, text, options) {
    const isUser = role === "user";
    const wrapping = document.createElement("div");
    wrapping.className = "msg " + (isUser ? "right-msg" : "left-msg");
    if (options && options.typing) {
      wrapping.classList.add("typing");
      wrapping.dataset.typing = "1";
    }

    const name = isUser ? "You" : "BUSE Bot";
    wrapping.innerHTML =
      '<div class="msg-bubble">' +
      '<div class="msg-info"><span class="msg-info-name">' +
      name +
      "</span></div>" +
      '<div class="msg-text">' +
      (options && options.typing ? "..." : linkify(text)) +
      "</div></div>";

    chatMessages.appendChild(wrapping);
    scrollToBottom();
    return wrapping;
  }

  function removeTyping() {
    const typing = chatMessages.querySelector('[data-typing="1"]');
    if (typing) {
      typing.remove();
    }
  }

  async function askBot(question) {
    const trimmed = (question || "").trim();
    if (!trimmed) {
      return;
    }

    appendMessage("user", trimmed);
    input.value = "";
    sendButton.disabled = true;
    appendMessage("bot", "...", { typing: true });

    try {
      const body = new URLSearchParams();
      body.set("question", trimmed);
      const response = await fetch("/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
      });
      const data = await response.json();
      removeTyping();
      appendMessage("bot", data.response || "Sorry, I could not answer that.");
    } catch (error) {
      removeTyping();
      appendMessage("bot", "Sorry, something went wrong. Please try again.");
    } finally {
      sendButton.disabled = false;
      input.focus();
    }
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    askBot(input.value);
  });

  document.querySelectorAll(".chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      askBot(chip.dataset.question || chip.textContent);
    });
  });

  document.querySelectorAll("[data-open]").forEach(function (button) {
    button.addEventListener("click", function () {
      const target = button.getAttribute("data-open");
      if (target === "about") {
        aboutModal.showModal();
      }
      if (target === "feedback") {
        feedbackStatus.hidden = true;
        feedbackStatus.textContent = "";
        feedbackModal.showModal();
      }
    });
  });

  document.getElementById("feedback-cancel").addEventListener("click", function () {
    feedbackModal.close();
  });

  document.getElementById("feedback-submit").addEventListener("click", async function () {
    const suggestion = suggestionInput.value.trim();
    if (!suggestion) {
      feedbackStatus.hidden = false;
      feedbackStatus.textContent = "Please enter a suggestion first.";
      return;
    }

    try {
      const response = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ suggestion: suggestion }),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || "Could not save feedback");
      }
      suggestionInput.value = "";
      feedbackStatus.hidden = false;
      feedbackStatus.textContent = data.message || "Thank you for your feedback.";
      setTimeout(function () {
        feedbackModal.close();
      }, 900);
    } catch (error) {
      feedbackStatus.hidden = false;
      feedbackStatus.textContent = "Could not submit feedback. Please try again.";
    }
  });

  appendMessage(
    "bot",
    "Hello! I am BUSE Bot. Ask me about admissions, fees, faculties, accommodation, or campus services — or tap a topic above."
  );
})();
