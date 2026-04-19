"""
Enhanced voice input using OpenAI Whisper for better accuracy.

v3.2.20 fixes:
- One-shot ambient calibration at init (configurable via WHISPER_RECALIBRATE_EACH_LISTEN)
- phrase_time_limit on every listen so a single long utterance can't block forever
- no_speech_prob rejection to filter Whisper's silence hallucinations
  (known ones: "you", "thanks for watching", "Bye.", "." — annoying on quiet mics)
- Device auto-selection: uses CUDA when available, falls back to CPU
- Configurable microphone device index via WHISPER_MIC_INDEX
- Returns (text, confidence) tuple internally so callers can decide what to do
  with low-confidence transcripts; public listen() still returns Optional[str]
"""
import time
import logging
from typing import Optional, Tuple

import whisper
import numpy as np
import speech_recognition as sr

import config

logger = logging.getLogger("WhisperVoice")


def _resolve_device(pref: str) -> str:
    """Return a concrete torch device string ('cuda' or 'cpu')."""
    if pref == "cpu":
        return "cpu"
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


class WhisperVoiceManager:
    """Speech recognition using local OpenAI Whisper."""

    def __init__(self, model_size: Optional[str] = None, device_index: Optional[int] = None):
        self.model_size = model_size or getattr(config, "WHISPER_MODEL_SIZE", "base")
        self.device_pref = getattr(config, "WHISPER_DEVICE", "auto")
        self.device = _resolve_device(self.device_pref)
        self.language = getattr(config, "WHISPER_LANGUAGE", "en")
        self.mic_index = device_index if device_index is not None else getattr(
            config, "WHISPER_MIC_INDEX", None
        )
        self.no_speech_threshold = float(getattr(config, "WHISPER_NO_SPEECH_THRESHOLD", 0.55))
        self.listen_timeout = int(getattr(config, "WHISPER_LISTEN_TIMEOUT", 10))
        self.phrase_limit = int(getattr(config, "WHISPER_PHRASE_LIMIT", 15))
        self.recalibrate_each = bool(getattr(config, "WHISPER_RECALIBRATE_EACH_LISTEN", False))

        self.model = None
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self._calibrated = False

        t0 = time.time()
        logger.info(
            f"[WHISPER] loading model '{self.model_size}' on device '{self.device}'..."
        )
        try:
            self.model = whisper.load_model(self.model_size, device=self.device)
            dt = time.time() - t0
            logger.info(f"[WHISPER] loaded in {dt:.1f}s (device={self.device})")
        except Exception as e:
            logger.error(f"[WHISPER] load failed: {e}")
            logger.info("[WHISPER] falling back to Google Speech Recognition")
            self.model = None

        # One-shot mic calibration so listen() is fast
        try:
            self._calibrate_once()
        except Exception as e:
            logger.warning(f"[WHISPER] init calibration failed, will calibrate per-listen: {e}")

    # ---------------------------------------------------------------- internals

    def _mic(self):
        """Instantiate a Microphone with the configured device index."""
        if self.mic_index is not None:
            return sr.Microphone(device_index=self.mic_index)
        return sr.Microphone()

    def _calibrate_once(self):
        with self._mic() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            self.recognizer.energy_threshold = max(self.recognizer.energy_threshold, 300)
            self._calibrated = True
            logger.info(
                f"[WHISPER] calibrated — energy_threshold={self.recognizer.energy_threshold:.0f}"
            )

    # -------------------------------------------------------------------- listen

    def listen(self, timeout: Optional[int] = None) -> Optional[str]:
        """Capture one phrase from the mic and transcribe it.

        Returns None if nothing spoken, audio was silence, or transcription failed.
        """
        text, conf = self._listen_transcribe(timeout)
        if text is None:
            return None
        if conf is not None and conf < (1.0 - self.no_speech_threshold):
            # Whisper itself thinks this was mostly silence — drop it
            logger.debug(
                f"[WHISPER] rejecting low-confidence: conf={conf:.2f} text={text[:60]!r}"
            )
            return None
        return text

    def _listen_transcribe(self, timeout: Optional[int]) -> Tuple[Optional[str], Optional[float]]:
        to = timeout if timeout is not None else self.listen_timeout

        if self.model is None:
            text = self._listen_fallback(to)
            return (text, None)

        try:
            with self._mic() as source:
                if self.recalibrate_each or not self._calibrated:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                try:
                    audio = self.recognizer.listen(
                        source, timeout=to, phrase_time_limit=self.phrase_limit
                    )
                except sr.WaitTimeoutError:
                    return (None, None)
        except OSError as e:
            logger.warning(f"[WHISPER] mic unavailable: {e}")
            return (None, None)

        try:
            raw = audio.get_wav_data(convert_rate=16000, convert_width=2)
            arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            if arr.size == 0 or np.max(np.abs(arr)) < 0.005:
                # Near-silence — don't even feed to the model
                return (None, None)

            use_fp16 = (self.device == "cuda")
            kwargs = {"fp16": use_fp16}
            if self.language:
                kwargs["language"] = self.language

            t0 = time.time()
            result = self.model.transcribe(arr, **kwargs)
            dt = time.time() - t0

            text = str(result.get("text", "")).strip()
            segs = result.get("segments") or [{}]
            no_speech = float(segs[0].get("no_speech_prob", 0.5))
            conf = max(0.0, 1.0 - no_speech)

            if not text:
                return (None, conf)

            logger.debug(f"[WHISPER] {dt:.2f}s  conf={conf:.2f}  text={text!r}")
            return (text, conf)
        except Exception as e:
            logger.error(f"[WHISPER] transcribe failed: {e}")
            return (self._listen_fallback(to), None)

    def _listen_fallback(self, timeout: int) -> Optional[str]:
        """Google fallback only used when Whisper model failed to load."""
        try:
            with self._mic() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=self.phrase_limit
                )
                return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            logger.warning(f"[WHISPER fallback] Google unreachable: {e}")
            return None
        except Exception as e:
            logger.debug(f"[WHISPER fallback] error: {e}")
            return None
