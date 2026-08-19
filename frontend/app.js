const API_BASE = "http://localhost:8000/api";

const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const healthBtn = document.getElementById("healthBtn");
const documentInput = document.getElementById("documentInput");
const uploadBtn = document.getElementById("uploadBtn");
const uploadStatus = document.getElementById("uploadStatus");

function addMessage(content, sender = "bot") {
  const msg = document.createElement("div");
  msg.className = `message ${sender}`;
  msg.textContent = content;
  chatMessages.appendChild(msg);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function checkApi() {
  try {
    const response = await fetch("http://localhost:8000/health");
    const data = await response.json();
    addMessage(`API status: ${data.status} (${data.app})`, "bot");
  } catch (error) {
    addMessage("The backend is not running. Start it with: uvicorn app.main:app --reload", "bot");
    console.error(error);
  }
}

async function sendChatMessage(message) {
  addMessage(message, "user");
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();
    addMessage(data.reply || "No response received.", "bot");
  } catch (error) {
    addMessage("The chat service is unavailable. Please check the backend server.", "bot");
    console.error(error);
  }
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) {
    return;
  }

  messageInput.value = "";
  await sendChatMessage(message);
});

healthBtn.addEventListener("click", checkApi);

uploadBtn.addEventListener("click", async () => {
  const file = documentInput.files[0];
  if (!file) {
    uploadStatus.textContent = "Please choose a PDF file first.";
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE}/documents/upload`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Upload failed");
    }

    uploadStatus.textContent = `Uploaded ${data.filename} with ${data.chunks} chunks.`;
    uploadStatus.className = "status success";
  } catch (error) {
    uploadStatus.textContent = error.message;
    uploadStatus.className = "status";
  }
});

checkApi();
