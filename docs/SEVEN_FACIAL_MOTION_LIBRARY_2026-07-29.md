# Seven facial motion library

Date: 2026-07-29

## Intent

Seven's owner page now has an aligned 2D facial-motion system. It does not
pretend that independent generated portraits are continuous animation.
Instead, it derives every speech frame from one stable video take of the same
face, pose, outfit, lighting, and camera position.

## Preserved before-state

- Repository HEAD before this change:
  `ddc7241215eca481365d92b5ad2fee29698471f7`.
- Pre-existing owner edits in `deploy/peanut/README.md` and
  `docs/COMPLETION_LEDGER.md` were inspected and left untouched.
- The public `/seven/` static files were content-equivalent to the checked-in
  static tree before this change; six text files differed only by CRLF line
  endings and all 13 portrait assets matched byte-for-byte.

## Source evidence

The source media remains in the owner's Downloads folder and was not moved,
renamed, deleted, or overwritten.

| Source | Bytes | SHA-256 |
|---|---:|---|
| `Normal speaking loop.mp4` | 3,254,092 | `88B13D7E02A5D8316374A2A052AC3C926DE511A9953B95CC6397B929A6AE42A7` |
| `Amused.mp4` | 3,732,331 | `925B17F712B92D5B609F87F0BBBC786C6FA0C164CACAA42007B868DBD28F0622` |
| `Seven_Controlled_Anger_Tactical_01.mp4` | 1,664,680 | `A65F1828032393713C99591DCF88EB30561C18F1ED3624C970D008420BED77AF` |

## Implemented motion

- Ten aligned WebP states: rest, M/B/P, A, E/I, O, U/W, F/V,
  L/T/D/N/R, CH/SH/TH, and blink.
- Deterministic text-to-viseme sequencing. The same text produces the same
  frame sequence.
- Browser speech boundary events resynchronize the frame cursor while a
  92 ms animation clock provides continuous movement between boundary events.
- Speech start, end, error, cancellation, and ready-state transitions cleanly
  own and release the animation timer.
- The existing static speaking portrait remains the reduced-motion fallback.
- Muted local smile and controlled-anger films render as smooth portrait
  overlays, then return to the still portrait stack.
- Expression-film selection is deliberately conservative and visual only. It
  does not claim that a keyword classifier is Seven's emotional mind.
- The owner greeting explicitly uses the smile film. Strong positive or angry
  wording can select the corresponding visual film after speech.

## Privacy and delivery

- All speech frames and emotion films are self-hosted under
  `deploy/peanut/static/assets/`.
- No third-party runtime image, animation, speech, or CDN request was added.
- The browser voice control remains muted by default and owner-controlled.
- Camera and microphone consent behavior is unchanged.

## Local validation

- `node --check deploy/peanut/static/seven.js`: passed.
- Executable browser-client contract: 6 passed, 0 failed.
- Focused static owner-experience suite: 4 passed.
- Complete repository suite: exit code 0; two existing expected skips.
- `python -m seven --status`: exit code 0; Seven Real 4.4.4 initialized with
  100 active tool schemas.
- Real local browser preview loaded `seven.css?v=2.1.0`,
  `seven-scene.js?v=2.1.0`, and `seven.js?v=2.1.0`, rendered the portrait
  stack, found the expression-film layer, and produced no browser console
  warnings or errors.

## Honest proof boundary

The code, media, deterministic frame mapping, automated browser contract, and
local visual render are verified.

## Peanut deployment proof

- Source commit: `4dd925302b3a9d09d4a6e4e2b4e39a0ea39ca196`.
- Commit pushed to `origin/codex/seven-completion`.
- Exact static archive:
  - bytes: `2,723,499`;
  - SHA-256:
    `92935A73EA426D5860993009EA7DDC11497EE189D5A8DFDD9BA4457F23DFC7A1`;
  - tracked static files: `31`.
- Before release: `/opt/seven-conversation-20260729T120417Z`.
- Active release after switch: `/opt/seven-facial-20260729-4dd9253`.
- The previous immutable release remains the rollback target.
- `seven-core.service` remained PID `2424332`, active/running, zero restarts.
- `seven-ollama.service` remained PID `2416096`, active/running, zero restarts.
- Only `seven-web.service` was restarted; it became PID `2467170`,
  active/running, zero restarts.
- Loopback gateway health returned:
  `{"ok":true,"service":"seven-web","version":"1.0.0"}`.
- Public `https://jvrsoftware.co.za/seven/` returned HTTP 200 and loaded the
  `2.1.0` CSS and JavaScript with no browser console warnings or errors.
- Public byte/hash comparisons matched the exact Git archive for:
  `index.html`, `seven.css`, `seven.js`, A and rest visemes, smile film, and
  controlled-anger film.
- The smile response is served as `video/mp4`; the full public body is
  432,075 bytes and matches SHA-256
  `E155F8CED45CCA58B3702EEE6EAD44B77A0FEB19E7DFF27908F487E3EF135C62`.

A final owner-side acceptance check is still needed to judge whether the lip
motion feels natural with the particular voice selected by the owner's
browser. Browser speech APIs expose word/character boundaries, not exact audio
phonemes, so this is aligned approximate lip sync, not studio-grade
audio-driven facial capture.
