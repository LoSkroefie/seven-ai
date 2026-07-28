"use strict";

let csrf = "";
let events = null;

const loginPanel = document.querySelector("#login-panel");
const chatPanel = document.querySelector("#chat-panel");
const loginError = document.querySelector("#login-error");
const statusNode = document.querySelector("#status");
const conversation = document.querySelector("#conversation");

function addLine(kind, text) {
  const item = document.createElement("li");
  item.className = kind;
  item.textContent = text;
  conversation.append(item);
  item.scrollIntoView({ block: "end" });
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (csrf && options.method && options.method !== "GET") {
    headers.set("X-CSRF-Token", csrf);
  }
  const response = await fetch(path, { ...options, headers, credentials: "same-origin" });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "request_failed");
  return body;
}

async function unlock(password) {
  const body = await api("api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password })
  });
  csrf = body.csrf;
  loginPanel.classList.add("hidden");
  chatPanel.classList.remove("hidden");
  connectEvents();
}

async function resume() {
  try {
    const body = await api("api/session");
    csrf = body.csrf;
    loginPanel.classList.add("hidden");
    chatPanel.classList.remove("hidden");
    connectEvents();
  } catch (_) {
    loginPanel.classList.remove("hidden");
  }
}

function connectEvents() {
  if (events) events.close();
  events = new EventSource("api/events");
  events.addEventListener("turn_status", async event => {
    const value = JSON.parse(event.data);
    const payload = value.payload || {};
    statusNode.textContent = payload.status || "working";
    if (payload.status === "complete" && payload.turn_id) {
      try {
        const body = await api(`api/turn?id=${encodeURIComponent(payload.turn_id)}`);
        addLine("seven", body.turn.reply);
      } catch (_) {
        statusNode.textContent = "reply unavailable";
      }
    }
    if (payload.status === "failed") {
      addLine("seven", "I could not complete that turn. The failure was recorded.");
    }
  });
  events.onerror = () => { statusNode.textContent = "reconnecting"; };
}

document.querySelector("#login-form").addEventListener("submit", async event => {
  event.preventDefault();
  loginError.textContent = "";
  try {
    await unlock(document.querySelector("#password").value);
    document.querySelector("#password").value = "";
  } catch (_) {
    loginError.textContent = "The channel could not be opened.";
  }
});

document.querySelector("#chat-form").addEventListener("submit", async event => {
  event.preventDefault();
  const box = document.querySelector("#message");
  const message = box.value.trim();
  if (!message) return;
  addLine("owner", message);
  box.value = "";
  statusNode.textContent = "queued";
  try {
    await api("api/turn", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });
  } catch (_) {
    addLine("seven", "The message could not be queued.");
    statusNode.textContent = "error";
  }
});

document.querySelector("#logout").addEventListener("click", async () => {
  try { await api("api/logout", { method: "POST", body: "{}" }); } catch (_) {}
  csrf = "";
  if (events) events.close();
  chatPanel.classList.add("hidden");
  loginPanel.classList.remove("hidden");
  conversation.replaceChildren();
});

resume();

