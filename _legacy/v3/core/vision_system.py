"""
Vision System - Seven's Eyes (On-Demand + Watch Mode)

Two modes:
  look()  — One-shot: open camera, grab frame, analyze, close.
  watch() — Sustained: keep camera open, send snapshots to vision model
            at a configurable interval until stop_watching() is called.

Does NOT touch screen_control.py (separate screenshot-based automation).
"""

import cv2
import base64
import threading
import time
import socket
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
import logging
import numpy as np


class VisionSystem:
    """
    Seven's vision system - on-demand + watch mode.

    On-demand:
        description = vision.look()              # Quick one-shot look
        description = vision.look(prompt="...")   # Look with custom question
        frame_b64 = vision.glance()              # Grab frame without analysis

    Sustained watching:
        vision.watch(interval=45)                # Start watching every 45s
        vision.stop_watching()                   # Stop watching
        vision.is_watching()                     # Check if watching
    """

    def __init__(self, bot, config=None):
        self.bot = bot
        self.logger = logging.getLogger("VisionSystem")

        # Configuration
        config = config or {}
        self.enabled_cameras = config.get('enabled_cameras', ['webcam'])
        self.vision_model = config.get('vision_model', 'llama3.2-vision')
        self.webcam_index = config.get('webcam_index', 0)
        self.ip_cameras = config.get('ip_cameras', [])
        self.motion_sensitivity = config.get('motion_sensitivity', 50)
        self.default_watch_interval = config.get('analysis_interval', 60)

        # State
        self.running = False
        self.current_scenes = {}       # {camera_name: description}
        self.scene_history = []        # List of past observations
        self.last_analysis = {}        # {camera_name: timestamp}
        self._last_frames = {}         # {camera_name: frame} for change detection
        self._look_lock = threading.Lock()

        # Watch mode state
        self._watching = {}            # {camera_name: True/False}
        self._watch_threads = {}       # {camera_name: Thread}
        self._watch_cameras = {}       # {camera_name: cv2.VideoCapture} kept open during watch

    def start(self):
        """Mark vision system as ready (no camera opened yet)."""
        if self.running:
            return
        self.running = True
        self.logger.info("Vision system ready (on-demand + watch mode)")

    def stop(self):
        """Stop vision system and release any open cameras."""
        self.running = False

        # Stop all active watches
        for cam_name in list(self._watching.keys()):
            self.stop_watching(cam_name)

        self._last_frames.clear()
        self.logger.info("Vision system stopped")

    # ── One-Shot: look() ────────────────────────────────────────────

    def look(self, camera_name='webcam', prompt=None) -> Optional[str]:
        """
        One-shot look: open camera, grab frame, analyze with vision model, close.

        Args:
            camera_name: 'webcam' or an IP camera name
            prompt: Custom question about the scene

        Returns:
            Scene description string, or None on failure
        """
        if not self.running:
            return None

        with self._look_lock:
            # If we're already watching this camera, grab from the open camera
            if camera_name in self._watch_cameras and self._watch_cameras[camera_name].isOpened():
                frame = self._read_from_open_camera(camera_name)
            else:
                frame = self._grab_frame(camera_name)

            if frame is None:
                return None

            return self._analyze_frame(camera_name, frame, prompt)

    def glance(self, camera_name='webcam') -> Optional[str]:
        """
        Quick snapshot — grab a frame as base64 JPEG without vision analysis.

        Returns:
            Base64-encoded JPEG string, or None on failure
        """
        if not self.running:
            return None

        if camera_name in self._watch_cameras and self._watch_cameras[camera_name].isOpened():
            frame = self._read_from_open_camera(camera_name)
        else:
            frame = self._grab_frame(camera_name)

        if frame is None:
            return None

        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return base64.b64encode(buffer).decode('utf-8')

    def look_async(self, camera_name='webcam', prompt=None, callback=None):
        """Look in a background thread (non-blocking)."""
        def _do_look():
            result = self.look(camera_name, prompt)
            if callback and result:
                callback(result)

        thread = threading.Thread(target=_do_look, daemon=True, name="VisionSystem-Look")
        thread.start()

    # ── Sustained: watch() / stop_watching() ────────────────────────

    def watch(self, camera_name='webcam', interval=None, prompt=None,
              on_scene=None) -> str:
        """
        Start sustained watching: keep camera open, send snapshots to
        vision model at regular intervals.

        Args:
            camera_name: Which camera to watch through
            interval: Seconds between vision analyses (default: config value, min 30)
            prompt: Custom prompt for each analysis
            on_scene: Optional callback(description) called after each analysis

        Returns:
            Status message
        """
        if not self.running:
            return "Vision system not started"

        if self._watching.get(camera_name):
            return f"Already watching through '{camera_name}'"

        interval = max(interval or self.default_watch_interval, 30)  # Min 30s

        # Open the camera and keep it open
        camera = self._open_camera(camera_name)
        if camera is None:
            return f"Failed to open camera '{camera_name}'"

        self._watch_cameras[camera_name] = camera
        self._watching[camera_name] = True

        # Start the watch loop in a background thread
        thread = threading.Thread(
            target=self._watch_loop,
            args=(camera_name, interval, prompt, on_scene),
            daemon=True,
            name=f"VisionSystem-Watch-{camera_name}"
        )
        thread.start()
        self._watch_threads[camera_name] = thread

        self.logger.info(f"Started watching through '{camera_name}' (every {interval}s)")
        return f"Now watching through '{camera_name}' — analyzing every {interval}s"

    def stop_watching(self, camera_name='webcam') -> str:
        """Stop sustained watching for a camera."""
        if not self._watching.get(camera_name):
            return f"Not currently watching through '{camera_name}'"

        self._watching[camera_name] = False

        # Wait for thread to finish
        thread = self._watch_threads.get(camera_name)
        if thread and thread.is_alive():
            thread.join(timeout=5)

        # Release the camera
        cam = self._watch_cameras.pop(camera_name, None)
        if cam:
            try:
                cam.release()
            except Exception:
                pass

        self._watch_threads.pop(camera_name, None)
        self.logger.info(f"Stopped watching through '{camera_name}'")
        return f"Stopped watching through '{camera_name}'"

    def is_watching(self, camera_name='webcam') -> bool:
        """Check if currently watching through a camera."""
        return self._watching.get(camera_name, False)

    def _watch_loop(self, camera_name, interval, prompt, on_scene):
        """Background loop for sustained watching."""
        self.logger.info(f"Watch loop started: '{camera_name}' every {interval}s")

        while self._watching.get(camera_name) and self.running:
            try:
                frame = self._read_from_open_camera(camera_name)

                if frame is not None:
                    # Check if scene changed before burning an Ollama call
                    last_frame = self._last_frames.get(camera_name)
                    if last_frame is not None:
                        changed = self._detect_scene_change(last_frame, frame)
                        if not changed and self.current_scenes.get(camera_name):
                            # Scene unchanged, skip analysis
                            time.sleep(interval)
                            continue

                    # Analyze the frame
                    description = self._analyze_frame(camera_name, frame, prompt)

                    if description and on_scene:
                        try:
                            on_scene(description)
                        except Exception as e:
                            self.logger.error(f"Watch callback error: {e}")
                else:
                    self.logger.warning(f"Watch: failed to read frame from '{camera_name}'")

            except Exception as e:
                self.logger.error(f"Watch loop error for '{camera_name}': {e}")

            # Wait for next interval
            # Use small sleeps so we can break out quickly when stop_watching is called
            for _ in range(int(interval)):
                if not self._watching.get(camera_name) or not self.running:
                    break
                time.sleep(1)

        self.logger.info(f"Watch loop ended: '{camera_name}'")

    # ── Scene Change Detection ──────────────────────────────────────

    def has_scene_changed(self, camera_name='webcam') -> Optional[bool]:
        """
        Check if the scene has changed since last look/watch analysis.

        Returns:
            True if changed, False if same, None if no previous frame
        """
        if not self.running:
            return None

        if camera_name in self._watch_cameras and self._watch_cameras[camera_name].isOpened():
            frame = self._read_from_open_camera(camera_name)
        else:
            frame = self._grab_frame(camera_name)

        if frame is None:
            return None

        last_frame = self._last_frames.get(camera_name)
        if last_frame is None:
            return None

        return self._detect_scene_change(last_frame, frame)

    def get_current_scene(self, camera_name='webcam') -> Optional[str]:
        """Get the most recent scene description (cached from last look/watch)."""
        return self.current_scenes.get(camera_name)

    def get_all_scenes(self) -> Dict[str, str]:
        """Get all current scene descriptions."""
        return self.current_scenes.copy()

    def get_status(self) -> Dict[str, Any]:
        """Get vision system status."""
        watching = {name: True for name, active in self._watching.items() if active}
        return {
            'running': self.running,
            'mode': 'on-demand + watch',
            'available_cameras': self.enabled_cameras,
            'watching': watching,
            'scenes_cached': list(self.current_scenes.keys()),
            'total_looks': len(self.scene_history),
            'last_look': {
                name: ts.isoformat()
                for name, ts in self.last_analysis.items()
            } if self.last_analysis else {}
        }

    # ── Camera Management ───────────────────────────────────────────

    def _open_camera(self, camera_name) -> Optional[cv2.VideoCapture]:
        """Open a camera by name and return the VideoCapture object."""
        try:
            if camera_name == 'webcam':
                camera = cv2.VideoCapture(self.webcam_index)
                if not camera.isOpened():
                    camera = cv2.VideoCapture(self.webcam_index, cv2.CAP_DSHOW)
                if not camera.isOpened():
                    self.logger.warning(f"Cannot open webcam at index {self.webcam_index}")
                    return None
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                return camera
            else:
                ip_cam = next((c for c in self.ip_cameras if c['name'] == camera_name), None)
                if not ip_cam:
                    self.logger.warning(f"IP camera '{camera_name}' not configured")
                    return None
                camera = cv2.VideoCapture(ip_cam['url'])
                if not camera.isOpened():
                    self.logger.warning(f"Cannot open IP camera '{camera_name}'")
                    return None
                return camera
        except Exception as e:
            self.logger.error(f"Failed to open camera '{camera_name}': {e}")
            return None

    def _grab_frame(self, camera_name='webcam') -> Optional[np.ndarray]:
        """Open camera, grab a single frame, release. For one-shot look()."""
        camera = self._open_camera(camera_name)
        if camera is None:
            return None

        try:
            # Read a few frames to let camera auto-expose
            for _ in range(3):
                ret, frame = camera.read()
            if not ret or frame is None:
                self.logger.warning(f"Camera '{camera_name}' opened but failed to read frame")
                return None
            return frame
        finally:
            camera.release()

    def _read_from_open_camera(self, camera_name) -> Optional[np.ndarray]:
        """Read a frame from an already-open camera (used during watch mode)."""
        cam = self._watch_cameras.get(camera_name)
        if cam is None or not cam.isOpened():
            return None
        ret, frame = cam.read()
        if not ret or frame is None:
            return None
        return frame

    # ── Vision Analysis ─────────────────────────────────────────────

    def _analyze_frame(self, camera_name, frame, prompt=None) -> Optional[str]:
        """Send frame to vision model and process the response."""
        try:
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            image_base64 = base64.b64encode(buffer).decode('utf-8')

            if not prompt:
                prompt = ("Describe what you see in this image concisely. "
                          "Focus on people, objects, activities, and any notable changes.")

            if not self.bot.ollama:
                self.logger.warning("Ollama client not available for vision")
                return None

            response = self.bot.ollama.generate_with_vision(
                prompt=prompt,
                image_base64=image_base64,
                vision_model=self.vision_model
            )

            if not response:
                self.logger.warning(f"No vision response for '{camera_name}'")
                return None

            description = response.get('response', '').strip()
            if not description:
                self.logger.warning(f"Empty vision response for '{camera_name}'")
                return None

            # Update state
            self.current_scenes[camera_name] = description
            self.last_analysis[camera_name] = datetime.now()
            self._last_frames[camera_name] = frame.copy()

            # History
            self.scene_history.append({
                'camera': camera_name,
                'time': self.last_analysis[camera_name],
                'description': description,
                'prompt': prompt
            })
            if len(self.scene_history) > 100:
                self.scene_history = self.scene_history[-100:]

            self.logger.info(f"[{camera_name}] Vision: {description[:80]}...")

            # Feed to sentience systems
            self._feed_phase5(camera_name, description)
            self._feed_embodied(camera_name, description)

            return description

        except Exception as e:
            self.logger.error(f"Vision analysis error for '{camera_name}': {e}")
            return None

    def _feed_phase5(self, camera_name, description):
        """Feed vision result to Phase 5 sentience systems."""
        if not self.bot.phase5:
            return
        try:
            self.bot.phase5.cognition.perceive({
                'user_input': f"[Vision:{camera_name}] {description}",
                'source': 'vision',
                'camera': camera_name,
                'timestamp': self.last_analysis[camera_name]
            })
            if self._is_interesting(description):
                self.bot.phase5.affective.generate_emotion(
                    f"Seeing something interesting: {description[:100]}",
                    {'source': 'vision', 'camera': camera_name}
                )
        except Exception as e:
            self.logger.error(f"Phase 5 vision integration error: {e}")

    def _feed_embodied(self, camera_name, description):
        """Feed vision result to V2.6 Embodied Experience."""
        if not hasattr(self.bot, 'embodied_experience') or not self.bot.embodied_experience:
            return
        try:
            visual_event = self.bot.embodied_experience.process_visual_scene(
                description, camera=camera_name
            )
            if visual_event and self.bot.phase5 and self.bot.phase5.affective:
                self.bot.embodied_experience.feed_to_affective_system(
                    visual_event, self.bot.phase5.affective
                )
        except Exception as e:
            self.logger.error(f"V2.6 embodied experience error: {e}")

    def _detect_scene_change(self, frame1, frame2) -> bool:
        """Detect if scene changed significantly between two frames."""
        try:
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            if gray1.shape != gray2.shape:
                gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))
            diff = cv2.absdiff(gray1, gray2)
            _, thresh = cv2.threshold(diff, self.motion_sensitivity, 255, cv2.THRESH_BINARY)
            change_ratio = np.count_nonzero(thresh) / thresh.size
            return change_ratio > 0.05
        except Exception as e:
            self.logger.error(f"Scene change detection error: {e}")
            return True

    def _is_interesting(self, description):
        """Determine if a scene description is interesting."""
        keywords = ['person', 'people', 'face', 'movement', 'moving',
                    'unusual', 'change', 'new', 'different']
        desc_lower = description.lower()
        return any(kw in desc_lower for kw in keywords)

    # ── Camera Discovery ────────────────────────────────────────────

    def discover_ip_cameras(self, network='192.168.1', port_range=(554, 8080)):
        """Discover IP cameras on local network by scanning common ports."""
        self.logger.info(f"Scanning network {network}.0/24 for IP cameras...")

        import config as cfg
        credentials = getattr(cfg, 'VISION_DISCOVERY_CREDENTIALS', [('admin', 'admin')])

        discovered = []
        ports = [554, 8080, 8081, 80, 81]

        for i in range(1, 255):
            ip = f"{network}.{i}"
            for port in ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    result = sock.connect_ex((ip, port))
                    sock.close()
                    if result == 0:
                        self.logger.info(f"Found device at {ip}:{port}")
                        for username, password in credentials:
                            cred = f"{username}:{password}@" if password else f"{username}@"
                            discovered.append({'ip': ip, 'port': port,
                                               'url': f"rtsp://{cred}{ip}:{port}/stream"})
                        discovered.append({'ip': ip, 'port': port,
                                           'url': f"rtsp://{ip}:{port}/"})
                        break
                except Exception:
                    pass

        self.logger.info(f"Discovery complete: found {len(discovered)} potential cameras")
        return discovered

    def add_ip_camera(self, name, url, camera_type='rtsp'):
        """Add a new IP camera configuration."""
        self.ip_cameras.append({'name': name, 'url': url, 'type': camera_type})
        self.enabled_cameras.append(name)
        return True


# Convenience functions
def generate_rtsp_url(ip, username='admin', password='', port=554, path='/stream'):
    """Generate RTSP URL for IP camera"""
    cred = f"{username}:{password}@" if password else f"{username}@" if username else ""
    return f"rtsp://{cred}{ip}:{port}{path}"

def generate_http_url(ip, username='admin', password='', port=80, path='/video'):
    """Generate HTTP URL for IP camera"""
    cred = f"{username}:{password}@" if password else f"{username}@" if username else ""
    return f"http://{cred}{ip}:{port}{path}"
