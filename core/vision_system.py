"""
Vision System - Seven's Eyes

Continuous visual perception using:
- Local webcam (USB camera)
- IP cameras (RTSP/HTTP streams)
- llama3.2-vision for scene understanding

This gives Seven the ability to see and understand her environment.
"""

import cv2
import base64
import threading
import time
import socket
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
import numpy as np

class VisionSystem:
    """
    Seven's vision system - continuous visual perception
    
    Supports:
    - USB webcams
    - IP cameras (RTSP/HTTP)
    - Automatic camera discovery
    - llama3.2-vision integration
    """
    
    def __init__(self, bot, config=None):
        """
        Initialize vision system
        
        Args:
            bot: Reference to main bot instance
            config: Vision configuration dict
        """
        self.bot = bot
        self.logger = logging.getLogger("VisionSystem")
        
        # Configuration
        config = config or {}
        self.enabled_cameras = config.get('enabled_cameras', ['webcam'])  # ['webcam', 'ip_camera_1']
        self.analysis_interval = config.get('analysis_interval', 30)  # Analyze every 30 seconds
        self.frame_skip = config.get('frame_skip', 10)  # Process every Nth frame
        self.vision_model = config.get('vision_model', 'llama3.2-vision')
        
        # Camera sources
        self.cameras = {}
        self.camera_threads = {}
        
        # Webcam config
        self.webcam_index = config.get('webcam_index', 0)
        
        # IP camera config
        self.ip_cameras = config.get('ip_cameras', [])
        # Format: [{'name': 'nanny_cam', 'url': 'rtsp://admin:admin123456@192.168.1.100:554/stream', 'type': 'rtsp'}]
        
        # State
        self.running = False
        self.current_scenes = {}  # {camera_name: scene_description}
        self.scene_history = []
        self.last_analysis = {}  # {camera_name: timestamp}
        
        # Detection settings
        self.motion_sensitivity = config.get('motion_sensitivity', 50)
        self.interesting_threshold = config.get('interesting_threshold', 0.7)
    
    def start(self):
        """Start vision system"""
        if self.running:
            self.logger.warning("Vision system already running")
            return
        
        self.running = True
        
        # Start webcam if enabled
        if 'webcam' in self.enabled_cameras:
            success = self._start_webcam()
            if success:
                self.logger.info("✓ Webcam started")
            else:
                self.logger.warning("Webcam failed to start")
        
        # Start IP cameras if configured
        for ip_cam in self.ip_cameras:
            if ip_cam['name'] in self.enabled_cameras:
                success = self._start_ip_camera(ip_cam)
                if success:
                    self.logger.info(f"✓ IP camera '{ip_cam['name']}' started")
                else:
                    self.logger.warning(f"IP camera '{ip_cam['name']}' failed to start")
        
        if self.cameras:
            self.logger.info(f"✓ Vision system started with {len(self.cameras)} camera(s)")
        else:
            self.logger.error("Vision system: No cameras available")
            self.running = False
    
    def stop(self):
        """Stop vision system"""
        self.logger.info("Stopping vision system...")
        self.running = False
        
        # Stop all cameras
        for name, camera in self.cameras.items():
            try:
                camera.release()
                self.logger.info(f"Camera '{name}' stopped")
            except Exception as e:
                self.logger.error(f"Error stopping camera '{name}': {e}")
        
        # Wait for threads to finish
        for name, thread in self.camera_threads.items():
            if thread.is_alive():
                thread.join(timeout=5)
        
        self.cameras.clear()
        self.camera_threads.clear()
        
        self.logger.info("Vision system stopped")
    
    def _start_webcam(self):
        """Start USB webcam"""
        try:
            camera = cv2.VideoCapture(self.webcam_index)
            
            if not camera.isOpened():
                self.logger.error(f"Failed to open webcam at index {self.webcam_index}")
                return False
            
            # Set camera properties for better quality
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camera.set(cv2.CAP_PROP_FPS, 15)
            
            self.cameras['webcam'] = camera
            
            # Start processing thread
            thread = threading.Thread(
                target=self._camera_loop,
                args=('webcam', camera),
                daemon=True,
                name="VisionSystem-Webcam"
            )
            thread.start()
            self.camera_threads['webcam'] = thread
            
            return True
            
        except Exception as e:
            self.logger.error(f"Webcam initialization error: {e}")
            return False
    
    def _start_ip_camera(self, ip_cam_config):
        """Start IP camera"""
        name = ip_cam_config['name']
        url = ip_cam_config['url']
        cam_type = ip_cam_config.get('type', 'rtsp')
        
        try:
            # Try to connect
            camera = cv2.VideoCapture(url)
            
            if not camera.isOpened():
                self.logger.error(f"Failed to open IP camera '{name}' at {url}")
                return False
            
            self.cameras[name] = camera
            
            # Start processing thread
            thread = threading.Thread(
                target=self._camera_loop,
                args=(name, camera),
                daemon=True,
                name=f"VisionSystem-{name}"
            )
            thread.start()
            self.camera_threads[name] = thread
            
            return True
            
        except Exception as e:
            self.logger.error(f"IP camera '{name}' initialization error: {e}")
            return False
    
    def _camera_loop(self, camera_name, camera):
        """Main processing loop for a camera"""
        self.logger.info(f"Camera '{camera_name}' processing started")

        frame_count = 0
        last_frame = None
        consecutive_failures = 0
        MAX_BACKOFF = 30  # Max seconds between retries

        while self.running:
            try:
                ret, frame = camera.read()

                if not ret:
                    consecutive_failures += 1
                    if consecutive_failures == 1:
                        self.logger.warning(f"Camera '{camera_name}' failed to read frame — retrying...")
                    elif consecutive_failures == 5:
                        self.logger.warning(f"Camera '{camera_name}' still failing — is another app using it?")
                    elif consecutive_failures == 15:
                        self.logger.error(f"Camera '{camera_name}' unavailable after 15 attempts — backing off")

                    # Exponential backoff: 1s, 2s, 4s, ... capped at MAX_BACKOFF
                    backoff = min(2 ** min(consecutive_failures - 1, 5), MAX_BACKOFF)
                    time.sleep(backoff)

                    # Try to reopen the camera after many failures
                    if consecutive_failures == 15:
                        self.logger.info(f"Camera '{camera_name}' attempting to reopen...")
                        camera.release()
                        time.sleep(2)
                        if camera_name == 'webcam':
                            camera = cv2.VideoCapture(self.webcam_index)
                            # Try DirectShow fallback on Windows
                            if not camera.isOpened():
                                camera = cv2.VideoCapture(self.webcam_index, cv2.CAP_DSHOW)
                        if camera.isOpened():
                            self.cameras[camera_name] = camera
                            self.logger.info(f"Camera '{camera_name}' reopened successfully")
                            consecutive_failures = 0
                        else:
                            self.logger.warning(f"Camera '{camera_name}' reopen failed — will keep retrying every {MAX_BACKOFF}s")
                    continue

                # Reset failure counter on successful read
                if consecutive_failures > 0:
                    self.logger.info(f"Camera '{camera_name}' recovered after {consecutive_failures} failures")
                    consecutive_failures = 0

                frame_count += 1

                # Process only every Nth frame
                if frame_count % self.frame_skip != 0:
                    continue

                # Check if should analyze
                if self._should_analyze(camera_name):
                    # Detect if scene changed significantly
                    if last_frame is not None:
                        changed = self._detect_scene_change(last_frame, frame)
                        if not changed and self.current_scenes.get(camera_name):
                            # Skip analysis if scene hasn't changed
                            continue

                    # Analyze scene
                    self._analyze_scene(camera_name, frame)
                    last_frame = frame.copy()

            except Exception as e:
                self.logger.error(f"Camera '{camera_name}' loop error: {e}")
                time.sleep(1)

        self.logger.info(f"Camera '{camera_name}' processing stopped")

            if not camera.isOpened():
                self.logger.info(f"Default backend failed for index {self.webcam_index}, trying DirectShow...")
                camera = cv2.VideoCapture(self.webcam_index, cv2.CAP_DSHOW)

            if not camera.isOpened():
                self.logger.error(f"Failed to open webcam at index {self.webcam_index}")
                return False
            
            # Set camera properties for better quality
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camera.set(cv2.CAP_PROP_FPS, 15)
            
            self.cameras['webcam'] = camera
            
            # Start processing thread
            thread = threading.Thread(
                target=self._camera_loop,
                args=('webcam', camera),
                daemon=True,
                name="VisionSystem-Webcam"
            )
            thread.start()
            self.camera_threads['webcam'] = thread
            
            return True
            
        except Exception as e:
            self.logger.error(f"Webcam initialization error: {e}")
            return False
    
    def _start_ip_camera(self, ip_cam_config):
        """Start IP camera"""
        name = ip_cam_config['name']
        url = ip_cam_config['url']
        cam_type = ip_cam_config.get('type', 'rtsp')
        
        try:
            # Try to connect
            camera = cv2.VideoCapture(url)
            
            if not camera.isOpened():
                self.logger.error(f"Failed to open IP camera '{name}' at {url}")
                return False
            
            self.cameras[name] = camera
            
            # Start processing thread
            thread = threading.Thread(
                target=self._camera_loop,
                args=(name, camera),
                daemon=True,
                name=f"VisionSystem-{name}"
            )
            thread.start()
            self.camera_threads[name] = thread
            
            return True
            
        except Exception as e:
            self.logger.error(f"IP camera '{name}' initialization error: {e}")
            return False
    
    def _camera_loop(self, camera_name, camera):
        """Main processing loop for a camera"""
        self.logger.info(f"Camera '{camera_name}' processing started")
        
        frame_count = 0
        last_frame = None
        
        while self.running:
            try:
                ret, frame = camera.read()
                
                if not ret:
                    self.logger.warning(f"Camera '{camera_name}' failed to read frame")
                    time.sleep(1)
                    continue
                
                frame_count += 1
                
                # Process only every Nth frame
                if frame_count % self.frame_skip != 0:
                    continue
                
                # Check if should analyze
                if self._should_analyze(camera_name):
                    # Detect if scene changed significantly
                    if last_frame is not None:
                        changed = self._detect_scene_change(last_frame, frame)
                        if not changed and self.current_scenes.get(camera_name):
                            # Skip analysis if scene hasn't changed
                            continue
                    
                    # Analyze scene
                    self._analyze_scene(camera_name, frame)
                    last_frame = frame.copy()
                
            except Exception as e:
                self.logger.error(f"Camera '{camera_name}' loop error: {e}")
                time.sleep(1)
        
        self.logger.info(f"Camera '{camera_name}' processing stopped")
    
    def _should_analyze(self, camera_name):
        """Should we analyze this frame?"""
        last = self.last_analysis.get(camera_name)
        
        if not last:
            return True
        
        elapsed = (datetime.now() - last).total_seconds()
        return elapsed >= self.analysis_interval
    
    def _detect_scene_change(self, frame1, frame2):
        """Detect if scene changed significantly between frames"""
        try:
            # Convert to grayscale
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            
            # Compute difference
            diff = cv2.absdiff(gray1, gray2)
            
            # Threshold
            _, thresh = cv2.threshold(diff, self.motion_sensitivity, 255, cv2.THRESH_BINARY)
            
            # Count changed pixels
            changed_pixels = np.count_nonzero(thresh)
            total_pixels = thresh.size
            
            change_ratio = changed_pixels / total_pixels
            
            # Consider significant if >5% of pixels changed
            return change_ratio > 0.05
            
        except Exception as e:
            self.logger.error(f"Scene change detection error: {e}")
            return True  # Assume changed if error
    
    def _analyze_scene(self, camera_name, frame):
        """Analyze scene with llama3.2-vision"""
        try:
            # Convert frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            # Convert to base64
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Prepare prompt
            prompt = "Describe what you see in this image concisely. Focus on people, objects, activities, and any notable changes."
            
            # Send to Ollama
            if not self.bot.ollama:
                self.logger.warning("Ollama client not available")
                return
            
            # FIXED: Use new generate_with_vision method
            response = self.bot.ollama.generate_with_vision(
                prompt=prompt,
                image_base64=image_base64,
                vision_model=self.vision_model
            )
            
            if not response:
                self.logger.warning(f"No vision response for camera '{camera_name}'")
                return
            
            description = response.get('response', '').strip()
            
            if not description:
                self.logger.warning(f"Empty vision response for camera '{camera_name}'")
                return
            
            # Update state
            self.current_scenes[camera_name] = description
            self.last_analysis[camera_name] = datetime.now()
            
            # Add to history
            self.scene_history.append({
                'camera': camera_name,
                'time': self.last_analysis[camera_name],
                'description': description
            })
            
            # Keep only last 100 scenes
            if len(self.scene_history) > 100:
                self.scene_history = self.scene_history[-100:]
            
            self.logger.info(f"[{camera_name}] Vision: {description[:60]}...")
            
            # Feed to Phase 5 cognitive system
            if self.bot.phase5:
                try:
                    self.bot.phase5.cognition.perceive({
                        'user_input': f"[Vision:{camera_name}] {description}",
                        'source': 'vision',
                        'camera': camera_name,
                        'timestamp': self.last_analysis[camera_name]
                    })
                    
                    # Generate appropriate emotional response
                    if self._is_interesting(description):
                        self.bot.phase5.affective.generate_emotion(
                            f"Seeing something interesting: {description[:100]}",
                            {'source': 'vision', 'camera': camera_name}
                        )
                
                except Exception as e:
                    self.logger.error(f"Phase 5 vision integration error: {e}")
            
            # V2.6: Embodied Experience — vision triggers genuine emotions
            if hasattr(self.bot, 'embodied_experience') and self.bot.embodied_experience:
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
            
        except Exception as e:
            self.logger.error(f"Scene analysis error for camera '{camera_name}': {e}")
    
    def _is_interesting(self, description):
        """Determine if scene is interesting"""
        interesting_keywords = [
            'person', 'people', 'face', 'movement', 'moving',
            'unusual', 'change', 'new', 'different'
        ]
        
        desc_lower = description.lower()
        
        for keyword in interesting_keywords:
            if keyword in desc_lower:
                return True
        
        return False
    
    def get_current_scene(self, camera_name='webcam'):
        """Get latest scene description from camera"""
        return self.current_scenes.get(camera_name)
    
    def get_all_scenes(self):
        """Get all current scenes from all cameras"""
        return self.current_scenes.copy()
    
    def discover_ip_cameras(self, network='192.168.1', port_range=(554, 8080)):
        """
        Discover IP cameras on local network
        
        This scans the network for common camera ports.
        Credentials are read from config.VISION_DISCOVERY_CREDENTIALS.
        """
        self.logger.info(f"Scanning network {network}.0/24 for IP cameras...")
        
        import config as cfg
        credentials = getattr(cfg, 'VISION_DISCOVERY_CREDENTIALS', [('admin', 'admin')])
        
        discovered = []
        
        # Common camera ports
        ports = [554, 8080, 8081, 80, 81]
        
        for i in range(1, 255):
            ip = f"{network}.{i}"
            
            for port in ports:
                try:
                    # Quick connection test
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    result = sock.connect_ex((ip, port))
                    sock.close()
                    
                    if result == 0:
                        self.logger.info(f"Found device at {ip}:{port}")
                        
                        # Try credential combinations from config
                        for username, password in credentials:
                            cred = f"{username}:{password}@" if password else f"{username}@"
                            urls = [
                                f"rtsp://{cred}{ip}:{port}/stream",
                                f"http://{cred}{ip}:{port}/video",
                            ]
                            for url in urls:
                                discovered.append({
                                    'ip': ip,
                                    'port': port,
                                    'url': url
                                })
                        
                        # Also try without credentials
                        discovered.append({
                            'ip': ip,
                            'port': port,
                            'url': f"rtsp://{ip}:{port}/"
                        })
                        
                        break  # Don't check other ports for this IP
                        
                except Exception:
                    pass
        
        self.logger.info(f"Discovery complete: found {len(discovered)} potential cameras")
        return discovered
    
    def add_ip_camera(self, name, url, camera_type='rtsp'):
        """Add and start a new IP camera"""
        config = {
            'name': name,
            'url': url,
            'type': camera_type
        }
        
        self.ip_cameras.append(config)
        self.enabled_cameras.append(name)
        
        if self.running:
            success = self._start_ip_camera(config)
            return success
        
        return True
    
    def get_status(self):
        """Get vision system status"""
        return {
            'running': self.running,
            'cameras': list(self.cameras.keys()),
            'active_cameras': len(self.cameras),
            'scenes': {name: scene[:50] for name, scene in self.current_scenes.items()},
            'total_scenes_analyzed': len(self.scene_history)
        }


# Convenience function for IP camera URL generation
def generate_rtsp_url(ip, username='admin', password='', port=554, path='/stream'):
    """Generate RTSP URL for IP camera"""
    cred = f"{username}:{password}@" if password else f"{username}@" if username else ""
    return f"rtsp://{cred}{ip}:{port}{path}"

def generate_http_url(ip, username='admin', password='', port=80, path='/video'):
    """Generate HTTP URL for IP camera"""
    cred = f"{username}:{password}@" if password else f"{username}@" if username else ""
    return f"http://{cred}{ip}:{port}{path}"
