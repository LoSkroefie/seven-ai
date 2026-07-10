"""
Minimal desktop chat for Seven Real.
Only calls Seven.handle() — no parallel personality stack.
Optional voice: push-to-talk Mic + Speak replies checkbox.
"""
from __future__ import annotations

import logging
import queue
import threading
import tkinter as tk
from tkinter import scrolledtext
from typing import Optional

from seven import config
from seven.agent.loop import Seven

logger = logging.getLogger("seven.ui")


class SevenChatApp:
    def __init__(
        self,
        agent: Optional[Seven] = None,
        start_heartbeat: bool = True,
        enable_voice: bool = False,
    ):
        self.agent = agent or Seven()
        if start_heartbeat:
            self.agent.start_heartbeat()

        self.voice_io = None
        self._speak_var = tk.BooleanVar(value=False)
        if enable_voice or config.ENABLE_VOICE:
            self._init_voice()

        self.root = tk.Tk()
        self.root.title(f"{config.BOT_NAME} Real — local agent")
        self.root.geometry("740x580")
        self.root.minsize(480, 360)

        self._work_q: queue.Queue = queue.Queue()
        self._busy = False
        self._tray = None
        self._tray_thread: Optional[threading.Thread] = None
        self._closing = False

        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_request)
        self.root.after(100, self._poll_results)

        msg = (
            f"{config.BOT_NAME} Real ready. Tools tier={self.agent.tools.tier}. "
            f"Type a message or /status /tools /help."
        )
        if self.voice_io:
            msg += f" Voice: {self.voice_io.status_line()}. Mic = push-to-talk."
        else:
            msg += " Close → tray if available."
        self._append_system(msg)
        # Free will utterances appear in chat + speaker
        if self.voice_io:
            def _fw_utter(text: str):
                def ui():
                    self._append(config.BOT_NAME, text, "assistant")
                    if self._speak_var.get() and self.voice_io and self.voice_io.tts_ok:
                        self.voice_io.speak_async(text)
                self.root.after(0, ui)
            self.agent.freewill.on_utter = _fw_utter

    def _init_voice(self):
        try:
            from seven.voice.io import VoiceIO
            config.ENABLE_VOICE = True
            config.ENABLE_FREEWILL = True
            self.voice_io = VoiceIO(lazy_whisper=True)
            self._speak_var = tk.BooleanVar(value=True)  # always speak in companion mode
        except Exception as e:
            logger.warning("Voice init failed: %s", e)
            self.voice_io = None

    def _build(self):
        top = tk.Frame(self.root)
        top.pack(fill=tk.X, padx=8, pady=6)

        tk.Label(top, text=config.BOT_NAME, font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="idle")
        tk.Label(top, textvariable=self.status_var, fg="#666").pack(side=tk.RIGHT)

        btns = tk.Frame(top)
        btns.pack(side=tk.RIGHT, padx=8)
        tk.Button(btns, text="Status", command=lambda: self._quick("/status")).pack(side=tk.LEFT, padx=2)
        tk.Button(btns, text="Tools", command=lambda: self._quick("/tools")).pack(side=tk.LEFT, padx=2)
        tk.Button(btns, text="Clear", command=lambda: self._quick("/clear")).pack(side=tk.LEFT, padx=2)
        if self.voice_io:
            tk.Checkbutton(btns, text="Speak", variable=self._speak_var).pack(side=tk.LEFT, padx=4)

        self.chat = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#e0e0e0",
            insertbackground="#e0e0e0",
        )
        self.chat.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.chat.tag_configure("user", foreground="#7cbcfc")
        self.chat.tag_configure("assistant", foreground="#c5e1a5")
        self.chat.tag_configure("system", foreground="#aaa")
        self.chat.tag_configure("error", foreground="#ef9a9a")

        bottom = tk.Frame(self.root)
        bottom.pack(fill=tk.X, padx=8, pady=8)

        self.entry = tk.Text(bottom, height=3, font=("Segoe UI", 10), wrap=tk.WORD)
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.entry.bind("<Control-Return>", lambda e: self._send())
        self.entry.bind("<Return>", self._on_return)

        send_col = tk.Frame(bottom)
        send_col.pack(side=tk.RIGHT, padx=(8, 0))
        self.send_btn = tk.Button(send_col, text="Send", width=10, command=self._send)
        self.send_btn.pack(pady=1)
        if self.voice_io:
            self.mic_btn = tk.Button(
                send_col, text="Mic", width=10, command=self._push_to_talk, bg="#2a4a6a", fg="white"
            )
            self.mic_btn.pack(pady=1)
        tk.Label(send_col, text="Ctrl+Enter", fg="#888", font=("Segoe UI", 8)).pack()

    def _on_return(self, event):
        if event.state & 0x0001:  # Shift
            return None
        self._send()
        return "break"

    def _append(self, who: str, text: str, tag: str):
        self.chat.configure(state=tk.NORMAL)
        self.chat.insert(tk.END, f"{who}> ", tag)
        self.chat.insert(tk.END, text.rstrip() + "\n\n", tag)
        self.chat.see(tk.END)
        self.chat.configure(state=tk.DISABLED)

    def _append_system(self, text: str):
        self._append("system", text, "system")

    def _quick(self, cmd: str):
        self.entry.delete("1.0", tk.END)
        self.entry.insert("1.0", cmd)
        self._send()

    def _push_to_talk(self):
        if self._busy or not self.voice_io:
            return
        self._busy = True
        self.status_var.set("listening…")
        self.send_btn.configure(state=tk.DISABLED)
        if hasattr(self, "mic_btn"):
            self.mic_btn.configure(state=tk.DISABLED)

        def worker():
            try:
                heard = self.voice_io.listen_once()
                if heard:
                    self._work_q.put(("heard", heard))
                else:
                    self._work_q.put(("sys", "(no speech / timeout)"))
            except Exception as e:
                self._work_q.put(("err", str(e)))

        threading.Thread(target=worker, name="seven-ptt", daemon=True).start()

    def _send(self, text: Optional[str] = None):
        if self._busy:
            return
        if text is None:
            text = self.entry.get("1.0", tk.END).strip()
            self.entry.delete("1.0", tk.END)
        if not text:
            return
        self._append(config.USER_NAME, text, "user")
        self._busy = True
        self.status_var.set("thinking…")
        self.send_btn.configure(state=tk.DISABLED)
        if hasattr(self, "mic_btn"):
            self.mic_btn.configure(state=tk.DISABLED)

        def worker():
            try:
                reply = self.agent.handle(text)
                self._work_q.put(("ok", reply))
            except Exception as e:
                logger.exception("GUI handle failed")
                self._work_q.put(("err", str(e)))

        threading.Thread(target=worker, name="seven-gui-worker", daemon=True).start()

    def _poll_results(self):
        try:
            while True:
                kind, payload = self._work_q.get_nowait()
                if kind == "heard":
                    self._busy = False
                    self.send_btn.configure(state=tk.NORMAL)
                    if hasattr(self, "mic_btn"):
                        self.mic_btn.configure(state=tk.NORMAL)
                    self.status_var.set("idle")
                    self._send(payload)
                    continue
                if kind == "sys":
                    self._busy = False
                    self.send_btn.configure(state=tk.NORMAL)
                    if hasattr(self, "mic_btn"):
                        self.mic_btn.configure(state=tk.NORMAL)
                    self.status_var.set("idle")
                    self._append_system(payload)
                    continue

                self._busy = False
                self.send_btn.configure(state=tk.NORMAL)
                if hasattr(self, "mic_btn"):
                    self.mic_btn.configure(state=tk.NORMAL)
                self.status_var.set("idle")
                if kind == "ok":
                    if payload == "__QUIT__":
                        self._force_quit()
                        return
                    self._append(config.BOT_NAME, payload or "…", "assistant")
                    if (
                        self.voice_io
                        and self._speak_var.get()
                        and self.voice_io.tts_ok
                        and payload
                        and "tool_tier=" not in (payload or "")[:80]
                    ):
                        self.voice_io.speak_async(payload)
                else:
                    self._append(config.BOT_NAME, f"Error: {payload}", "error")
        except queue.Empty:
            pass
        if not self._closing:
            self.root.after(100, self._poll_results)

    def _on_close_request(self):
        if self._ensure_tray():
            self.root.withdraw()
            self.status_var.set("in tray")
            return
        self.root.iconify()

    def _ensure_tray(self) -> bool:
        if self._tray is not None:
            return True
        try:
            import pystray
            from PIL import Image, ImageDraw
        except ImportError:
            logger.info("pystray not installed — tray disabled (pip install pystray)")
            return False

        img = Image.new("RGB", (64, 64), color=(30, 30, 30))
        d = ImageDraw.Draw(img)
        d.ellipse((8, 8, 56, 56), fill=(100, 180, 255))
        d.text((22, 20), "7", fill=(20, 20, 20))

        def show(icon=None, item=None):
            self.root.after(0, self._show_window)

        def status(icon=None, item=None):
            self.root.after(0, lambda: self._quick("/status"))

        def quit_app(icon=None, item=None):
            self.root.after(0, self._force_quit)

        menu = pystray.Menu(
            pystray.MenuItem("Open Seven", show, default=True),
            pystray.MenuItem("Status", status),
            pystray.MenuItem("Quit", quit_app),
        )
        self._tray = pystray.Icon("seven_real", img, f"{config.BOT_NAME} Real", menu)

        def run_tray():
            try:
                self._tray.run()
            except Exception:
                logger.exception("tray failed")

        self._tray_thread = threading.Thread(target=run_tray, name="seven-tray", daemon=True)
        self._tray_thread.start()
        return True

    def _show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.status_var.set("idle")

    def _force_quit(self):
        self._closing = True
        try:
            if self.voice_io:
                self.voice_io.stop_speaking()
        except Exception:
            pass
        try:
            if self._tray is not None:
                self._tray.stop()
        except Exception:
            pass
        try:
            self.agent.shutdown()
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        self._ensure_tray()
        self.root.mainloop()


def run_gui(enable_voice: bool = False):
    app = SevenChatApp(enable_voice=enable_voice)
    app.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_gui()
