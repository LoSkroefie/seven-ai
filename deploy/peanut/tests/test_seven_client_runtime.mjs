import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";

const clientSource = fs.readFileSync(
  new URL("../static/seven.js", import.meta.url),
  "utf8",
);

class StubClassList {
  constructor() {
    this.values = new Set();
  }

  add(value) {
    this.values.add(value);
  }

  remove(value) {
    this.values.delete(value);
  }

  contains(value) {
    return this.values.has(value);
  }

  toggle(value, enabled) {
    if (enabled) this.values.add(value);
    else this.values.delete(value);
  }
}

class StubElement {
  constructor(tag = "div") {
    this.tagName = tag.toUpperCase();
    this.attributes = new Map();
    this.children = [];
    this.classList = new StubClassList();
    this.dataset = {};
    this.textContent = "";
    this.value = "";
    this.src = "";
    this.srcObject = null;
    this.videoWidth = 0;
    this.videoHeight = 0;
  }

  addEventListener() {}
  append(child) { this.children.push(child); }
  focus() {}
  pause() {}
  play() { return Promise.resolve(); }
  replaceChildren() { this.children = []; }
  requestSubmit() {}
  scrollIntoView() {}
  setPointerCapture() {}
  getAttribute(name) { return this.attributes.get(name) || ""; }
  setAttribute(name, value) { this.attributes.set(name, String(value)); }
}

async function createHarness() {
  const nodes = new Map();
  const getNode = (selector) => {
    if (!nodes.has(selector)) nodes.set(selector, new StubElement());
    return nodes.get(selector);
  };
  const document = {
    body: new StubElement("body"),
    hidden: false,
    addEventListener() {},
    createElement(tag) {
      const element = new StubElement(tag);
      if (tag === "canvas") {
        element.getContext = () => ({ drawImage() {} });
        element.toBlob = (callback, type) => callback(new Blob(["jpeg"], { type }));
      }
      return element;
    },
    querySelector: getNode,
  };
  let fetchCalls = 0;
  const fetchArguments = [];
  let audioPlayCount = 0;
  let fetchImpl = async () => ({
    ok: false,
    status: 401,
    headers: new Headers({ "content-type": "application/json" }),
    json: async () => ({ error: "authentication_required" }),
  });
  class StubEventSource {
    static CLOSED = 2;
    constructor() {
      this.readyState = 1;
    }
    addEventListener() {}
    close() { this.readyState = StubEventSource.CLOSED; }
  }
  class StubUtterance {
    constructor(text) {
      this.text = text;
    }
  }
  class StubAudio {
    constructor(src) {
      this.src = src;
    }

    pause() {}

    play() {
      audioPlayCount += 1;
      this.onplay?.();
      this.onended?.();
      return Promise.resolve();
    }
  }
  class StubImage {
    constructor() {
      this.decoding = "";
      this.src = "";
    }
  }
  class StubMediaRecorder {
    static isTypeSupported() { return false; }
  }
  const window = {
    Blob,
    Audio: StubAudio,
    CustomEvent: class {
      constructor(type, options) {
        this.type = type;
        this.detail = options?.detail;
      }
    },
    EventSource: StubEventSource,
    Headers,
    Image: StubImage,
    MediaRecorder: StubMediaRecorder,
    SpeechSynthesisUtterance: StubUtterance,
    URL,
    addEventListener() {},
    clearTimeout,
    dispatchEvent() {},
    location: new URL("https://example.test/seven/"),
    matchMedia: () => ({ matches: true }),
    requestAnimationFrame: (callback) => callback(),
    clearInterval,
    setInterval,
    setTimeout,
    speechSynthesis: {
      cancel() {},
      getVoices: () => [],
      speak(utterance) {
        utterance.onstart?.();
        utterance.onend?.();
      },
    },
  };
  const context = vm.createContext({
    Blob,
    Audio: StubAudio,
    CustomEvent: window.CustomEvent,
    EventSource: StubEventSource,
    Headers,
    Image: StubImage,
    MediaRecorder: StubMediaRecorder,
    SpeechSynthesisUtterance: StubUtterance,
    URL,
    clearTimeout,
    clearInterval,
    console,
    document,
    fetch: async (...args) => {
      fetchCalls += 1;
      fetchArguments.push(args);
      return fetchImpl(...args);
    },
    navigator: { mediaDevices: {} },
    requestAnimationFrame: window.requestAnimationFrame,
    setTimeout,
    setInterval,
    window,
  });
  window.document = document;
  window.fetch = context.fetch;
  window.navigator = context.navigator;
  window.window = window;
  vm.runInContext(clientSource, context, { filename: "seven.js" });
  await new Promise((resolve) => setImmediate(resolve));
  fetchCalls = 0;
  fetchArguments.length = 0;
  return {
    context,
    nodes,
    evaluate: (source) => vm.runInContext(source, context),
    fetchCalls: () => fetchCalls,
    fetchArguments: () => fetchArguments,
    audioPlayCount: () => audioPlayCount,
    setFetch: (implementation) => { fetchImpl = implementation; },
  };
}

