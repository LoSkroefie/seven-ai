"""
Natural Voice Engine for Seven AI
- edge-tts: Microsoft neural TTS voices (free, natural-sounding)
- pygame: Audio playback with instant interrupt support
- Voice + keyboard barge-in for natural conversation flow
- Falls back to pyttsx3 if edge-tts/pygame unavailable
"""
import asyncio
import os
import re
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional
import logging

import math
import struct

import config

# --- Graceful imports with fallbacks ---

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

logger = logging.getLogger("VoiceEngine")

# Map Seven's Emotion enum values to edge-tts voice parameters
# rate/pitch/volume are relative adjustments (e.g. "+10%", "-5Hz")
EMOTION_VOICE_MAP = {
    'anger':          {'rate': '+10%',  'pitch': '-5Hz',  'volume': '+10%'},
    'sadness':        {'rate': '-20%',  'pitch': '-8Hz',  'volume': '-15%'},
    'happiness':      {'rate': '+12%',  'pitch': '+6Hz',  'volume': '+5%'},
    'enjoyment':      {'rate': '+8%',   'pitch': '+4Hz',  'volume': '+5%'},
    'surprise':       {'rate': '+10%',  'pitch': '+10Hz', 'volume': '+5%'},
    'excitement':     {'rate': '+18%',  'pitch': '+8Hz',  'volume': '+10%'},
    'love':           {'rate': '-5%',   'pitch': '+3Hz',  'volume': '-5%'},
    'calmness':       {'rate': '-12%',  'pitch': '-3Hz',  'volume': '-10%'},
    'confusion':      {'rate': '-5%',   'pitch': '+2Hz',  'volume': '+0%'},
    'empathy':        {'rate': '-8%',   'pitch': '+2Hz',  'volume': '-5%'},
    'curiosity':      {'rate': '+5%',   'pitch': '+5Hz',  'volume': '+0%'},
    'amusement':      {'rate': '+8%',   'pitch': '+6Hz',  'volume': '+5%'},
    'joy':            {'rate': '+12%',  'pitch': '+6Hz',  'volume': '+5%'},
    'fear':           {'rate': '+8%',   'pitch': '+5Hz',  'volume': '-5%'},
    'anxiety':        {'rate': '+5%',   'pitch': '+3Hz',  'volume': '-5%'},
    'disappointment': {'rate': '-10%',  'pitch': '-5Hz',  'volume': '-10%'},
    'contentment':    {'rate': '-8%',   'pitch': '+0Hz',  'volume': '-5%'},
    'awe':            {'rate': '-5%',   'pitch': '+5Hz',  'volume': '+0%'},
    'tenderness':     {'rate': '-8%',   'pitch': '+3Hz',  'volume': '-8%'},
    'frustration':    {'rate': '+5%',   'pitch': '-3Hz',  'volume': '+5%'},
    'boredom':        {'rate': '-15%',  'pitch': '-5Hz',  'volume': '-10%'},
    'doubt':          {'rate': '-5%',   'pitch': '-2Hz',  'volume': '-5%'},
    'playful':        {'rate': '+10%',  'pitch': '+6Hz',  'volume': '+5%'},
}

# Default params when emotion not mapped
_DEFAULT_VOICE_PARAMS = {'rate': '+0%', 'pitch': '+0Hz', 'volume': '+0%'}


