const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const root = path.resolve(__dirname, "..");
const read = (file) => fs.readFileSync(path.join(root, file), "utf8");
const html = read("index.html");
const css = read("css/seven-home.css");
const home = read("js/seven-home.js");
const avatar = read("js/seven-avatar.js");

test("Seven is added without replacing the existing 3D application", () => {
  assert.match(html, /id="world"/);
  assert.match(html, /js\/app\.js\?v=3\.6\.0/);
  assert.match(html, /id="seven-home-button"/);
  assert.match(html, /id="seven-home"[^>]+aria-modal="true"/);
  assert.match(html, /css\/seven-home\.css\?v=1\.0\.0/);
  assert.match(html, /js\/seven-home\.js\?v=1\.0\.0/);
});

test("the browser talks only to the same-origin gateway with session CSRF", () => {
  assert.match(home, /const API_BASE = "\/3dwebsite\/seven-api"/);
  assert.match(home, /url\.origin !== window\.location\.origin/);
  assert.match(home, /credentials: "same-origin"/);
  assert.match(home, /X-CSRF-Token/);
  assert.match(home, /\/api\/session/);
  assert.match(home, /\/api\/login/);
  assert.match(home, /\/api\/logout/);
  assert.doesNotMatch(home, /Authorization|Bearer|localStorage|sessionStorage/);
});

test("an expected unauthenticated session is not reported as a gateway outage", () => {
  const refresh = home.slice(home.indexOf("async function refreshSession"), home.indexOf("function appendMessage"));
  assert.match(refresh, /error\.status === 401/);
  assert.match(refresh, /Authentication required/);
  assert.match(refresh, /Gateway unavailable/);
});

test("text is canonical and SSE reconnects without injecting HTML", () => {
  assert.match(home, /\/api\/turn/);
  assert.match(home, /pendingTurns/);
  assert.match(home, /pollTurn/);
  assert.match(home, /turn_status/);
  assert.match(home, /new EventSource/);
  assert.match(home, /scheduleReconnect/);
  assert.match(home, /Math\.min\(30000/);
  assert.match(home, /body\.textContent = String\(text\)/);
  assert.doesNotMatch(home, /innerHTML/);
});

test("microphone capture is explicit push-to-record and stops its tracks", () => {
  assert.match(home, /MediaRecorder/);
  assert.match(home, /pointerdown/);
  assert.match(home, /pointerup/);
  assert.match(home, /Release to validate/);
  assert.match(home, /recorderStream\?\.getTracks\(\)\.forEach\(\(track\) => track\.stop\(\)\)/);
  assert.match(home, /Local transcription is ready to review\. Press Send/);
  assert.match(home, /discardRecording = true/);
});

test("camera has local preview and separate send, then stops", () => {
  assert.match(html, /id="seven-camera-preview"/);
  assert.match(html, /id="seven-camera-send"/);
  assert.match(html, /id="seven-camera-stop"/);
  assert.match(home, /getUserMedia\(\{ video:/);
  const capture = home.slice(home.indexOf("async function sendSnapshot"), home.indexOf("function stopAllMedia"));
  assert.ok(capture.indexOf("stopCamera();") < capture.indexOf('apiFetch("/api/media/jpeg"'));
  assert.match(capture, /Seven analyzed the snapshot/);
  assert.match(home, /cameraStream\?\.getTracks\(\)\.forEach\(\(track\) => track\.stop\(\)\)/);
});

test("speech is muted by default and avatar reflects runtime state", () => {
  assert.match(html, /id="seven-voice-toggle"[^>]+aria-pressed="false">Voice muted/);
  assert.match(home, /speechEnabled = false/);
  assert.match(home, /speechSynthesis/);
  assert.match(avatar, /import \* as THREE from "three"/);
  for (const state of ["connected", "thinking", "listening", "speaking", "error"]) {
    assert.match(avatar, new RegExp(`${state}:`));
    assert.match(css, new RegExp(`data-state="${state}"`));
  }
});

test("the overlay contains labels and shields existing world controls", () => {
  for (const id of ["seven-login", "seven-username", "seven-passphrase", "seven-messages", "seven-input", "seven-record", "seven-camera-enable"]) {
    assert.match(html, new RegExp(`id="${id}"`));
  }
  assert.match(css, /body\.seven-open>\.topbar/);
  assert.match(home, /event\.stopPropagation\(\)/);
  assert.match(home, /stopAllMedia/);
});
