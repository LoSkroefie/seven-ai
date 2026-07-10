"""
Voice I/O for Seven.
TTS: edge-tts neural female (Ava) + pygame, barge-in supported.
STT: Whisper local preferred, Google fallback.
Push-to-talk / talk mode — not ambient spam.
"""
from __future__ import annotations

import asyncio
import logging
import re
import tempfile
import threading
import time
from pathlib import Path
from typing import List, Optional, Tuple

from seven import config

logger = logging.getLogger("seven.voice")

_HALLUCINATIONS = frozenset({
    "you", "thank you", "thanks for watching", "thanks for watching.",
    "bye", "bye.", ".", "...", "you.", "thank you.", "subscribe",
    "please subscribe", "the end", "music",
})


class VoiceIO:
    def __init__(self, lazy_whisper: bool = True):
        self.tts_ok = False
        self.stt_ok = False
        self.tts_engine_name = "none"
        self.stt_backend = "none"
        self._whisper = None
        self._whisper_device = "cpu"
        self._lazy_whisper = lazy_whisper
        self._speak_lock = threading.Lock()
        self._stop_speak = threading.Event()
        self.barge_in_enabled = bool(getattr(config, "VOICE_BARGE_IN", True))
        self.last_barge_in = False

        self._init_tts()
        self._init_stt_probe()

    def status(self) -> dict:
        return {
            "tts_ok": self.tts_ok,
            "tts_engine": self.tts_engine_name,
            "tts_voice": getattr(config, "EDGE_TTS_VOICE", ""),
            "stt_ok": self.stt_ok or self._can_google_stt(),
            "stt_backend": self.stt_backend,
            "whisper_loaded": self._whisper is not None,
            "barge_in": self.barge_in_enabled,
            "mic_index": config.MIC_INDEX,
        }

    def status_line(self) -> str:
        s = self.status()
        return (
            f"tts={s['tts_engine']}/{s['tts_voice']} "
            f"stt={s['stt_backend']} barge_in={s['barge_in']} "
            f"whisper_loaded={s['whisper_loaded']}"
        )

    def _init_tts(self):
        if config.TTS_ENGINE == "none":
            return
        if config.TTS_ENGINE in ("edge", "auto"):
            try:
                import edge_tts  # noqa: F401
                import pygame  # noqa: F401
                self.tts_ok = True
                self.tts_engine_name = "edge"
                return
            except ImportError as e:
                logger.warning("edge-tts/pygame unavailable: %s", e)
        try:
            import pyttsx3  # noqa: F401
            self.tts_ok = True
            self.tts_engine_name = "pyttsx3"
        except ImportError:
            logger.warning("No TTS available")

    def _init_stt_probe(self):
        try:
            import speech_recognition as sr  # noqa: F401
        except ImportError:
            logger.warning("SpeechRecognition not installed — STT off")
            return

        if config.USE_WHISPER:
            try:
                import whisper  # noqa: F401
                self.stt_backend = "whisper"
                self.stt_ok = True
                if not self._lazy_whisper:
                    self._ensure_whisper()
                return
            except ImportError:
                logger.warning("whisper not installed — Google STT fallback")

        if self._can_google_stt():
            self.stt_backend = "google"
            self.stt_ok = True

    def _can_google_stt(self) -> bool:
        try:
            import speech_recognition as sr  # noqa: F401
            return True
        except ImportError:
            return False

    def _ensure_whisper(self) -> bool:
        if self._whisper is not None:
            return True
        try:
            import whisper
            device = config.WHISPER_DEVICE
            if device == "auto":
                try:
                    import torch
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                except ImportError:
                    device = "cpu"
            self._whisper_device = device
            logger.info("Loading Whisper model=%s device=%s …", config.WHISPER_MODEL, device)
            self._whisper = whisper.load_model(config.WHISPER_MODEL, device=device)
            self.stt_backend = "whisper"
            self.stt_ok = True
            return True
        except Exception as e:
            logger.warning("Whisper load failed: %s", e)
            if self._can_google_stt():
                self.stt_backend = "google"
                self.stt_ok = True
            return False

    @staticmethod
    def list_microphones() -> List[Tuple[int, str]]:
        try:
            import speech_recognition as sr
            return list(enumerate(sr.Microphone.list_microphone_names()))
        except Exception as e:
            logger.warning("list mics failed: %s", e)
            return []

    def stop_speaking(self):
        self._stop_speak.set()
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

    def speak(self, text: str, max_chars: int = 900) -> bool:
        if not text or not self.tts_ok:
            return False
        text = self._clean_for_speech(text, max_chars)
        if not text:
            return False
        self._stop_speak.clear()
        self.last_barge_in = False
        with self._speak_lock:
            try:
                if self.tts_engine_name == "edge":
                    self._speak_edge(text)
                else:
                    self._speak_pyttsx3(text)
                return True
            except Exception as e:
                logger.warning("TTS failed (%s): %s", self.tts_engine_name, e)
                if self.tts_engine_name == "edge":
                    try:
                        self._speak_pyttsx3(text)
                        self.tts_engine_name = "pyttsx3"
                        return True
                    except Exception as e2:
                        logger.warning("pyttsx3 fallback failed: %s", e2)
                return False

    def speak_async(self, text: str, max_chars: int = 900):
        threading.Thread(
            target=self.speak, args=(text, max_chars), name="seven-tts", daemon=True
        ).start()

    @staticmethod
    def _clean_for_speech(text: str, max_chars: int) -> str:
        text = text.strip()
        text = re.sub(r"```[\s\S]*?```", " ", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"[#*_>]{1,3}", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > max_chars:
            text = text[:max_chars].rsplit(" ", 1)[0] + "…"
        return text

    def _barge_in_watcher(self):
        """Background: stop TTS if user speaks over her."""
        if not self.barge_in_enabled:
            return
        try:
            import speech_recognition as sr
            import audioop
            r = sr.Recognizer()
            mic_kwargs = {}
            if config.MIC_INDEX is not None:
                mic_kwargs["device_index"] = int(config.MIC_INDEX)
            with sr.Microphone(**mic_kwargs) as source:
                r.adjust_for_ambient_noise(source, duration=0.25)
                baseline = 150
                # sample ambient
                try:
                    audio = r.listen(source, timeout=0.3, phrase_time_limit=0.3)
                    baseline = max(audioop.rms(audio.frame_data, audio.sample_width), 100)
                except Exception:
                    pass
                threshold = baseline * float(getattr(config, "BARGE_IN_SENSITIVITY", 3.5))
                while not self._stop_speak.is_set():
                    try:
                        import pygame
                        if not pygame.mixer.get_init() or not pygame.mixer.music.get_busy():
                            break
                    except Exception:
                        break
                    try:
                        chunk = r.listen(source, timeout=0.25, phrase_time_limit=0.4)
                        rms = audioop.rms(chunk.frame_data, chunk.sample_width)
                        if rms > threshold:
                            logger.info("Barge-in detected rms=%s thr=%s", rms, threshold)
                            self.last_barge_in = True
                            self.stop_speaking()
                            break
                    except sr.WaitTimeoutError:
                        continue
                    except Exception:
                        break
        except Exception as e:
            logger.debug("barge-in watcher unavailable: %s", e)

    def _speak_edge(self, text: str):
        import edge_tts
        import pygame

        voice = getattr(config, "EDGE_TTS_VOICE", "en-US-AvaNeural")
        rate = getattr(config, "EDGE_TTS_RATE", "+0%")
        pitch = getattr(config, "EDGE_TTS_PITCH", "+0Hz")

        async def _run():
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            fd = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            path = fd.name
            fd.close()
            await communicate.save(path)
            return path

        try:
            path = asyncio.run(_run())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                path = loop.run_until_complete(_run())
            finally:
                loop.close()

        watcher = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            if self.barge_in_enabled:
                watcher = threading.Thread(
                    target=self._barge_in_watcher, name="seven-barge", daemon=True
                )
                watcher.start()
            while pygame.mixer.music.get_busy():
                if self._stop_speak.is_set():
                    pygame.mixer.music.stop()
                    break
                pygame.time.wait(50)
        finally:
            try:
                Path(path).unlink(missing_ok=True)
            except Exception:
                pass

    def _speak_pyttsx3(self, text: str):
        import pyttsx3
        engine = pyttsx3.init()
        try:
            voices = engine.getProperty("voices") or []
            # Prefer female-looking voice names
            for v in voices:
                name = (getattr(v, "name", "") or "").lower()
                if any(x in name for x in ("zira", "female", "eva", "hazel", "susan")):
                    engine.setProperty("voice", v.id)
                    break
            engine.setProperty("rate", int(getattr(config, "DEFAULT_SPEECH_RATE", 170)))
        except Exception:
            pass
        engine.say(text)
        engine.runAndWait()

    def listen_once(
        self,
        timeout: int = 6,
        phrase_time_limit: int = 20,
        calibrate: float = 0.4,
    ) -> Optional[str]:
        if not self.stt_ok and not self._can_google_stt():
            return None
        try:
            import speech_recognition as sr
        except ImportError:
            return None

        r = sr.Recognizer()
        r.dynamic_energy_threshold = True
        mic_kwargs = {}
        if config.MIC_INDEX is not None:
            mic_kwargs["device_index"] = int(config.MIC_INDEX)

        try:
            with sr.Microphone(**mic_kwargs) as source:
                if calibrate > 0:
                    r.adjust_for_ambient_noise(source, duration=calibrate)
                logger.info("Listening…")
                audio = r.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )
        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            logger.warning("Mic capture failed: %s", e)
            return None

        if config.USE_WHISPER:
            if self._ensure_whisper() and self._whisper is not None:
                text = self._transcribe_whisper(audio)
                if text:
                    return text
        return self._transcribe_google(audio, r)

    def _transcribe_whisper(self, audio) -> Optional[str]:
        path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio.get_wav_data())
                path = f.name
            kwargs = {"fp16": self._whisper_device == "cuda"}
            lang = getattr(config, "WHISPER_LANGUAGE", "en")
            if lang:
                kwargs["language"] = lang
            result = self._whisper.transcribe(path, **kwargs)
            text = (result.get("text") or "").strip()
            return self._filter_hallucination(text, result)
        except Exception as e:
            logger.warning("Whisper transcribe failed: %s", e)
            return None
        finally:
            if path:
                try:
                    Path(path).unlink(missing_ok=True)
                except Exception:
                    pass

    def _transcribe_google(self, audio, recognizer) -> Optional[str]:
        try:
            text = recognizer.recognize_google(audio)
            return (text or "").strip() or None
        except Exception as e:
            logger.info("Google STT: %s", e)
            return None

    @staticmethod
    def _filter_hallucination(text: str, result: dict) -> Optional[str]:
        if not text:
            return None
        low = text.strip().lower().strip(" .!?")
        if low in _HALLUCINATIONS or text.strip() in _HALLUCINATIONS:
            return None
        segs = result.get("segments") or []
        if segs:
            avg_nsp = sum(s.get("no_speech_prob", 0) for s in segs) / max(len(segs), 1)
            if avg_nsp > 0.7 and len(text) < 12:
                return None
        return text
