# Seven Peanut gateway

This directory is the production boundary between an owner's browser and
Seven's loopback-only API.  The browser never receives `SEVEN_INTERNAL_TOKEN`
and cannot call tools directly.  Text turns enter a bounded queue, a single
worker calls Seven over `127.0.0.1`, and the browser receives sanitized status
events over server-sent events (SSE).

## Security model

- Apache terminates HTTPS and proxies the standalone `/seven/` console plus the
  Three.js site's `/3dwebsite/seven-api/` route to `127.0.0.1:8788`.
- The gateway and Seven core run as different unprivileged users.
- Owner passwords are hashed and verified with Argon2id when `argon2-cffi` is
  installed.  The bundled setup command falls back to Python's memory-hard
  `scrypt` and never stores a plaintext password.
- Sessions are server-side.  The browser only receives a random opaque
  `Secure; HttpOnly; SameSite=Strict; Path=/` cookie.
- Every state-changing request requires the session's CSRF token and an exact
  HTTPS `Origin` match.
- Text, request body, queue, media, login, and request rates are bounded.
- JPEG/audio endpoints validate format and size and never retain uploads.
  Authenticated snapshots are analyzed by Seven's configured local Ollama
  vision model; audio is transcribed by a local CPU-only Faster Whisper model.
  Both operations are bounded and serialized at their model boundary. Text
  remains the canonical interaction path.
- Activity and SSE payloads are allow-listed metadata.  Prompts, replies,
  cookies, passwords, internal tokens, and upstream error bodies are excluded.

## Install outline

1. Create the `seven` and `seven-web` system users and install the repository
   under `/opt/seven`.
2. Create separate virtual environments for core and gateway.
   Pre-download the configured Faster Whisper model into
   `/var/lib/seven-web/models`; runtime networking is restricted to loopback.
3. Copy `env/*.example` to `/etc/seven/*.env`, generate independent secrets,
   and set mode `0600`.
4. Generate the owner password hash interactively:

   `python -m seven_gateway.hash_password`

5. Install the unit templates and Apache configuration, then enable
   `seven-core.service` and `seven-web.service`.
6. Validate locally before enabling the public proxy:

   `curl --fail http://127.0.0.1:8765/health`

   `curl --fail http://127.0.0.1:8788/health`

The examples contain no working credentials.  Never reuse the public session
secret as Seven's internal API token.

## Three.js owner home

`threejs-overlay/` is the versioned deployment copy for the existing
`/3dwebsite/` experience. It adds Seven as an overlay without replacing the
site's existing worlds or controls. The overlay uses only the same-origin
`/3dwebsite/seven-api/api/*` gateway and contains no bearer token, password,
or persistent browser storage.

The browser asks separately for microphone and camera permission. Microphone
audio is transcribed locally and placed in the composer for owner review; it
is not sent to Seven until the owner presses Send. A camera snapshot is
analyzed only after the owner presses Send snapshot, then browser camera
tracks are stopped. Seven's spoken reply uses browser speech synthesis and is
muted by default.

## Legacy history

`scripts/import_legacy_messages.py` imports exactly 74 messages by default.
They are inserted only into `messages` and `events`, with
`source=legacy_history` and a source hash.  They are not converted to facts,
beliefs, goals, or memories.  The operation is idempotent by source hash and
backs up the target database before its first write.

Run a dry check first:

`python scripts/import_legacy_messages.py SOURCE TARGET_DB --dry-run`

Then apply:

`python scripts/import_legacy_messages.py SOURCE TARGET_DB --apply`

## Tests

From this directory:

`python -m pytest tests -q`
