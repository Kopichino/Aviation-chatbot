// 1. Generate a Unique Session ID
const sessionId = "user_" + Math.random().toString(36).substring(7);
console.log("Session ID:", sessionId);

// 2. Select Elements
const chatContainer = document.getElementById("chat-container");
const chatToggleBtn = document.getElementById("chat-toggle-btn");
const closeChatBtn = document.getElementById("close-chat");
const sendBtn = document.getElementById("send-btn");
const userInput = document.getElementById("user-input");
const messagesDiv = document.getElementById("chat-messages");

// 3. Toggle Chat Window
chatToggleBtn.addEventListener("click", () => {
  chatContainer.style.display = "flex";
  chatToggleBtn.style.display = "none";

  // Trigger welcome message if chat is empty
  if (messagesDiv.children.length <= 1) {
    triggerWelcomeMessage();
  }
});

closeChatBtn.addEventListener("click", () => {
  chatContainer.style.display = "none";
  chatToggleBtn.style.display = "flex"; // Show toggle button again
});

// 4. Trigger Backend Welcome (Hidden "Hi")
async function triggerWelcomeMessage() {
  await sendMessage("Hi", true);
}

// 5. Main Send Function
async function sendMessage(text, isHidden = false) {
  if (!text.trim()) return; // Don't send empty spaces

  // A. INSTANTLY Add User Message to UI (unless hidden)
  if (!isHidden) {
    addMessage(text, "user-message");
    userInput.value = ""; // Clear input box immediately
    userInput.focus(); // Keep focus on input
  }

  // B. Show Loading Indicator
  const loadingId = addMessage("Typing...", "bot-message");

  try {
    // C. Send to Backend
    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        session_id: sessionId,
      }),
    });

    const data = await response.json();

    // D. Remove Loading & Show Answer
    removeMessage(loadingId);
    addMessage(data.response, "bot-message");
  } catch (error) {
    removeMessage(loadingId);
    addMessage("⚠️ Error: Backend not running.", "bot-message");
    console.error(error);
  }
}

// 6. UI Helper: Add Message Bubble
function addMessage(text, className) {
  const div = document.createElement("div");
  div.classList.add("message", className);

  // Format bold text (**text** -> <b>text</b>)
  const formattedText = text.replace(/\*\*(.*?)\*\*/g, "<b>$1</b>");
  div.innerHTML = formattedText;

  div.id = "msg-" + Date.now() + Math.random(); // Unique ID
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight; // Auto-scroll to bottom
  return div.id;
}

// 7. UI Helper: Remove Message
function removeMessage(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// 8. Event Listeners
// --- PREVENT DOUBLE SENDING ---

sendBtn.addEventListener("click", (e) => {
  e.preventDefault(); // Stop default button behavior
  sendMessage(userInput.value);
});

userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    e.preventDefault(); // Stop "form submit" behavior
    sendMessage(userInput.value);
  }
});
