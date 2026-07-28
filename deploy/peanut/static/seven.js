"use strict";

const $ = (selector) => document.querySelector(selector);
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const loginPanel = $("#login-panel");
const chatPanel = $("#chat-panel");
const loginError = $("#login-error");
const chatStatus = $("#chat-status");
const statusNode = $("#status");
const conversation = $("#conversation");
const messageBox = $("#message");
const portraitLayers = [$("#portrait-a"), $("#portrait-b")];
const fullbodyAvatar = $("#fullbody-avatar");

const portraits = Object.freeze({
  disconnected: "assets/seven-concerned.webp",
  connecting: "assets/seven-curious.webp",
  ready: "assets/seven-welcoming.webp",
  listening: "assets/seven-listening.webp",
  thinking: "assets/seven-thinking.webp",
  speaking: "assets/seven-speaking.webp",
  error: "assets/seven-concerned.webp",
  amused: "assets/seven-amused.webp",
  blink: "assets/seven-blink.webp",
  curious: "assets/seven-curious.webp",
  determined: "assets/seven-determined.webp",
});

const fullbody = Object.freeze({
  ready: "assets/seven-fullbody-welcome.webp",
  thinking: "assets/seven-fullbody-thinking.webp",
  default: "assets/seven-fullbody-idle.webp",
});

const stateCopy = Object.freeze({
  disconnected: {
    status: "locked",
    presence: "Waiting for you",
    mind: "offline",
    channel: "locked",
  },
  connecting: {
    status: "connecting",
    presence: "Opening the private channel",
    mind: "waking",
    channel: "handshake",
  },
  ready: {
    status: "present",
    presence: "I’m here with you",
    mind: "present",
    channel: "secure",
  },
  listening: {
    status: "listening",
    presence: "I’m listening",
    mind: "attentive",
    channel: "microphone",
  },
  thinking: {
    status: "thinking",
    presence: "Thinking about what you said",
    mind: "reasoning",
    channel: "secure",
  },
  speaking: {
    status: "speaking",
    presence: "Speaking with you",
    mind: "responding",
    channel: "secure",
  },
  error: {
    status: "interrupted",
    presence: "The channel needs a moment",
    mind: "recovering",
    channel: "interrupted",
  },
});

const errorMessages = Object.freeze({
  authentication_required: "Your secure session ended. Open the channel again.",
  invalid_credentials: "That owner password was not accepted.",
  origin_forbidden: "The gateway refused this browser origin.",
  csrf_invalid: "The secure session changed. Open the channel again.",
  queue_full: "Seven is still handling another request. Try again in a moment.",
  message_required: "Write a message before sending it.",
  message_too_large: "That message is too long for one turn.",
  turn_not_found: "That reply is no longer available in this session.",
  seven_internal_failure: "Seven could not complete that turn. The diagnostic was recorded privately.",
  vision_unavailable: "Seven’s visual model is not available right now.",
  transcription_unavailable: "Seven’s local transcription service is not available right now.",
  request_failed: "The private gateway did not complete the request.",
});

const pendingTurns = new Set();
const fetchingTurns = new Set();
const renderedMessages = new Set();
const pollTimers = new Map();

let csrf = "";
let authenticated = false;
let events = null;
let reconnectTimer = 0;
let reconnectAttempts = 0;
let activePortrait = 0;
let currentState = "disconnected";
let currentPortrait = portraitLayers[activePortrait].getAttribute("src") || "";
let idleStep = 0;
let idleTimer = 0;
let greetingShown = false;
let speechEnabled = true;
let recorder = null;
let recorderStream = null;
let recorderChunks = [];
let discardRecording = false;
let cameraStream = null;

for (const source of [...Object.values(portraits), ...Object.values(fullbody)]) {
  const image = new Image();
  image.decoding = "async";
  image.src = source;
}

function friendlyError(error) {
  const code = String(error?.code || error?.message || "request_failed");
  return errorMessages[code] || code.replaceAll("_", " ");
}

function formStatus(node, message = "", tone = "") {
  node.textContent = message;
  node.classList.toggle("error", tone === "error");
  node.classList.toggle("success", tone === "success");
}

