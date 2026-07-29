from __future__ import annotations

import asyncio


class SpeechSynthesisUnavailable(RuntimeError):
    pass


class DisabledSynthesizer:
    def synthesize(self, _text: str) -> bytes:
        raise SpeechSynthesisUnavailable("tts_unavailable")


class EdgeSynthesizer:
    """Bounded Microsoft neural speech adapter used by the owner gateway."""

    def __init__(
        self,
        voice: str,
        rate: str,
        pitch: str,
        timeout_seconds: int,
        audio_limit_bytes: int,
    ):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.timeout_seconds = timeout_seconds
        self.audio_limit_bytes = audio_limit_bytes

    async def _render(self, text: str) -> bytes:
        try:
            import edge_tts
        except ImportError as exc:
            raise SpeechSynthesisUnavailable("tts_dependency_missing") from exc

        audio = bytearray()
        communicate = edge_tts.Communicate(
            text,
            self.voice,
            rate=self.rate,
            pitch=self.pitch,
        )
        async for chunk in communicate.stream():
            if chunk.get("type") != "audio":
                continue
            audio.extend(chunk.get("data") or b"")
            if len(audio) > self.audio_limit_bytes:
                raise SpeechSynthesisUnavailable("tts_audio_too_large")
        if not audio:
            raise SpeechSynthesisUnavailable("tts_empty_audio")
        return bytes(audio)

    def synthesize(self, text: str) -> bytes:
        async def bounded() -> bytes:
            try:
                return await asyncio.wait_for(
                    self._render(text),
                    timeout=self.timeout_seconds,
                )
            except asyncio.TimeoutError as exc:
                raise SpeechSynthesisUnavailable("tts_timeout") from exc

        return asyncio.run(bounded())
