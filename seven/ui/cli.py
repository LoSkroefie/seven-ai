"""Interactive CLI for Seven Real (text + optional push-to-talk voice)."""
from __future__ import annotations

import sys

from seven import config
from seven.agent.loop import Seven


def run_cli(voice: bool = False, agent: Seven | None = None):
    print("=" * 60)
    print(f"  {config.BOT_NAME} Real  —  local agent  —  L4 autonomy")
    print(f"  model={config.OLLAMA_MODEL}  provider={config.LLM_PROVIDER}")
    print(f"  data={config.DATA_DIR}")
    print("  Type /help for commands.")
    if voice or config.ENABLE_VOICE:
        print("  Voice ON: empty line or /listen = push-to-talk; replies spoken.")
    print("=" * 60)

    own_agent = agent is None
    agent = agent or Seven()
    if own_agent:
        agent.start_heartbeat()

    voice_io = None
    speak_replies = False
    if voice or config.ENABLE_VOICE:
        config.ENABLE_VOICE = True
        from seven.voice.io import VoiceIO
        voice_io = VoiceIO(lazy_whisper=True)
        speak_replies = voice_io.tts_ok
        print(f"  {voice_io.status_line()}")
        if not voice_io.stt_ok:
            print("  STT unavailable — text still works. See docs/VOICE.md")
        mics = voice_io.list_microphones()
        if mics and config.MIC_INDEX is None:
            print(f"  mics found: {len(mics)} (set SEVEN_MIC_INDEX if wrong one)")

    try:
        while True:
            try:
                prompt = f"{config.USER_NAME}> "
                user = input(prompt).strip()
            except EOFError:
                break

            # Push-to-talk: empty line or /listen /mic
            if voice_io and (user == "" or user.lower() in ("/listen", "/mic", "/ptt")):
                if not (voice_io.stt_ok or voice_io._can_google_stt()):
                    print("[voice] STT not available")
                    continue
                print("[listening — speak now…]")
                heard = voice_io.listen_once()
                if not heard:
                    print("[voice] (no speech / timeout)")
                    continue
                print(f"{config.USER_NAME}> {heard}")
                user = heard
            elif not user:
                continue

            # Local voice toggles
            low = user.lower()
            if low == "/voice on" and voice_io is None:
                from seven.voice.io import VoiceIO
                config.ENABLE_VOICE = True
                voice_io = VoiceIO(lazy_whisper=True)
                speak_replies = voice_io.tts_ok
                print(voice_io.status_line())
                continue
            if low == "/voice off":
                speak_replies = False
                print("Voice speak replies off (STT still via /listen if loaded)")
                continue
            if low == "/speak on":
                speak_replies = True
                print("Speak replies on")
                continue
            if low == "/speak off":
                speak_replies = False
                print("Speak replies off")
                continue
            if low == "/mics" and voice_io:
                for i, name in voice_io.list_microphones():
                    print(f"  [{i}] {name}")
                continue
            if low == "/voice" and voice_io:
                print(voice_io.status_line())
                continue

            reply = agent.handle(user)
            if reply == "__QUIT__":
                print("Goodbye.")
                break
            print(f"\n{config.BOT_NAME}> {reply}\n")
            if voice_io and speak_replies and voice_io.tts_ok and not reply.startswith("Seven Real"):
                # skip speaking pure status dumps unless short
                if not (reply.startswith("tier=") or "tool_tier=" in reply[:80]):
                    voice_io.speak(reply)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        if voice_io:
            voice_io.stop_speaking()
        if own_agent:
            agent.shutdown()


def main(argv=None):
    argv = argv or sys.argv[1:]
    voice = "--voice" in argv
    run_cli(voice=voice)


if __name__ == "__main__":
    main()
