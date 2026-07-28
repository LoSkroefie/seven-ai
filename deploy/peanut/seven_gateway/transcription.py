from __future__ import annotations

import io
import logging
import threading
from pathlib import Path

LOGGER = logging.getLogger("seven.gateway.transcription")


class TranscriptionUnavailable(RuntimeError):
    """A deliberately content-free local transcription failure."""


class DisabledTranscriber:
    def transcribe(self, _audio: bytes) -> dict:
        raise TranscriptionUnavailable("transcription_unavailable")


class WhisperTranscriber:
    """Lazy, CPU-only, one-at-a-time Faster Whisper transcription."""

    def __init__(self, model: str, download_root: Path, threads: int):
        self.model_name = model
        self.download_root = download_root
        self.threads = max(1, int(threads))
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        if self._model is not None:
            return self._model
        try:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8",
                cpu_threads=self.threads,
                num_workers=1,
                download_root=str(self.download_root),
                local_files_only=True,
            )
        except Exception:
            LOGGER.exception("local Whisper model could not be loaded")
            raise TranscriptionUnavailable("transcription_unavailable") from None
        return self._model

    def transcribe(self, audio: bytes) -> dict:
        if not audio:
            raise TranscriptionUnavailable("empty_audio")
        with self._lock:
            try:
                segments, info = self._load().transcribe(
                    io.BytesIO(audio),
                    beam_size=1,
                    best_of=1,
                    vad_filter=True,
                    condition_on_previous_text=False,
                )
                text = " ".join(
                    segment.text.strip() for segment in segments if segment.text.strip()
                ).strip()
            except TranscriptionUnavailable:
                raise
            except Exception:
                LOGGER.exception("local transcription failed")
                raise TranscriptionUnavailable("transcription_failed") from None
        if not text:
            raise TranscriptionUnavailable("no_speech_detected")
        return {
            "transcript": text,
            "language": getattr(info, "language", None),
            "language_probability": getattr(info, "language_probability", None),
        }
