# Local music playback

Seven can play user-owned local audio through an independently owned playback process. The five tools are `music_status`, `play_local_audio`, `pause_local_audio`, `resume_local_audio`, and `stop_local_audio`.

Supported filename extensions are MP3, WAV, OGG, FLAC, M4A, and Opus. Actual codec support comes from the selected backend and a failed codec load is reported as `error` or `failed`, never “now playing.”

## Backends

1. `pygame-worker` is preferred when the voice extra is installed. A separate Python process owns its mixer and acknowledges playing, pause, resume, stop, natural finish, and errors through local runtime state.
2. `ffplay` is a core-install fallback when it is on `PATH`. Seven verifies that the process remains alive after launch and can stop its owned process tree. Pause/resume explicitly report unsupported because ffplay has no reliable noninteractive acknowledgement channel.

Install the full-control backend with:

```bash
pip install "seven-ai[music]"
```

State files live under `SEVEN_DATA_DIR/runtime/music`. They contain only playback state, PID, error preview, and the selected local path. Seven stops its player on normal interpreter exit. After an abnormal crash, the next runtime reclaims a surviving worker only when both its command line and exact control-file path prove ownership. Seven never kills an unrelated media player.

## Deliberate scope and truthful limits

- This surface does not search YouTube, download copyrighted media, or claim that opening a web page is playback.
- It does not manage playlists, media libraries, streaming accounts, DRM, or OS-wide media sessions.
- Playing and text-to-speech simultaneously can still produce overlapping audio because they are distinct output processes.
- A successful start proves backend acknowledgement/process survival, not that speakers are connected, audible, or set to a suitable volume.
- Codec/device support needs runtime evidence on each target machine.

## Legacy disposition

The v3 player coupled YouTube search, downloading, FFmpeg conversion, shared-process pygame playback, cache retention, and browser fallback. Browser fallback was returned as success even though Seven had not played audio. The current recovery keeps local playback real and owned. Online discovery and legally permitted acquisition require a separate provider contract and are not smuggled into the playback result.
