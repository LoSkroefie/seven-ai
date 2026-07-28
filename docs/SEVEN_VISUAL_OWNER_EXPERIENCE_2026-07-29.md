# Seven visual owner experience — verified deployment

Date: 2026-07-29  
Public route: `https://jvrsoftware.co.za/seven/`  
UI source commit: `d566dded3eaa39b07626e8e066a751d533a46e66`  
Active Peanut release: `/opt/seven-ui-20260729-eebc96882589`  
Rollback release: `/opt/seven-1456c01`

## Outcome

The bare fallback console was replaced with a responsive, state-reactive owner
experience that keeps the existing secure Seven gateway.

The deployed interface includes:

- Seven's canonical Vuka identity rather than a geometric stand-in.
- Ten facial states: ready, welcoming, listening, thinking, speaking, amused,
  concerned, blink, determined, and curious.
- Three full-body states: idle, welcome, and thinking.
- A self-hosted Three.js particle and orbital scene. No runtime CDN is used and
  the production content-security policy was not weakened.
- Live visual states for disconnected, connecting, ready, listening, thinking,
  speaking, and error.
- Immediate owner greeting:
  `Hi. I’m Seven. I’ve been waiting to meet you.`
- Text chat, browser speech, press-and-hold microphone transcription, explicit
  camera preview/snapshot analysis, voice toggle, and secure logout controls.
- Deterministic idle expression changes and reduced-motion support.

## Root cause fixed

The old browser client rendered every historical `turn_status` event returned
by the SSE activity stream. Old failed turns therefore appeared as current
failures after login.

The new client records the turn IDs created by the current page session and
only fetches or renders terminal events for those IDs. Polling remains as a
fallback for missed SSE events. Native EventSource reconnect behavior is
preserved so bounded SSE responses do not flash a false reconnect failure.

## Source and local validation

The scoped commit contains 34 changed files:

- `deploy/peanut/static/index.html`
- `deploy/peanut/static/seven.css`
- `deploy/peanut/static/seven.js`
- `deploy/peanut/static/seven-scene.js`
- 13 optimized WebP presence assets
- pinned Three.js `0.169.0` and its license
- 14 canonical/master PNG assets
- `deploy/peanut/tests/test_static_owner_experience.py`

Unrelated pre-existing working-tree edits in `deploy/peanut/README.md` and
`docs/COMPLETION_LEDGER.md` were not staged, overwritten, or included.

Validation evidence:

- `node --check` passed for `seven.js` and `seven-scene.js`.
- Peanut gateway/static focused suite passed: 13 tests.
- Full repository suite completed successfully: 163 collected, 161 passed,
  2 skipped, exit code 0.
- Real-browser local preview proved login, greeting, one complete reply, stable
  ready state, no stale replay after reload, and zero browser console errors.

## Production before-state

Before the switch:

- `/opt/seven -> /opt/seven-1456c01`
- `seven-core.service`: PID `2221252`, restarts `0`
- `seven-web.service`: PID `2196110`, restarts `0`
- `seven-ollama.service`: PID `2219406`, restarts `0`
- all three services were active/running
- gateway health returned `{"ok":true,"service":"seven-web","version":"1.0.0"}`
- the live static tree contained only `index.html`, `seven.css`, `seven.js`,
  and generated `release.json`

The release archive was built from commit `d566dde`:

- archive SHA-256:
  `276cbd5638cd1e4d42c0faa5b7927f06a67f0f98d1b2c40f6b39caebcbd49cdb`
- deployed static manifest SHA-256:
  `eebc96882589c96542722924b8c1963eedd06dec71266bbc64f8e1595390da32`
- deployed source payload: 19 files, 1,592,962 bytes

The first immutable staging attempt rejected the package before any live
switch because its expected hashes described Windows working-tree bytes rather
than the exact Git archive bytes. The rollback gate kept
`/opt/seven-1456c01` active and all service PIDs unchanged. Its failed staging
tree was retained at `/opt/.seven-ui-20260729-0ae4eb07dc18.stage` for evidence.

## Production deployment proof

The corrected deployment:

- cloned the exact active release
- replaced only `deploy/peanut/static`
- preserved the old release as the rollback target
- atomically switched `/opt/seven`
- did not restart Seven core, web gateway, or Ollama
- did not change `/etc/seven`
- did not change the Seven or gateway database identities

After the switch:

- `/opt/seven -> /opt/seven-ui-20260729-eebc96882589`
- all three service PIDs and restart counters were unchanged
- gateway health remained healthy
- all 19 public static source files were downloaded from `/seven/` and matched
  the Git archive byte-for-byte
- the browser loaded the self-hosted Three.js module and all 13 WebP assets
  with HTTP 200 responses
- no browser console errors were recorded

Authenticated public proof:

1. Owner login returned HTTP 200.
2. Seven displayed the immediate greeting.
3. The browser sent:
   `Hi Seven. Please greet your owner in one short sentence and confirm this private channel is working.`
4. The real Peanut Seven model replied:
   `Hi Seven. Your owner is here. Private channel is working.`
5. The interface entered the speaking state.
6. Reload retained the authenticated session, displayed only the greeting, and
   did not replay the prior completed turn.

Server-side immutable evidence is stored at:

`/var/backups/seven/20260728T234135Z-ui-eebc96882589`

## Remaining proof boundary

Text, SSE, authentication, visual-state, static-delivery, and real-model reply
flows are verified live.

Microphone and camera handlers preserve explicit owner consent, stop their
tracks, and passed gateway contract tests. Physical camera/microphone capture
was not triggered while the owner was away, so that device-permission step
still requires one owner-side browser test.