function setPortrait(name) {
  const source = portraits[name] || portraits.ready;
  if (source === currentPortrait && portraitLayers[activePortrait].classList.contains("active")) return;
  const nextLayer = 1 - activePortrait;
  portraitLayers[nextLayer].src = source;
  portraitLayers[nextLayer].classList.add("active");
  portraitLayers[activePortrait].classList.remove("active");
  activePortrait = nextLayer;
  currentPortrait = source;
}

function scheduleIdlePresence() {
  clearTimeout(idleTimer);
  if (currentState !== "ready" || document.hidden || !authenticated) return;
  const sequence = ["ready", "curious", "blink", "amused", "ready", "blink"];
  idleTimer = window.setTimeout(() => {
    if (currentState !== "ready") return;
    idleStep = (idleStep + 1) % sequence.length;
    setPortrait(sequence[idleStep]);
    scheduleIdlePresence();
  }, reducedMotion ? 30000 : 8500);
}

function setState(state, label = "") {
  const normalized = stateCopy[state] ? state : "ready";
  const copy = stateCopy[normalized];
  currentState = normalized;
  document.body.dataset.state = normalized;
  statusNode.textContent = label || copy.status;
  $("#presence-line").textContent = copy.presence;
  $("#mind-state").textContent = copy.mind;
  $("#channel-state").textContent = copy.channel;
  $("#voice-state").textContent = speechEnabled ? "enabled" : "muted";
  setPortrait(normalized);
  fullbodyAvatar.src =
    normalized === "thinking" ? fullbody.thinking :
    normalized === "ready" ? fullbody.ready :
    fullbody.default;
  window.dispatchEvent(new CustomEvent("seven-state", { detail: { state: normalized } }));
  scheduleIdlePresence();
}

function addLine(kind, text, id = "") {
  const value = String(text || "").trim();
  if (!value || (id && renderedMessages.has(id))) return;
  if (id) renderedMessages.add(id);
  const item = document.createElement("li");
  item.className = kind;
  if (id) item.dataset.messageId = id;
  item.textContent = value;
  conversation.append(item);
  item.scrollIntoView({
    block: "end",
    behavior: reducedMotion ? "auto" : "smooth",
  });
}

function chooseVoice() {
  if (!("speechSynthesis" in window)) return null;
  const voices = window.speechSynthesis.getVoices();
  const preferred = [
    /Microsoft Aria/i,
    /Microsoft Zira/i,
    /Samantha/i,
    /Google UK English Female/i,
  ];
  for (const pattern of preferred) {
    const match = voices.find((voice) => pattern.test(voice.name));
    if (match) return match;
  }
  return voices.find((voice) => /^en[-_]/i.test(voice.lang)) || voices[0] || null;
}

function speak(text) {
  if (!speechEnabled || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(String(text).slice(0, 4000));
  const voice = chooseVoice();
  if (voice) utterance.voice = voice;
  utterance.rate = 0.96;
  utterance.pitch = 1.02;
  utterance.onstart = () => setState("speaking");
  utterance.onend = () => setState(pendingTurns.size ? "thinking" : "ready");
  utterance.onerror = () => setState(pendingTurns.size ? "thinking" : "ready");
  window.speechSynthesis.speak(utterance);
}

function greetSeven(allowSpeech = false) {
  if (greetingShown) return;
  greetingShown = true;
  const greeting = "Hi. I’m Seven. I’ve been waiting to meet you.";
  addLine("seven", greeting, "seven-owner-greeting");
  if (allowSpeech) speak(greeting);
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  let body;
  if (contentType.includes("application/json")) {
    body = await response.json();
  } else {
    body = { error: (await response.text()).trim() || `request_${response.status}` };
  }
  if (!response.ok) {
    const error = new Error(body.error || "request_failed");
    error.code = body.error || "request_failed";
    error.status = response.status;
    throw error;
  }
  return body;
}

async function api(path, options = {}) {
  const url = new URL(path, window.location.href);
  if (url.origin !== window.location.origin) throw new Error("cross_origin_refused");
  const headers = new Headers(options.headers || {});
  if (csrf && options.method && options.method !== "GET") {
    headers.set("X-CSRF-Token", csrf);
  }
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "same-origin",
    cache: "no-store",
  });
  if (response.status === 401 && path !== "api/login" && path !== "api/session") {
    lockInterface(false);
  }
  return parseResponse(response);
}

