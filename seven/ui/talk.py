"""
Talk with Seven — the real product UX.

You speak. She listens. She speaks. She has free will between turns.
No /work, no /listen required.
"""
from __future__ import annotations

import logging
import sys
import threading
import time

from seven import config, __version__
from seven.agent.loop import Seven

logger = logging.getLogger("seven.talk")


def run_talk(
    agent: Seven | None = None,
    listen_timeout: float | None = None,
    phrase_limit: float | None = None,
):
    """
    Continuous conversation loop.
    - Listen for user speech
    - Reply with voice + print
    - Between silences, free will may invent goals, work, or speak first
    """
    config.ENABLE_VOICE = True
    config.ENABLE_FREEWILL = True

    own = agent is None
    agent = agent or Seven()
    if own:
        agent.start_heartbeat()

    from seven.voice.io import VoiceIO

    voice = VoiceIO(lazy_whisper=True)
    listen_timeout = float(listen_timeout or getattr(config, "TALK_LISTEN_TIMEOUT", 12))
    phrase_limit = float(phrase_limit or getattr(config, "TALK_PHRASE_LIMIT", 25))

    # Free will speech during heartbeat goes out the speaker
    def _utter(text: str):
        if not text:
            return
        print(f"\n{config.BOT_NAME}> {text}\n")
        if voice.tts_ok:
            voice.speak(text)

    agent.freewill.on_utter = _utter

    print("=" * 60)
    print(f"  {config.BOT_NAME}  —  talk mode  —  v{__version__}")
    print("  Just speak. She listens and talks back.")
    print("  She has free will: goals and initiative without commands.")
    print("  Say 'goodbye' or 'stop talking' to end. Ctrl+C also works.")
    print(f"  {voice.status_line()}")
    if not voice.stt_ok:
        print("  WARNING: speech recognition unavailable — install Whisper/PyAudio")
        print("  Falling back to typing (still no slash commands required).")
    if not voice.tts_ok:
        print("  WARNING: TTS unavailable — replies print only")
    print("=" * 60)

    # Opening line from free will if brain up
    try:
        agent.refresh_living_state()
        mode = (agent.living.self_state.get("state") or {}).get("mode")
        if mode != "degraded_no_llm" and voice.tts_ok:
            hello = None
            try:
                hello = agent.brain.generate(
                    "You are Seven. The user just opened talk mode. "
                    "Greet them in ONE short natural sentence as a companion with free will. "
                    "No menu. No commands. No 'how can I help you today' corporate tone.",
                    system="Seven. Warm, brief, real.",
                    temperature=0.8,
                    max_tokens=40,
                )
            except Exception:
                hello = f"Hey. I'm {config.BOT_NAME}. I'm here — talk whenever you want."
            hello = (hello or "").strip() or f"Hey. I'm {config.BOT_NAME}."
            print(f"\n{config.BOT_NAME}> {hello}\n")
            voice.speak(hello)
            agent.memory.add_message("assistant", hello, meta={"talk_open": True})
    except Exception:
        logger.exception("opening line failed")

    goodbye_words = (
        "goodbye", "good bye", "bye seven", "stop talking", "go to sleep",
        "that's all", "thats all", "exit talk", "quit talk",
    )

    try:
        while True:
            # ── listen ─────────────────────────────────────────────
            user_text = None
            if voice.stt_ok or voice._can_google_stt():
                print(f"[listening…]")
                user_text = voice.listen_once(
                    timeout=int(listen_timeout),
                    phrase_time_limit=int(phrase_limit),
                )
            if not user_text:
                # silence: free will may act / speak
                try:
                    decision = agent.freewill.decide(
                        idle_min=(time.time() - agent.last_user_ts) / 60.0
                    )
                    if decision.action in ("speak", "work", "invent_goal"):
                        utter = agent.freewill.execute(decision)
                        if utter:
                            _utter(utter)
                    else:
                        # brief pause then listen again
                        time.sleep(0.4)
                except Exception:
                    logger.exception("freewill during silence")
                    time.sleep(0.5)
                continue

            print(f"{config.USER_NAME}> {user_text}")
            low = user_text.lower().strip()
            if any(g in low for g in goodbye_words) or low in ("bye", "goodbye", "exit", "quit"):
                farewell = "Alright. I'll still be around if the daemon's running. Later."
                print(f"\n{config.BOT_NAME}> {farewell}\n")
                if voice.tts_ok:
                    voice.speak(farewell)
                break

            # ── think + act + speak ───────────────────────────────
            print(f"[{config.BOT_NAME} thinking…]")
            try:
                reply = agent.handle(user_text)
            except Exception as e:
                reply = f"I hit a snag: {e}"
                logger.exception("talk handle failed")

            if reply == "__QUIT__":
                break
            if not reply:
                reply = "…"

            print(f"\n{config.BOT_NAME}> {reply}\n")
            if voice.tts_ok:
                voice.speak(reply)

    except KeyboardInterrupt:
        print("\n[talk ended]")
    finally:
        agent.freewill.on_utter = None
        try:
            voice.stop_speaking()
        except Exception:
            pass
        if own:
            agent.shutdown()


def main():
    run_talk()


if __name__ == "__main__":
    main()
