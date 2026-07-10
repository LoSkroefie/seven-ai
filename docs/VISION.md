# Seven Real — Vision & presence (8GB VRAM)

## Models

| Role | Default | Size (approx) |
|---|---|---|
| Text / tools | `llama3.2` | ~2 GB |
| Vision | `llama3.2-vision` | ~7.8 GB |

On an **8GB** card you generally **cannot** keep both fully resident. Seven:

1. Downscales screenshots/images to max edge **1280px**
2. Uses vision model `keep_alive=2m` so VRAM frees after analysis
3. Text model reloads on next chat (cold ~30–60s possible)

```bat
ollama pull llama3.2
ollama pull llama3.2-vision
```

## Tools

| Tool | Needs LLM vision? | Notes |
|---|---|---|
| `list_cameras` | No | Probe indices |
| `capture_webcam` | No | Save JPEG |
| `check_presence` | No | OpenCV Haar faces — fast “is someone there?” |
| `screenshot` / `screen_size` | No | Capture only |
| `analyze_image` | Yes | Any image path |
| `see_screen` | Yes | Screenshot + analyze |
| `see_webcam` | Yes | Capture + analyze |

## VRAM procedure (recommended)

**Before a vision task:**

```bat
ollama ps
REM if text model loaded and vision fails/timeouts:
ollama stop llama3.2
```

**Run vision once:**

```bat
python -m seven -c "Use see_screen and describe the main window on my desktop."
```

**After vision**, next text chat may reload `llama3.2` (slow first reply is normal).

Optional env:

| Var | Default | Meaning |
|---|---|---|
| `OLLAMA_VISION_MODEL` | `llama3.2-vision` | Vision model name |
| `SEVEN_VISION_MAX_EDGE` | `1280` | Max image dimension |
| `SEVEN_VISION_JPEG_QUALITY` | `75` | JPEG quality |
| `SEVEN_VISION_KEEP_ALIVE` | `2m` | How long vision stays in VRAM |
| `SEVEN_CAMERA_INDEX` | `0` | Webcam index |
| `SEVEN_LLM_TIMEOUT` | `300` | Seconds (vision first load can be long) |

## Smoke tests

```bat
REM local capture (no LLM)
python -c "from seven.tools.vision import list_cameras, capture_webcam; print(list_cameras()); print(capture_webcam())"

REM presence (no LLM)
python -c "from seven.tools.vision import check_presence; print(check_presence())"

REM screen + vision model (needs Ollama + vision model)
python -m seven -c "Call see_screen with a short prompt about what app is focused."
```

## Presence vs OpenSeeFace

- **Now:** `check_presence` uses OpenCV Haar cascades (faces yes/no + boxes).
- **Later:** OpenSeeFace can add landmarks / head pose / attention; not required for basic “are you there?”.

## Privacy

- Screenshots and webcam frames land in `%USERPROFILE%\.seven\` (`vision_screen.jpg`, `webcam.jpg`, …).
- Nothing is uploaded except if you switch LLM provider to cloud.