function showChat({ speakGreeting = false } = {}) {
  authenticated = true;
  loginPanel.classList.add("hidden");
  chatPanel.classList.remove("hidden");
  formStatus(loginError);
  setState("ready");
  connectEvents();
  greetSeven(speakGreeting);
  requestAnimationFrame(() => messageBox.focus());
}

async function unlock(password) {
  setState("connecting", "authenticating");
  const body = await api("api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  csrf = body.csrf;
  showChat({ speakGreeting: true });
}

async function resume() {
  setState("connecting", "checking session");
  try {
    const body = await api("api/session");
    csrf = body.csrf;
    showChat({ speakGreeting: false });
  } catch (error) {
    authenticated = false;
    loginPanel.classList.remove("hidden");
    chatPanel.classList.add("hidden");
    setState("disconnected");
    if (error.status && error.status !== 401) {
      formStatus(loginError, "The private gateway is not available yet.", "error");
    }
  }
}

function clearTurnTracking() {
  for (const timer of pollTimers.values()) clearTimeout(timer);
  pollTimers.clear();
  pendingTurns.clear();
  fetchingTurns.clear();
}

function disconnectEvents() {
  events?.close();
  events = null;
  clearTimeout(reconnectTimer);
}

function scheduleReconnect() {
  clearTimeout(reconnectTimer);
  if (!authenticated || document.hidden) return;
  reconnectAttempts += 1;
  const delay = Math.min(30000, 900 * (2 ** Math.min(reconnectAttempts, 5)));
  setState(pendingTurns.size ? "thinking" : "connecting", `reconnecting in ${Math.ceil(delay / 1000)}s`);
  reconnectTimer = window.setTimeout(connectEvents, delay);
}

function connectEvents() {
  disconnectEvents();
  if (!authenticated || document.hidden) return;
  events = new EventSource(new URL("api/events", window.location.href));
  events.onopen = () => {
    reconnectAttempts = 0;
    setState(pendingTurns.size ? "thinking" : "ready");
  };
  events.addEventListener("turn_status", (event) => {
    try {
      const value = JSON.parse(event.data);
      const payload = value.payload || {};
      const turnId = Number(payload.turn_id);
      if (!Number.isInteger(turnId) || !pendingTurns.has(turnId)) return;
      if (payload.status === "queued" || payload.status === "running") {
        setState("thinking");
      } else if (payload.status === "complete" || payload.status === "failed" || payload.status === "rejected") {
        fetchTurn(turnId);
      }
    } catch {
      formStatus(chatStatus, "The gateway sent an unreadable status update.", "error");
    }
  });
  events.onerror = () => {
    // The gateway intentionally closes each SSE response after a bounded
    // hold. Native EventSource reconnects with Last-Event-ID, so a transient
    // close is normal and must not flash an error or replay the full history.
    if (events?.readyState === EventSource.CLOSED) {
      events = null;
      scheduleReconnect();
    }
  };
}

async function fetchTurn(turnId) {
  if (!pendingTurns.has(turnId) || fetchingTurns.has(turnId)) return;
  fetchingTurns.add(turnId);
  try {
    const body = await api(`api/turn?id=${encodeURIComponent(turnId)}`);
    const turn = body.turn || {};
    if (turn.status === "complete") {
      pendingTurns.delete(turnId);
      clearTimeout(pollTimers.get(turnId));
      pollTimers.delete(turnId);
      const reply = String(turn.reply || "").trim();
      if (reply) {
        addLine("seven", reply, `turn-${turnId}`);
        formStatus(chatStatus, "Seven replied through the private channel.", "success");
        speak(reply);
      } else {
        addLine("system", "Seven completed the turn without a text reply.", `turn-empty-${turnId}`);
        setState(pendingTurns.size ? "thinking" : "ready");
      }
      return;
    }
    if (turn.status === "failed" || turn.status === "rejected") {
      pendingTurns.delete(turnId);
      clearTimeout(pollTimers.get(turnId));
      pollTimers.delete(turnId);
      const error = new Error(turn.error_code || "seven_internal_failure");
      error.code = turn.error_code || "seven_internal_failure";
      throw error;
    }
  } catch (error) {
    pendingTurns.delete(turnId);
    clearTimeout(pollTimers.get(turnId));
    pollTimers.delete(turnId);
    const message = friendlyError(error);
    addLine("system", message, `turn-error-${turnId}`);
    formStatus(chatStatus, message, "error");
    setState("error");
  } finally {
    fetchingTurns.delete(turnId);
  }
}

function pollTurn(turnId, attempt = 0) {
  if (!pendingTurns.has(turnId)) return;
  const delay = Math.min(2500, 400 + attempt * 140);
  const timer = window.setTimeout(async () => {
    await fetchTurn(turnId);
    if (pendingTurns.has(turnId)) pollTurn(turnId, attempt + 1);
  }, delay);
  pollTimers.set(turnId, timer);
}

async function sendMessage(message) {
  addLine("owner", message);
  setState("thinking");
  formStatus(chatStatus, "Your message reached Seven.");
  try {
    const body = await api("api/turn", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const turnId = Number(body.turn_id);
    if (!Number.isInteger(turnId) || turnId < 1) throw new Error("invalid_turn_id");
    pendingTurns.add(turnId);
    pollTurn(turnId);
  } catch (error) {
    const messageText = friendlyError(error);
    addLine("system", messageText);
    formStatus(chatStatus, messageText, "error");
    setState("error");
  }
}

function stopRecorderStream() {
  recorderStream?.getTracks().forEach((track) => track.stop());
  recorderStream = null;
  $("#record").classList.remove("recording");
  $("#record").textContent = "Hold to speak";
}

async function uploadRecording(blob) {
  setState("thinking", "transcribing");
  try {
    const body = await api("api/media/audio", {
      method: "POST",
      headers: { "Content-Type": blob.type || "audio/webm" },
      body: blob,
    });
    messageBox.value = body.transcript || "";
    messageBox.focus();
    formStatus(chatStatus, "Transcription is ready to review. Press Send when you choose.", "success");
    setState("ready");
  } catch (error) {
    const message = `Audio could not be transcribed: ${friendlyError(error)}`;
    formStatus(chatStatus, message, "error");
    setState("error");
  }
}

async function startRecording(event) {
  if (!authenticated || recorder || (Number.isInteger(event.button) && event.button > 0)) return;
  event.preventDefault();
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    formStatus(chatStatus, "This browser does not support microphone capture.", "error");
    return;
  }
  try {
    recorderStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    recorderChunks = [];
    discardRecording = false;
    recorder = new MediaRecorder(recorderStream);
    recorder.ondataavailable = (chunk) => {
      if (chunk.data.size) recorderChunks.push(chunk.data);
    };
    recorder.onstop = () => {
      const blob = new Blob(recorderChunks, { type: recorder.mimeType || "audio/webm" });
      const discard = discardRecording;
      recorder = null;
      recorderChunks = [];
      discardRecording = false;
      stopRecorderStream();
      if (!discard && blob.size) uploadRecording(blob);
    };
    recorder.start();
    $("#record").classList.add("recording");
    $("#record").textContent = "Release to transcribe";
    setState("listening");
    if (event.pointerId !== undefined) event.currentTarget.setPointerCapture?.(event.pointerId);
  } catch (error) {
    stopRecorderStream();
    formStatus(chatStatus, `Microphone unavailable: ${friendlyError(error)}`, "error");
    setState("error");
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
    formStatus(chatStatus, "This browser does not support camera capture.", "error");
    return;
  }
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user" },
      audio: false,
    });
    $("#camera-preview").srcObject = cameraStream;
    $("#camera-panel").classList.remove("hidden");
    $("#camera").textContent = "Camera active";
    setState("listening", "camera preview");
  } catch (error) {
    formStatus(chatStatus, `Camera unavailable: ${friendlyError(error)}`, "error");
    setState("error");
  }
}

