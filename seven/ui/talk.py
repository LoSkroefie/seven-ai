"""
Talk with Seven — the real product UX.

You converse. She listens (mic or quiet text). She answers.
She has free will between turns — no /work, no /listen.
Quiet mode: type softly-friendly (no TTS) when others sleep.
"""
from __future__ import annotations

import logging
import os
import time

from seven import config, __version__
from seven.agent.loop import Seven

logger = logging.getLogger("seven.talk")


def run_talk(
    agent: Seven | None = None,
    listen_timeout: float | None = None,
    phrase_limit: float | None = None,
    quiet: bool | None = None,
):
    """
    Companion loop.
    - quiet=True: type to talk, print only (no mic/speaker) — free will still runs
    - quiet=False: voice in/out when available
    """
    config.ENABLE_FREEWILL = True

    # Quiet: env, explicit flag, or auto when SEVEN_QUIET=1
    if quiet is None:
        quiet = os.getenv("SEVEN_QUIET", "0") == "1"

    own = agent is None
    agent = agent or Seven()
    if own:
        agent.start_heartbeat()

    voice = None
    use_mic = False
    use_tts = False

    if not quiet:
        config.ENABLE_VOICE = True
        try:
            from seven.voice.io import VoiceIO
            voice = VoiceIO(lazy_whisper=True)
            use_mic = bool(voice.stt_ok or voice._can_google_stt())
            use_tts = bool(voice.tts_ok)
        except Exception as e:
            logger.warning("Voice init failed, quiet fallback: %s", e)
            quiet = True

    listen_timeout = float(listen_timeout or getattr(config, "TALK_LISTEN_TIMEOUT", 12))
    phrase_limit = float(phrase_limit or getattr(config, "TALK_PHRASE_LIMIT", 25))

    def _utter(text: str, speak: bool = True):
        if not text:
            return
        print(f"\n{config.BOT_NAME}> {text}\n")
        if speak and use_tts and voice and not quiet:
            try:
                voice.speak(text)
            except Exception:
                logger.exception("TTS failed")

    agent.freewill.on_utter = lambda t: _utter(t, speak=not quiet)

    mode_label = "QUIET (type — no mic/speaker)" if quiet or not use_mic else "VOICE"
    print("=" * 60)
    print(f"  {config.BOT_NAME}  —  companion  —  v{__version__}")
    print(f"  Mode: {mode_label}")
    print("  Just talk (or type). No slash commands.")
    print("  Free will: she may invent goals and act between turns.")
    print("  Say 'goodbye' to end. Ctrl+C works.")
    if voice and not quiet:
        print(f"  {voice.status_line()}")
        if not use_mic:
            print("  Mic unavailable → type instead (still free will).")
        if not use_tts:
            print("  TTS unavailable → text only.")
    if quiet:
        print("  Quiet: set SEVEN_QUIET=0 later for voice.")
    print("=" * 60)

    # Opening line
    try:
        agent.refresh_living_state()
        mode = (agent.living.self_state.get("state") or {}).get("mode")
        hello = f"Hey. I'm {config.BOT_NAME}. I'm here."
        if mode != "degraded_no_llm":
            try:
                hello = agent.brain.generate(
                    "You are Seven. User just opened companion mode. "
                    "ONE short natural sentence. Free will. No menus, no commands, "
                    "no corporate 'how can I help'.",
                    system="Seven. Warm, brief, real.",
                    temperature=0.8,
                    max_tokens=40,
                ) or hello
            except Exception as e:
                logger.warning("greeting LLM failed: %s", e)
                hello = f"Hey. I'm {config.BOT_NAME}. Brain's a bit slow but I'm here."
        else:
            hello = (
                f"Hey. I'm {config.BOT_NAME}. Ollama isn't running — "
                "start it and I'll think properly. You can still type."
            )
        hello = (hello or "").strip().strip('"')
        _utter(hello, speak=not quiet)
        agent.memory.add_message("assistant", hello, meta={"talk_open": True})
    except Exception:
        logger.exception("opening line failed")

    goodbye_words = (
        "goodbye", "good bye", "bye seven", "stop talking", "go to sleep",
        "that's all", "thats all", "exit talk", "quit talk",
    )

    # Freewill between typed turns: shorter idle for quiet testing
    freewill_check_every = 3  # after N empty/timeouts attempt freewill
    silence_streak = 0

    try:
        while True:
            user_text = None

            if not quiet and use_mic and voice:
                print("[listening…]")
                user_text = voice.listen_once(
                    timeout=int(listen_timeout),
                    phrase_time_limit=int(phrase_limit),
                )
                if not user_text:
                    silence_streak += 1
                    user_text = _freewill_or_none(agent, silence_streak, freewill_check_every)
                    if user_text is None:
                        # freewill may have spoken via on_utter
                        continue
                    # freewill returned nothing to treat as user — already uttered
                    continue
                silence_streak = 0
            else:
                # Quiet / no mic: natural typing, empty line = free will tick
                try:
                    user_text = input(f"{config.USER_NAME}> ").strip()
                except EOFError:
                    break
                if not user_text:
                    silence_streak += 1
                    _run_freewill_tick(agent)
                    continue
                silence_streak = 0

            print(f"{config.USER_NAME}> {user_text}")
            low = user_text.lower().strip()
            if any(g in low for g in goodbye_words) or low in ("bye", "goodbye", "exit", "quit"):
                farewell = "Alright. I'll keep existing in the background if the daemon's on. Later."
                _utter(farewell, speak=not quiet)
                break

            print(f"[{config.BOT_NAME}…]")
            try:
                reply = agent.handle(user_text)
            except Exception as e:
                reply = f"I hit a snag: {e}"
                logger.exception("talk handle failed")

            if reply == "__QUIT__":
                break
            if not reply:
                reply = "…"

            _utter(reply, speak=not quiet)

    except KeyboardInterrupt:
        print("\n[ended]")
    finally:
        agent.freewill.on_utter = None
        if voice:
            try:
                voice.stop_speaking()
            except Exception:
                pass
        if own:
            agent.shutdown()


def _run_freewill_tick(agent: Seven):
    try:
        decision = agent.freewill.decide(
            idle_min=(time.time() - agent.last_user_ts) / 60.0
        )
        # For quiet interactive use, lower barriers: treat empty line as "I'm idle, go"
        if decision.action in ("wait", "rest"):
            # nudge: force invent or speak if truly idle and brain ok
            mode = (agent.living.self_state.get("state") or {}).get("mode")
            if mode != "degraded_no_llm":
                goals = agent.memory.active_goals()
                if not goals:
                    decision = type(decision)("invent_goal", "user idle — I choose a goal")
                else:
                    decision = type(decision)(
                        "work",
                        "user idle — continue my goal",
                        goal_id=int(goals[0]["id"]),
                    )
        utter = agent.freewill.execute(decision)
        if utter and agent.freewill.on_utter:
            agent.freewill.on_utter(utter)
        elif decision.action == "work":
            # still surface that she worked
            note = f"(I worked on my own: {decision.reason})"
            if agent.freewill.on_utter:
                agent.freewill.on_utter(note)
    except Exception:
        logger.exception("freewill tick failed")


def _freewill_or_none(agent: Seven, silence_streak: int, every: int):
    """During voice silence, occasionally freewill. Always None as user text."""
    if silence_streak % every == 0:
        _run_freewill_tick(agent)
    else:
        time.sleep(0.3)
    return None


def main():
    run_talk()


if __name__ == "__main__":
    main()
