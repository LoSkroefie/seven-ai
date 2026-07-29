# Seven neural female voice deployment — 2026-07-29

## Finding

The Peanut owner page did not use Seven's configured neural voice. It called
the browser `speechSynthesis` API and selected the browser's default voice when
its preferred voice list was empty. On the tested client this produced a
robotic system voice. Peanut did not have `edge-tts` installed in Seven's live
runtime.

## Implemented boundary

- The owner page requests authenticated speech from `POST /api/tts`.
- The low-authority web gateway remains loopback-only. It forwards the bounded
  request to Seven core and cannot contact the external speech service itself.
- Seven core exposes authenticated loopback-only `POST /speech` and renders
  `en-US-AvaNeural` with rate `-5%` and pitch `+2Hz`.
- Text is capped at 4,000 characters, generated audio is capped at 4,000,000
  bytes, and generation times out after 30 seconds.
- The browser plays the returned MP3 and retains the existing viseme/expression
  animation. Browser speech remains only as a failure fallback.
- Owner session, origin, CSRF, rate-limit, response-size, and no-store controls
  remain enforced.

## Verification

- Python core/gateway focused tests: 14 passed.
- Browser runtime tests: 7 passed.
- Full repository test suite: passed with two pre-existing skips.
- Immutable live release: `/opt/seven-voice-20260729-ac532c0`.
- Source commits: `e1fdbb5` and the core-boundary correction `ac532c0`.
- Release archive:
  `seven-neural-voice-ac532c0.tar.gz`, 31,388,127 bytes,
  SHA-256
  `cf00585d452f2c2b822065e2ab0a0a91e2b090745ed4592478722d29aaa907a4`.
- Installed core dependency: `edge-tts 7.2.8`.
- Exact live authenticated chain:
  web gateway `/api/tts` -> Seven core `/speech` -> Ava neural MP3.
- Live result: HTTP 200, `audio/mpeg`, 28,656 bytes, SHA-256
  `8f70ed78545975b035df9724d225a6ce69aeb3f65083c51bcc429256da4f5606`.
- Gateway activity record 112 is `speech_generated` with 48 characters and
  28,656 bytes. Core and gateway logs both record HTTP 200.
- Public `/seven/` serves `seven.js?v=2.2.0`; its downloaded SHA-256 matches
  the live file:
  `172d51995ea52d76adf7e9efe1ecb6a64fecdd6c454e2217bf179e613b806a0f`.
- `seven-core`, `seven-web`, and `seven-ollama` were active. Core and web
  restart counts were zero after deployment.
- Gateway database integrity returned `ok`.

## Rollback evidence

Before-state backups:

- `/etc/seven/seven-core.env.before-neural-voice-20260729T182637Z.bak`
  SHA-256
  `e762d9d5dd591fa42759466d9a00b4101de60a63692dde5f9d0dda98d72e5a5b`
- `/etc/seven/seven-web.env.before-neural-voice-20260729T182637Z.bak`
  SHA-256
  `d8a8da2b43bd4667766ee8a92de9f4706c2ba231a0136cbde329b762e0409bd8`
- `/var/lib/seven/seven.db.before-neural-voice-20260729T182637Z.bak`
  SHA-256
  `920bc339192bc28dde3f2f058febf028b182e730bbee71a1217daa5a0f7abca0`
- `/var/lib/seven-web/gateway.sqlite3.before-neural-voice-20260729T182637Z.bak`
  SHA-256
  `af754cfcf9cc4474dec9fc9ec9350f70914021b969c838f048379ccc221776cc`

## Privacy and remaining limitation

`edge-tts` uses Microsoft's online neural speech service, so the text being
spoken leaves Peanut for synthesis. It does not require a paid API key. A
future fully local voice can replace this adapter, but it has not been claimed
or deployed here.