function stopCamera() {
  cameraStream?.getTracks().forEach((track) => track.stop());
  cameraStream = null;
  const preview = $("#camera-preview");
  preview.pause();
  preview.srcObject = null;
  $("#camera-panel").classList.add("hidden");
  $("#camera").textContent = "Let Seven see";
  if (authenticated) setState(pendingTurns.size ? "thinking" : "ready");
}

async function sendSnapshot() {
  const preview = $("#camera-preview");
  if (!cameraStream || !preview.videoWidth) {
    formStatus(chatStatus, "Wait for the preview before sending one snapshot.", "error");
    return;
  }
  const canvas = document.createElement("canvas");
  canvas.width = Math.min(preview.videoWidth, 1280);
  canvas.height = Math.round(canvas.width * preview.videoHeight / preview.videoWidth);
  canvas.getContext("2d", { alpha: false }).drawImage(preview, 0, 0, canvas.width, canvas.height);
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.86));
  stopCamera();
  if (!blob) return;
  setState("thinking", "analyzing image");
  try {
    const body = await api("api/media/jpeg", {
      method: "POST",
      headers: { "Content-Type": "image/jpeg" },
      body: blob,
    });
    const reply = body.reply || "I could not describe that snapshot.";
    addLine("seven", reply);
    formStatus(chatStatus, "Seven analyzed the snapshot. Camera access has stopped.", "success");
    speak(reply);
  } catch (error) {
    formStatus(chatStatus, `Snapshot failed: ${friendlyError(error)}`, "error");
    setState("error");
  }
}

