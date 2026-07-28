import { createSevenAvatar } from "./seven-avatar.js";

const API_BASE = "/3dwebsite/seven-api";
const $ = (selector) => document.querySelector(selector);
const home = $("#seven-home");
const messageIds = new Set();
const pendingTurns = new Set();

let avatar = { setState() {}, start() {}, stop() {}, destroy() {} };
let avatarReady = false;
let csrfToken = "";
let authenticated = false;
let eventSource = null;
let reconnectTimer = 0;
let reconnectAttempts = 0;
let recorder = null;
let recorderStream = null;
let recorderChunks = [];
let discardRecording = false;
let cameraStream = null;
let speechEnabled = false;
let lastFocus = null;

function setStatus(state, message) {
  home.dataset.state = state;
  $("#seven-connection").textContent = message;
  $("#seven-presence-value").textContent = state === "error" ? "Interrupted" : state === "disconnected" ? "Offline" : "Present";
  $("#seven-mode-value").textContent = state.charAt(0).toUpperCase() + state.slice(1);
  avatar.setState(state);
}

function formStatus(element, message, tone = "") {
  element.textContent = message;
  if (tone) element.dataset.tone = tone;
  else delete element.dataset.tone;
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : { message: await response.text() };
  if (!response.ok) {
    const error = new Error(payload.error || payload.message || `Request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return payload;
}

async function apiFetch(path, options = {}) {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  if (url.origin !== window.location.origin) throw new Error("Cross-origin gateway request refused.");
  const headers = new Headers(options.headers || {});
  if (csrfToken && options.method && options.method !== "GET") headers.set("X-CSRF-Token", csrfToken);
  if (options.body && typeof options.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "same-origin",
    cache: "no-store",
  });
  if (response.status === 401 && path !== "/api/session" && path !== "/api/login") {
    showAuthenticated(false);
  }
  return parseResponse(response);
}

function showAuthenticated(isAuthenticated, identity = "") {
  authenticated = Boolean(isAuthenticated);
  $("#seven-login").hidden = authenticated;
  $("#seven-chat").hidden = !authenticated;
  $("#seven-session").hidden = !authenticated;
  $("#seven-identity").textContent = identity || "Authenticated";
  if (authenticated) {
    setStatus("connected", "Secure channel connected");
    connectEvents();
    requestAnimationFrame(() => $("#seven-input").focus());
  } else {
    disconnectEvents();
    setStatus("disconnected", "Authentication required");
    stopAllMedia();
  }
}

async function refreshSession() {
  setStatus("connecting", "Checking secure session");
  try {
    const session = await apiFetch("/api/session", { method: "GET" });
    csrfToken = session.csrf || "";
    showAuthenticated(session.ok === true, "Owner");
  } catch (error) {
    if (error.status === 401) {
      showAuthenticated(false);
      formStatus($("#seven-login-status"), "Sign in to continue.");
      setStatus("disconnected", "Authentication required");
      return;
    }
    showAuthenticated(false);
    formStatus($("#seven-login-status"), "The private gateway is not available yet.", "error");
    setStatus("error", "Gateway unavailable");
  }
}

function appendMessage(role, text, id = "") {
  if (!text || (id && messageIds.has(id))) return;
  if (id) messageIds.add(id);
  const article = document.createElement("article");
  article.className = `seven-message seven-message-${role === "user" ? "user" : role === "system" ? "system" : "assistant"}`;
  if (id) article.dataset.messageId = id;
  const author = document.createElement("b");
  author.textContent = role === "user" ? "You" : role === "system" ? "System" : "Seven";
  const body = document.createElement("p");
  body.textContent = String(text);
  article.append(author, body);
  $("#seven-messages").append(article);
  article.scrollIntoView({ block: "end", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  if (role === "assistant") speak(text);
}

function handleEvent(payload) {
  if (!payload || typeof payload !== "object") return;
  if (payload.csrf) csrfToken = payload.csrf;
  if (payload.kind === "turn_status" && payload.payload?.turn_id) {
    const turnId = Number(payload.payload.turn_id);
    if (payload.payload.status === "complete" || payload.payload.status === "failed") {
      fetchTurn(turnId);
    }
  } else if (payload.type === "message" || payload.message) {
    appendMessage(payload.role || "assistant", payload.text || payload.message, payload.id || payload.message_id || "");
    if ((payload.role || "assistant") === "assistant") setStatus("ready", "Seven is present");
  } else if (payload.type === "status") {
    setStatus(payload.state || "connected", payload.label || payload.message || "Secure channel connected");
  }
}

function scheduleReconnect() {
  clearTimeout(reconnectTimer);
  if (!authenticated || document.hidden) return;
  reconnectAttempts += 1;
  const delay = Math.min(30000, 900 * (2 ** Math.min(reconnectAttempts, 5))) + Math.round(Math.random() * 350);
  setStatus("connecting", `Reconnecting in ${Math.ceil(delay / 1000)}s`);
  reconnectTimer = window.setTimeout(connectEvents, delay);
}

function connectEvents() {
  disconnectEvents(false);
  if (!authenticated || document.hidden) return;
  const url = new URL(`${API_BASE}/api/events`, window.location.origin);
  eventSource = new EventSource(url, { withCredentials: true });
  eventSource.onopen = () => {
    reconnectAttempts = 0;
    setStatus("connected", "Secure channel connected");
  };
  eventSource.onmessage = (event) => {
    try { handleEvent(JSON.parse(event.data)); }
    catch { formStatus($("#seven-chat-status"), "Received an unreadable gateway event.", "error"); }
  };
  eventSource.addEventListener("status", (event) => {
    try { handleEvent({ type: "status", ...JSON.parse(event.data) }); } catch {}
  });
  eventSource.addEventListener("turn_status", (event) => {
    try { handleEvent(JSON.parse(event.data)); } catch {}
  });
  eventSource.onerror = () => {
    eventSource?.close();
    eventSource = null;
    scheduleReconnect();
  };
}

function disconnectEvents(clearPending = true) {
  eventSource?.close();
  eventSource = null;
  if (clearPending) clearTimeout(reconnectTimer);
}

async function sendMessage(text) {
  const clientMessageId = crypto.randomUUID();
  appendMessage("user", text, clientMessageId);
  setStatus("thinking", "Seven is thinking");
  formStatus($("#seven-chat-status"), "Message delivered to the private gateway.");
  try {
    const result = await apiFetch("/api/turn", {
      method: "POST",
      body: JSON.stringify({ message: text }),
    });
    const turnId = Number(result.turn_id);
    if (!Number.isInteger(turnId) || turnId < 1) throw new Error("Gateway returned an invalid turn.");
    pendingTurns.add(turnId);
    pollTurn(turnId);
  } catch (error) {
    appendMessage("system", `Message not accepted: ${error.message}`);
    formStatus($("#seven-chat-status"), error.message, "error");
    setStatus("error", "Message failed");
  }
}

async function fetchTurn(turnId) {
  if (!pendingTurns.has(turnId)) return;
  try {
    const result = await apiFetch(`/api/turn?id=${encodeURIComponent(turnId)}`, { method: "GET" });
    const turn = result.turn || {};
    if (turn.status === "complete") {
      pendingTurns.delete(turnId);
      appendMessage("assistant", turn.reply || "", `turn-${turnId}`);
      formStatus($("#seven-chat-status"), "Seven replied through the private gateway.", "success");
      setStatus("ready", "Seven is present");
      return;
    }
    if (turn.status === "failed" || turn.status === "rejected") {
      pendingTurns.delete(turnId);
      throw new Error(turn.error_code || "Seven could not complete this turn.");
    }
  } catch (error) {
    pendingTurns.delete(turnId);
    appendMessage("system", `Turn failed: ${error.message}`, `turn-error-${turnId}`);
    formStatus($("#seven-chat-status"), error.message, "error");
    setStatus("error", "Turn failed");
  }
}

function pollTurn(turnId, attempt = 0) {
  if (!pendingTurns.has(turnId)) return;
  window.setTimeout(async () => {
    await fetchTurn(turnId);
    if (pendingTurns.has(turnId)) pollTurn(turnId, attempt + 1);
  }, Math.min(2500, 350 + attempt * 150));
}

function speak(text) {
  if (!speechEnabled || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(String(text).slice(0, 4000));
  utterance.rate = 0.96;
  utterance.pitch = 1.02;
  utterance.onstart = () => setStatus("speaking", "Seven is speaking");
  utterance.onend = () => setStatus("ready", "Seven is present");
  utterance.onerror = () => setStatus("ready", "Seven is present");
  window.speechSynthesis.speak(utterance);
}

function stopRecorderStream() {
  recorderStream?.getTracks().forEach((track) => track.stop());
  recorderStream = null;
  $("#seven-record").classList.remove("recording");
  $("#seven-record").textContent = "Hold to record";
}

async function uploadRecording(blob) {
  setStatus("thinking", "Validating locally captured audio");
  try {
    const result = await apiFetch("/api/media/audio", {
      method: "POST",
      headers: { "Content-Type": blob.type || "audio/webm" },
      body: blob,
    });
    $("#seven-input").value = result.transcript || "";
    $("#seven-input").focus();
    formStatus($("#seven-chat-status"), "Local transcription is ready to review. Press Send when you choose.", "success");
    setStatus("ready", "Transcription ready");
  } catch (error) {
    formStatus($("#seven-chat-status"), `Audio validation failed: ${error.message}`, "error");
    setStatus("error", "Audio validation failed");
  }
}

async function startRecording(event) {
  if (!authenticated || recorder || event.button > 0) return;
  event.preventDefault();
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    formStatus($("#seven-chat-status"), "This browser does not support microphone capture.", "error");
    return;
  }
  try {
    recorderStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    recorderChunks = [];
    discardRecording = false;
    recorder = new MediaRecorder(recorderStream);
    recorder.ondataavailable = (chunk) => { if (chunk.data.size) recorderChunks.push(chunk.data); };
    recorder.onstop = () => {
      const blob = new Blob(recorderChunks, { type: recorder.mimeType || "audio/webm" });
      const shouldDiscard = discardRecording;
      recorder = null;
      recorderChunks = [];
      discardRecording = false;
      stopRecorderStream();
      if (!shouldDiscard && blob.size) uploadRecording(blob);
    };
    recorder.start();
    $("#seven-record").classList.add("recording");
    $("#seven-record").textContent = "Release to validate";
    setStatus("listening", "Listening while you hold");
    if (event.pointerId !== undefined) event.currentTarget.setPointerCapture?.(event.pointerId);
  } catch (error) {
    stopRecorderStream();
    formStatus($("#seven-chat-status"), `Microphone unavailable: ${error.message}`, "error");
    setStatus("error", "Microphone unavailable");
  }
}

function stopRecording(event) {
  event?.preventDefault();
  if (recorder?.state === "recording") recorder.stop();
}

async function enableCamera() {
  if (cameraStream) {
    stopCamera();
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia) {
    formStatus($("#seven-chat-status"), "This browser does not support camera capture.", "error");
    return;
  }
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
    const preview = $("#seven-camera-preview");
    preview.srcObject = cameraStream;
    $("#seven-camera-panel").hidden = false;
    $("#seven-camera-enable").textContent = "Camera active";
    setStatus("listening", "Local camera preview");
  } catch (error) {
    formStatus($("#seven-chat-status"), `Camera unavailable: ${error.message}`, "error");
    setStatus("error", "Camera unavailable");
  }
}

function stopCamera() {
  cameraStream?.getTracks().forEach((track) => track.stop());
  cameraStream = null;
  const preview = $("#seven-camera-preview");
  preview.pause();
  preview.srcObject = null;
  $("#seven-camera-panel").hidden = true;
  $("#seven-camera-enable").textContent = "Enable camera";
  if (authenticated) setStatus("ready", "Seven is present");
}

async function sendSnapshot() {
  const preview = $("#seven-camera-preview");
  if (!cameraStream || !preview.videoWidth) {
    formStatus($("#seven-chat-status"), "Wait for the local preview before sending a snapshot.", "error");
    return;
  }
  const canvas = document.createElement("canvas");
  canvas.width = Math.min(preview.videoWidth, 1280);
  canvas.height = Math.round(canvas.width * preview.videoHeight / preview.videoWidth);
  canvas.getContext("2d", { alpha: false }).drawImage(preview, 0, 0, canvas.width, canvas.height);
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.86));
  stopCamera();
  if (!blob) return;
  setStatus("thinking", "Validating the snapshot");
  try {
    const result = await apiFetch("/api/media/jpeg", {
      method: "POST",
      headers: { "Content-Type": "image/jpeg" },
      body: blob,
    });
    appendMessage("assistant", result.reply || "I could not describe the snapshot.");
    formStatus($("#seven-chat-status"), "Seven analyzed the snapshot. Camera access has stopped.", "success");
    setStatus("ready", "Seven is present");
  } catch (error) {
    formStatus($("#seven-chat-status"), `Snapshot failed: ${error.message}`, "error");
    setStatus("error", "Snapshot failed");
  }
}

function stopAllMedia() {
  if (recorder?.state === "recording") {
    discardRecording = true;
    recorder.stop();
  }
  else stopRecorderStream();
  stopCamera();
  window.speechSynthesis?.cancel();
}

function openSeven() {
  lastFocus = document.activeElement;
  home.hidden = false;
  document.body.classList.add("seven-open");
  $(".topbar nav")?.classList.remove("open");
  $("#menu-button")?.setAttribute("aria-expanded", "false");
  if (!avatarReady) {
    avatar = createSevenAvatar($("#seven-avatar"));
    avatarReady = true;
    avatar.setState(home.dataset.state || "disconnected");
  }
  avatar.start();
  refreshSession();
  requestAnimationFrame(() => $("#seven-close").focus());
}

function closeSeven() {
  stopAllMedia();
  disconnectEvents();
  avatar.stop();
  home.hidden = true;
  document.body.classList.remove("seven-open");
  lastFocus?.focus?.();
}

$("#seven-home-button").addEventListener("click", openSeven);
$("#seven-close").addEventListener("click", closeSeven);
$("#seven-login").addEventListener("submit", async (event) => {
  event.preventDefault();
  formStatus($("#seven-login-status"), "Authenticating…");
  setStatus("connecting", "Authenticating");
  try {
    const result = await apiFetch("/api/login", {
      method: "POST",
      body: JSON.stringify({
        username: $("#seven-username").value.trim(),
        password: $("#seven-passphrase").value,
      }),
    });
    csrfToken = result.csrf || csrfToken;
    $("#seven-passphrase").value = "";
    formStatus($("#seven-login-status"), "");
    showAuthenticated(result.ok === true, "Owner");
  } catch (error) {
    $("#seven-passphrase").value = "";
    formStatus($("#seven-login-status"), error.message, "error");
    setStatus("error", "Authentication failed");
  }
});
$("#seven-logout").addEventListener("click", async () => {
  try { await apiFetch("/api/logout", { method: "POST", body: JSON.stringify({}) }); } catch {}
  csrfToken = "";
  showAuthenticated(false);
});
$("#seven-composer").addEventListener("submit", (event) => {
  event.preventDefault();
  const text = $("#seven-input").value.trim();
  if (!text || !authenticated) return;
  $("#seven-input").value = "";
  sendMessage(text);
});
$("#seven-input").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    $("#seven-composer").requestSubmit();
  }
});
$("#seven-voice-toggle").addEventListener("click", (event) => {
  speechEnabled = !speechEnabled;
  event.currentTarget.setAttribute("aria-pressed", String(speechEnabled));
  event.currentTarget.textContent = speechEnabled ? "Voice on" : "Voice muted";
  if (!speechEnabled) window.speechSynthesis?.cancel();
});
$("#seven-record").addEventListener("pointerdown", startRecording);
$("#seven-record").addEventListener("pointerup", stopRecording);
$("#seven-record").addEventListener("pointercancel", stopRecording);
$("#seven-record").addEventListener("keydown", (event) => {
  if ((event.key === " " || event.key === "Enter") && !event.repeat) startRecording(event);
});
$("#seven-record").addEventListener("keyup", (event) => {
  if (event.key === " " || event.key === "Enter") stopRecording(event);
});
$("#seven-camera-enable").addEventListener("click", enableCamera);
$("#seven-camera-stop").addEventListener("click", stopCamera);
$("#seven-camera-send").addEventListener("click", sendSnapshot);
home.addEventListener("keydown", (event) => {
  event.stopPropagation();
  if (event.key === "Escape") closeSeven();
});
home.addEventListener("keyup", (event) => event.stopPropagation());
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    disconnectEvents();
    stopAllMedia();
  } else if (!home.hidden && authenticated) {
    connectEvents();
  }
});
window.addEventListener("pagehide", stopAllMedia);
setStatus("disconnected", "Open Seven to connect");
