# Vision System

Seven can see and understand the world through cameras using OpenCV and llama3.2-vision.

---

## Overview

The vision system has three layers:

1. **Camera Interface** — OpenCV captures frames from USB webcams or IP cameras
2. **Image Processing** — Basic frame analysis (motion detection, face detection)
3. **Scene Understanding** — llama3.2-vision describes what it sees in natural language

## How It Works

```
Camera (USB/IP)
  → OpenCV Frame Capture
  → Preprocessing (resize, normalize)
  → llama3.2-vision Analysis
  → Natural Language Description
  → Seven's Emotional Response
```

Seven doesn't just describe what she sees — she *reacts* to it. Seeing a person wave might trigger Joy. A dark empty room might trigger mild Anxiety. This is powered by the Multimodal Emotion Bridge (`core/multimodal_emotion.py`).

## Camera Types

### USB Webcam
```python
# config.py
CAMERA_INDEX = 0  # Default webcam
```

### IP Cameras
Seven includes camera discovery tools:

```bash
# Scan network for cameras
python discover_cameras.py

# Alternative scanner
python find_cameras.py
```

IP cameras are accessed via RTSP or HTTP streams through OpenCV:
```python
# Example: RTSP camera
CAMERA_URL = "rtsp://192.168.1.100:554/stream"
```

## Scene Analysis

When vision is active, Seven periodically captures a frame and sends it to llama3.2-vision for analysis:

```
Seven sees: "A person sitting at a desk with two monitors. There's a coffee mug 
on the left side and some papers scattered around. The room is well-lit with 
natural light from a window behind the desk."
```

This description is injected into Seven's context, giving her awareness of the physical environment.

## Motion Detection

Seven can detect significant motion between frames:
- Alerts when someone enters the camera's field of view
- Tracks movement patterns over time
- Can be used for security monitoring

## Configuration

```python
# config.py
VISION_ENABLED = True
CAMERA_INDEX = 0              # Camera device index
VISION_INTERVAL = 30          # Seconds between analyses
VISION_MOTION_THRESHOLD = 25  # Motion sensitivity
```

## Requirements

- OpenCV (`opencv-python>=4.8.0`)
- NumPy (`numpy>=1.24.0`)
- Ollama with `llama3.2-vision` model pulled
- A camera (USB or IP)

## Important Notes

- Vision uses **OpenCV only** for camera access — no YOLO, no cloud vision APIs
- Scene understanding uses **llama3.2-vision** through local Ollama — no images leave your machine
- Camera access requires user permission on most operating systems
- IP camera discovery scans your local network only
