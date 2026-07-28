from __future__ import annotations

import sys
import types

import pytest

from seven_gateway.transcription import (
    DisabledTranscriber,
    TranscriptionUnavailable,
    WhisperTranscriber,
)


def test_disabled_transcriber_is_explicit():
    with pytest.raises(TranscriptionUnavailable, match="transcription_unavailable"):
        DisabledTranscriber().transcribe(b"audio")


def test_whisper_is_lazy_local_cpu_only_and_bounded_to_one_worker(tmp_path, monkeypatch):
    calls = {}

    class Segment:
        def __init__(self, text):
            self.text = text

    class Info:
        language = "en"
        language_probability = 0.97

    class FakeWhisperModel:
        def __init__(self, model, **kwargs):
            calls["init"] = (model, kwargs)

        def transcribe(self, audio, **kwargs):
            calls["audio"] = audio.read()
            calls["transcribe"] = kwargs
            return iter([Segment(" hello "), Segment("world")]), Info()

    monkeypatch.setitem(
        sys.modules,
        "faster_whisper",
        types.SimpleNamespace(WhisperModel=FakeWhisperModel),
    )
    transcriber = WhisperTranscriber("tiny.en", tmp_path, 2)
    result = transcriber.transcribe(b"RIFFfakeWAVE")

    assert result["transcript"] == "hello world"
    assert result["language"] == "en"
    model, init = calls["init"]
    assert model == "tiny.en"
    assert init["device"] == "cpu"
    assert init["compute_type"] == "int8"
    assert init["cpu_threads"] == 2
    assert init["num_workers"] == 1
    assert init["local_files_only"] is True
    assert calls["transcribe"]["vad_filter"] is True
    assert calls["audio"] == b"RIFFfakeWAVE"