class NaturalVoiceEngine:
    """
    Natural-sounding TTS with instant interrupt support.

    Primary:  edge-tts + pygame  (neural voice, needs internet, free)
    Fallback: pyttsx3            (robotic but fully offline)
    """

    def __init__(self):
        self.is_speaking = False
        self.stop_requested = False
        self._lock = threading.Lock()
        self._temp_dir = Path(tempfile.gettempdir()) / "seven_tts"
        self._temp_dir.mkdir(exist_ok=True)
        self._fallback_engine = None
        self._use_edge = EDGE_TTS_AVAILABLE and PYGAME_AVAILABLE
        self._pygame_initialized = False

        # Voice configuration (read from config, with sane defaults)
        self.voice = getattr(config, 'EDGE_TTS_VOICE', 'en-US-AriaNeural')
        self.base_rate = getattr(config, 'EDGE_TTS_RATE', '+0%')
        self.base_pitch = getattr(config, 'EDGE_TTS_PITCH', '+0Hz')
        self.base_volume = getattr(config, 'EDGE_TTS_VOLUME', '+0%')

        # Voice barge-in settings
        self.barge_in_enabled = getattr(config, 'VOICE_BARGE_IN', True) and PYAUDIO_AVAILABLE
        self.barge_in_multiplier = getattr(config, 'BARGE_IN_SENSITIVITY', 2.0)
        self.barge_in_consecutive = getattr(config, 'BARGE_IN_FRAMES', 3)
        self._barge_in_thread = None

        if self._use_edge:
            try:
                pygame.mixer.init(frequency=24000)
                self._pygame_initialized = True
                print(f"[OK] Natural voice engine ready (edge-tts: {self.voice})")
            except Exception as e:
                logger.warning(f"pygame mixer init failed: {e}")
                print(f"[WARNING] pygame init failed ({e}), falling back to pyttsx3")
                self._use_edge = False

        if not self._use_edge:
            self._init_fallback()

        # Report status
        if not self._use_edge and not self._fallback_engine:
            print("[WARNING] No TTS engine available — speech output disabled")

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    def _init_fallback(self):
        """Initialize pyttsx3 as fallback TTS engine."""
        if not PYTTSX3_AVAILABLE:
            return
        try:
            self._fallback_engine = pyttsx3.init()
            voices = self._fallback_engine.getProperty('voices')
            if len(voices) > config.DEFAULT_VOICE_INDEX:
                self._fallback_engine.setProperty('voice', voices[config.DEFAULT_VOICE_INDEX].id)
            self._fallback_engine.setProperty('rate', config.DEFAULT_SPEECH_RATE)
            self._fallback_engine.setProperty('volume', config.DEFAULT_VOLUME)
            print("[OK] Fallback voice engine ready (pyttsx3)")
        except Exception as e:
            logger.error(f"pyttsx3 init failed: {e}")
            self._fallback_engine = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def speak(self, text: str, emotion: str = "neutral", emotion_config=None,
              prosody_override: dict = None):
        """
        Speak *text* with a natural voice.  Interruptible via keyboard (ESC / SPACE)
        or by speaking (voice barge-in).

        Args:
            text:             Raw text to speak (markdown is stripped automatically).
            emotion:          Emotion name string (e.g. "happiness", "sadness").
            emotion_config:   Legacy EmotionConfig dataclass — used by pyttsx3 fallback.
            prosody_override: V2.6 multi-modal override dict {'rate', 'pitch', 'volume'}.
        """
        if not text:
            return

        text = self._clean_for_speech(text)
        if not text:
            return

        with self._lock:
            self.stop_requested = False
            self.is_speaking = True

        try:
            if self._use_edge:
                self._speak_edge(text, emotion, prosody_override=prosody_override)
            elif self._fallback_engine:
                self._speak_pyttsx3(text, emotion_config)
            else:
                print(f"[TTS unavailable] {text}")
        finally:
            with self._lock:
                self.is_speaking = False

    def stop(self):
        """Stop speaking immediately."""
        self.stop_requested = True
        if self._use_edge and self._pygame_initialized:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    @property
    def available(self) -> bool:
        return self._use_edge or self._fallback_engine is not None

    # ------------------------------------------------------------------
    # edge-tts + pygame
    # ------------------------------------------------------------------

    def _speak_edge(self, text: str, emotion: str, prosody_override: dict = None):
        """Generate speech with edge-tts, play through pygame."""
        audio_path = str(self._temp_dir / "speech.mp3")

        # Map emotion to voice adjustments
        params = EMOTION_VOICE_MAP.get(emotion, _DEFAULT_VOICE_PARAMS)
        rate = params.get('rate', self.base_rate)
        pitch = params.get('pitch', self.base_pitch)
        volume = params.get('volume', self.base_volume)

        # V2.6: Apply multimodal prosody override if provided
        if prosody_override:
            rate = prosody_override.get('rate', rate)
            pitch = prosody_override.get('pitch', pitch)
            volume = prosody_override.get('volume', volume)

        try:
            # Generate audio (sync wrapper around async edge-tts)
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(
                    self._generate_edge_audio(text, audio_path, rate, pitch, volume)
                )
            finally:
                loop.close()

            if self.stop_requested:
                return

            # Play
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()

            # Start voice barge-in monitor (listens for user speaking)
            if self.barge_in_enabled:
                self._start_barge_in_monitor()

            # Poll until playback finishes or user interrupts
            while pygame.mixer.music.get_busy():
                if self.stop_requested:
                    pygame.mixer.music.stop()
                    break

                # Keyboard barge-in (ESC or SPACE)
                if KEYBOARD_AVAILABLE:
                    try:
                        if keyboard.is_pressed('esc') or keyboard.is_pressed('space'):
                            print("\n[INTERRUPTED] Stopped by keypress")
                            pygame.mixer.music.stop()
                            self.stop_requested = True
                            time.sleep(0.3)  # debounce
                            break
                    except Exception:
                        pass

                time.sleep(0.05)  # ~20 checks/sec

        except Exception as e:
            logger.warning(f"edge-tts speak error: {e}")
            # Try pyttsx3 fallback
            if not self._fallback_engine:
                self._init_fallback()
            if self._fallback_engine:
                self._speak_pyttsx3(text, None)
        finally:
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass
            try:
                os.remove(audio_path)
            except Exception:
                pass

    async def _generate_edge_audio(self, text: str, output_path: str,
                                    rate: str, pitch: str, volume: str):
        """Generate audio file with edge-tts."""
        communicate = edge_tts.Communicate(
            text,
            self.voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
        )
        await communicate.save(output_path)

    # ------------------------------------------------------------------
    # pyttsx3 fallback
    # ------------------------------------------------------------------

    def _speak_pyttsx3(self, text: str, emotion_config=None):
        """Speak using pyttsx3 (sentence-by-sentence for interruptibility)."""
        if not self._fallback_engine:
            return

        try:
            if emotion_config:
                self._fallback_engine.setProperty('rate', emotion_config.voice_rate)
                self._fallback_engine.setProperty('volume', emotion_config.voice_volume / 100)
            else:
                self._fallback_engine.setProperty('rate', config.DEFAULT_SPEECH_RATE)
                self._fallback_engine.setProperty('volume', config.DEFAULT_VOLUME)

            sentences = self._split_sentences(text)
            for sentence in sentences:
                if self.stop_requested:
                    break
                self._fallback_engine.say(sentence)
                self._fallback_engine.runAndWait()

                # Check keyboard between sentences
                if KEYBOARD_AVAILABLE:
                    try:
                        if keyboard.is_pressed('esc') or keyboard.is_pressed('space'):
                            print("\n[INTERRUPTED] Stopped by keypress")
                            self.stop_requested = True
                            time.sleep(0.3)
                            break
                    except Exception:
                        pass

        except Exception as e:
            logger.error(f"pyttsx3 speak error: {e}")

    # ------------------------------------------------------------------
    # Voice barge-in (mic energy monitoring)
    # ------------------------------------------------------------------

    def _start_barge_in_monitor(self):
        """Spawn a background thread that monitors mic energy during playback.
        If the user starts speaking (energy spike above speaker baseline),
        stop playback immediately."""
        self._barge_in_thread = threading.Thread(
            target=self._barge_in_loop, daemon=True
        )
        self._barge_in_thread.start()

    def _barge_in_loop(self):
        """Background loop: read mic chunks, detect user voice over speaker output."""
        RATE = 16000
        CHUNK = 1024
        BASELINE_SECONDS = 2.0  # measure speaker bleed-through for this long
        pa = None
        stream = None

        try:
            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
            )

            # --- Phase 1: measure baseline energy (speaker bleed + ambient) ---
            baseline_samples = []
            baseline_chunks = max(1, int(RATE / CHUNK * BASELINE_SECONDS))
            for _ in range(baseline_chunks):
                if self.stop_requested:
                    return
                data = stream.read(CHUNK, exception_on_overflow=False)
                baseline_samples.append(self._rms(data))

            baseline = sum(baseline_samples) / len(baseline_samples) if baseline_samples else 500
            # Threshold = baseline × multiplier (default 2×)
            threshold = max(baseline * self.barge_in_multiplier, 800)

            # --- Phase 2: monitor for energy spikes ---
            consecutive_above = 0
            while self.is_speaking and not self.stop_requested:
                data = stream.read(CHUNK, exception_on_overflow=False)
                rms = self._rms(data)

                if rms > threshold:
                    consecutive_above += 1
                else:
                    consecutive_above = 0

                # Require several consecutive high-energy frames to avoid
                # false triggers from transient noise (cough, click, etc.)
                if consecutive_above >= self.barge_in_consecutive:
                    print(f"\n[BARGE-IN] Voice detected (energy {rms:.0f} > {threshold:.0f}) — stopping")
                    self.stop_requested = True
                    try:
                        pygame.mixer.music.stop()
                    except Exception:
                        pass
                    break

        except Exception as e:
            logger.debug(f"Barge-in monitor error: {e}")
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            if pa:
                try:
                    pa.terminate()
                except Exception:
                    pass

    @staticmethod
    def _rms(data: bytes) -> float:
        """Compute RMS energy of a 16-bit PCM audio chunk."""
        count = len(data) // 2
        if count == 0:
            return 0.0
        shorts = struct.unpack(f'{count}h', data)
        sum_sq = sum(s * s for s in shorts)
        return math.sqrt(sum_sq / count)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _split_sentences(text: str) -> list:
        """Split text at sentence boundaries."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def _clean_for_speech(text: str) -> str:
        """Strip markdown, URLs, code blocks — keep only speakable text."""
        # Markdown formatting
        text = re.sub(r'\*\*', '', text)
        text = re.sub(r'__', '', text)
        text = re.sub(r'\*', '', text)
        text = re.sub(r'_', ' ', text)
        # Code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`.*?`', '', text)
        # URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        # Keep only speech-friendly characters
        text = re.sub(r'[^\w\s.,!?\'"():;\-]+', '', text)
        return text.strip()
