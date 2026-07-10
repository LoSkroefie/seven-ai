"""Generate short previews of female neural voices into ~/.seven/voice_previews/"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import edge_tts

from seven import config

VOICES = [
    "en-US-AvaNeural",
    "en-US-EmmaNeural",
    "en-US-JennyNeural",
    "en-US-MichelleNeural",
    "en-GB-SoniaNeural",
    "en-AU-NatashaNeural",
]

SAMPLE = (
    "Hi, I'm Seven. I'm right here with you — warm, clear, and ready to help. "
    "Just talk to me."
)


async def main():
    out_dir = config.DATA_DIR / "voice_previews"
    out_dir.mkdir(parents=True, exist_ok=True)
    for v in VOICES:
        path = out_dir / f"{v}.mp3"
        print("rendering", v)
        communicate = edge_tts.Communicate(SAMPLE, v, rate="-5%", pitch="+2Hz")
        await communicate.save(str(path))
        print(" ", path)
    print("Default Seven voice:", config.EDGE_TTS_VOICE)
    print("Done. Play the mp3 files to pick a favorite; set SEVEN_EDGE_VOICE=en-US-AvaNeural")


if __name__ == "__main__":
    asyncio.run(main())