test("gateway error codes resolve to owner-facing messages", async () => {
  const harness = await createHarness();
  assert.equal(
    harness.evaluate("friendlyError({code: 'origin_rejected'})"),
    "The gateway refused this browser origin.",
  );
  assert.equal(
    harness.evaluate("friendlyError({code: 'csrf_rejected'})"),
    "The secure session changed. Open the channel again.",
  );
});

test("muted speech settles a completed reply independently of TTS", async () => {
  const harness = await createHarness();
  const result = harness.evaluate(`
    speechEnabled = false;
    pendingTurns.clear();
    setState("thinking");
    const spoken = speak("completed reply");
    ({ spoken, state: currentState, defaultEnabled: SPEECH_DEFAULT_ENABLED });
  `);
  assert.deepEqual(
    JSON.parse(JSON.stringify(result)),
    { spoken: false, state: "ready", defaultEnabled: false },
  );
});

test("enabled speech requests authenticated neural audio before browser fallback", async () => {
  const harness = await createHarness();
  harness.setFetch(async () => ({
    ok: true,
    status: 200,
    headers: new Headers({ "content-type": "audio/mpeg" }),
    blob: async () => new Blob(["ID3-neural-voice"], { type: "audio/mpeg" }),
  }));
  harness.evaluate(`
    authenticated = true;
    csrf = "csrf-for-neural-voice";
    speechEnabled = true;
    speak("Hello from Seven.");
  `);
  await new Promise((resolve) => setImmediate(resolve));
  await new Promise((resolve) => setImmediate(resolve));

  try {
    assert.equal(harness.fetchCalls(), 1);
    const [url, options] = harness.fetchArguments()[0];
    assert.match(String(url), /api\/tts$/);
    assert.equal(options.method, "POST");
    assert.equal(options.headers["X-CSRF-Token"], "csrf-for-neural-voice");
    assert.equal(harness.audioPlayCount(), 1);
    assert.equal(harness.evaluate("currentState"), "ready");
  } finally {
    harness.evaluate(`
      authenticated = false;
      stopAllMedia();
      clearTimeout(idleTimer);
    `);
  }
});

test("speech text maps to deterministic aligned visemes", async () => {
  const harness = await createHarness();
  const result = harness.evaluate(`
    ({
      phonemes: ["m", "a", "e", "o", "u", "f", "l", "sh"].map((value) => visemeAt(value, 0)),
      sequence: buildVisemeSequence("Meet Seven.").map((item) => item.name),
      smile: expressionForText("I am glad to see you."),
      anger: expressionForText("That threat is unacceptable."),
    });
  `);
  assert.deepEqual(
    JSON.parse(JSON.stringify(result)),
    {
      phonemes: ["mbp", "aa", "ee", "oh", "uw", "fv", "l", "ch"],
      sequence: ["rest", "mbp", "ee", "l", "rest", "ch", "ee", "fv", "ee", "l", "rest"],
      smile: "smile",
      anger: "anger",
    },
  );
});

test("recorder negotiation and byte cap are deterministic", async () => {
  const harness = await createHarness();
  const result = harness.evaluate(`
    window.MediaRecorder.isTypeSupported = (type) =>
      type === "audio/ogg;codecs=opus" || type === "audio/mp4";
    recorderBytes = MAX_AUDIO_BYTES - 10;
    ({
      mimeType: chooseRecorderMimeType(),
      withinLimit: recordingWouldExceedLimit(10),
      exceedsLimit: recordingWouldExceedLimit(11),
      maxDuration: MAX_RECORDING_MS,
    });
  `);
  assert.deepEqual(
    JSON.parse(JSON.stringify(result)),
    {
      mimeType: "audio/ogg;codecs=opus",
      withinLimit: false,
      exceedsLimit: true,
      maxDuration: 60_000,
    },
  );
});

test("snapshot dimensions are bounded and invalid input is rejected", async () => {
  const harness = await createHarness();
  const result = harness.evaluate(`
    ({
      landscape: fitSnapshotDimensions(2000, 1000),
      portrait: fitSnapshotDimensions(100, 10000),
      invalid: fitSnapshotDimensions(0, 720),
    });
  `);
  assert.deepEqual(
    JSON.parse(JSON.stringify(result)),
    {
      landscape: { width: 1280, height: 640 },
      portrait: { width: 82, height: 8192 },
      invalid: null,
    },
  );
});

test("concurrent terminal fetches share one request and settle once", async () => {
  const harness = await createHarness();
  harness.setFetch(async () => ({
    ok: true,
    status: 200,
    headers: new Headers({ "content-type": "application/json" }),
    json: async () => ({
      ok: true,
      turn: { id: 42, status: "complete", reply: "One terminal reply." },
    }),
  }));
  const result = await harness.evaluate(`
    (async () => {
      speechEnabled = false;
      pendingTurns.add(42);
      await Promise.all([fetchTurn(42), fetchTurn(42)]);
      await fetchTurn(42);
      return {
        pending: pendingTurns.has(42),
        terminal: terminalTurns.has(42),
        state: currentState,
      };
    })()
  `);
  assert.equal(harness.fetchCalls(), 1);
  assert.deepEqual(
    JSON.parse(JSON.stringify(result)),
    { pending: false, terminal: true, state: "ready" },
  );
});