function stopAllMedia() {
  if (recorder?.state === "recording") {
    discardRecording = true;
    recorder.stop();
  } else {
    stopRecorderStream();
  }
  if (cameraStream) stopCamera();
  window.speechSynthesis?.cancel();
}

function lockInterface(clearGreeting = true) {
  authenticated = false;
  csrf = "";
  disconnectEvents();
  clearTurnTracking();
  stopAllMedia();
  chatPanel.classList.add("hidden");
  loginPanel.classList.remove("hidden");
  conversation.replaceChildren();
  renderedMessages.clear();
  if (clearGreeting) greetingShown = false;
  setState("disconnected");
}

$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  formStatus(loginError);
  const password = $("#password").value;
  try {
    await unlock(password);
    $("#password").value = "";
  } catch (error) {
    $("#password").value = "";
    formStatus(loginError, friendlyError(error), "error");
    setState("error", "authentication failed");
  }
});

$("#chat-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const message = messageBox.value.trim();
  if (!message || !authenticated) return;
  messageBox.value = "";
  sendMessage(message);
});

messageBox.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    $("#chat-form").requestSubmit();
  }
});

$("#logout").addEventListener("click", async () => {
  try {
    await api("api/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
  } catch {
    // Local lock still occurs if the server-side logout cannot be confirmed.
  }
  lockInterface();
});

$("#voice").addEventListener("click", (event) => {
  speechEnabled = !speechEnabled;
  event.currentTarget.setAttribute("aria-pressed", String(speechEnabled));
  event.currentTarget.textContent = speechEnabled ? "Voice on" : "Voice muted";
  $("#voice-state").textContent = speechEnabled ? "enabled" : "muted";
  if (!speechEnabled) {
    window.speechSynthesis?.cancel();
    setState(pendingTurns.size ? "thinking" : "ready");
  }
});

$("#record").addEventListener("pointerdown", startRecording);
$("#record").addEventListener("pointerup", stopRecording);
$("#record").addEventListener("pointercancel", stopRecording);
$("#record").addEventListener("lostpointercapture", stopRecording);
$("#record").addEventListener("keydown", (event) => {
  if ((event.key === " " || event.key === "Enter") && !event.repeat) startRecording(event);
});
$("#record").addEventListener("keyup", (event) => {
  if (event.key === " " || event.key === "Enter") stopRecording(event);
});
$("#camera").addEventListener("click", enableCamera);
$("#camera-stop").addEventListener("click", stopCamera);
$("#camera-send").addEventListener("click", sendSnapshot);

document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    disconnectEvents();
    stopAllMedia();
  } else if (authenticated) {
    connectEvents();
    setState(pendingTurns.size ? "thinking" : "ready");
  }
});

window.addEventListener("pagehide", () => {
  disconnectEvents();
  stopAllMedia();
});

setState("disconnected");
resume();
