"""Lightweight floating Seven companion tied to the live agent state."""
from __future__ import annotations

import math
import queue
import threading
import time
import tkinter as tk
from pathlib import Path
from typing import Optional

import psutil
from PIL import Image, ImageTk

from seven import config
from seven.agent.loop import Seven


_POSES = {
    "idle": 0,
    "welcoming": 1,
    "thinking": 2,
    "determined": 3,
    "concerned": 4,
    "speaking": 5,
    "listening": 6,
    "amused": 7,
}


class SevenAvatar:
    """Transparent always-on-top desktop pet with one shared Seven runtime."""

    def __init__(
        self,
        agent: Seven,
        *,
        root: Optional[tk.Tk] = None,
        on_quit=None,
    ):
        self.agent = agent
        self.root = root or tk.Tk()
        self.on_quit = on_quit
        self.key = "#ff00ff"
        self.width = 292
        self.height = 472
        self._drag_origin = None
        self._started = time.monotonic()
        self._last_pose = ""
        self._chat = None
        self._chat_log = None
        self._chat_entry = None
        self._results: queue.Queue = queue.Queue()
        self._closing = False

        self.root.title("Seven")
        self.root.configure(bg=self.key)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        try:
            self.root.wm_attributes("-transparentcolor", self.key)
        except tk.TclError:
            pass
        x = max(0, self.root.winfo_screenwidth() - self.width - 34)
        y = max(0, self.root.winfo_screenheight() - self.height - 72)
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=self.key,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self._photos = self._load_poses()
        self._avatar_item = self.canvas.create_image(
            self.width // 2,
            self.height - 8,
            anchor="s",
            image=self._photos["idle"],
        )
        self._bubble = self.canvas.create_text(
            self.width // 2,
            18,
            anchor="n",
            width=260,
            text="Seven is here",
            fill="#dffbff",
            font=("Segoe UI", 10, "bold"),
        )
        self.canvas.bind("<ButtonPress-1>", self._drag_start)
        self.canvas.bind("<B1-Motion>", self._drag_move)
        self.canvas.bind("<Double-Button-1>", lambda _event: self.open_chat())
        self.canvas.bind("<Button-3>", self._menu)
        self.root.after(180, self._tick)

    @staticmethod
    def _sheet_path() -> Path:
        return Path(__file__).resolve().parents[1] / "assets" / "avatar" / "seven-pose-sheet.png"

    def _load_poses(self) -> dict[str, ImageTk.PhotoImage]:
        sheet = Image.open(self._sheet_path()).convert("RGBA")
        cell_w = sheet.width // 4
        cell_h = sheet.height // 2
        photos = {}
        for name, index in _POSES.items():
            col, row = index % 4, index // 4
            cell = sheet.crop(
                (
                    col * cell_w,
                    row * cell_h,
                    (col + 1) * cell_w,
                    (row + 1) * cell_h,
                )
            )
            alpha = cell.getchannel("A")
            bbox = alpha.getbbox()
            if bbox:
                cell = cell.crop(bbox)
            cell.thumbnail((260, 414), Image.Resampling.LANCZOS)
            photos[name] = ImageTk.PhotoImage(cell)
        return photos

    def _pose_for_state(self) -> str:
        activity = str(getattr(self.agent, "activity", "idle"))
        elapsed = time.time() - float(getattr(self.agent, "last_response_ts", 0))
        if activity == "thinking":
            return "thinking"
        if activity == "responded" and elapsed < 4.0:
            return "speaking"
        if activity == "concerned" and elapsed < 6.0:
            return "concerned"
        affect = self.agent.affect.status()
        dominant = affect.get("dominant_emotion")
        return {
            "concerned": "concerned",
            "frustrated": "determined",
            "determined": "determined",
            "curious": "thinking",
            "amused": "amused",
            "content": "amused",
        }.get(str(dominant), "idle")

    def _tick(self):
        if self._closing:
            return
        pose = self._pose_for_state()
        if pose != self._last_pose:
            self.canvas.itemconfigure(self._avatar_item, image=self._photos[pose])
            self._last_pose = pose
        affect = self.agent.affect.status()
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        activity = getattr(self.agent, "activity", "idle")
        self.canvas.itemconfigure(
            self._bubble,
            text=(
                f"{activity} · {affect.get('dominant_emotion', 'calm')}\n"
                f"CPU {cpu:.0f}%  RAM {ram:.0f}%"
            ),
        )
        bob = int(round(math.sin((time.monotonic() - self._started) * 1.7) * 3))
        self.canvas.coords(
            self._avatar_item, self.width // 2, self.height - 8 + bob
        )
        self._poll_chat_results()
        self.root.after(250, self._tick)

    def _drag_start(self, event):
        self._drag_origin = (event.x_root, event.y_root, self.root.winfo_x(), self.root.winfo_y())

    def _drag_move(self, event):
        if not self._drag_origin:
            return
        start_x, start_y, window_x, window_y = self._drag_origin
        self.root.geometry(
            f"+{window_x + event.x_root - start_x}+{window_y + event.y_root - start_y}"
        )

    def _menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Talk to Seven", command=self.open_chat)
        menu.add_command(label="Show mind state", command=self._show_mind)
        menu.add_separator()
        menu.add_command(label="Quit Seven", command=self.close)
        menu.tk_popup(event.x_root, event.y_root)

    def open_chat(self):
        if self._chat and self._chat.winfo_exists():
            self._chat.deiconify()
            self._chat.lift()
            self._chat_entry.focus_set()
            return
        self._chat = tk.Toplevel(self.root)
        self._chat.title("Talk to Seven")
        self._chat.geometry("620x480")
        self._chat.configure(bg="#08111f")
        self._chat_log = tk.Text(
            self._chat,
            state="disabled",
            wrap="word",
            bg="#08111f",
            fg="#dffbff",
            insertbackground="#dffbff",
            font=("Segoe UI", 10),
        )
        self._chat_log.pack(fill="both", expand=True, padx=10, pady=10)
        row = tk.Frame(self._chat, bg="#08111f")
        row.pack(fill="x", padx=10, pady=(0, 10))
        self._chat_entry = tk.Entry(
            row,
            bg="#101e31",
            fg="white",
            insertbackground="white",
            font=("Segoe UI", 11),
        )
        self._chat_entry.pack(side="left", fill="x", expand=True)
        self._chat_entry.bind("<Return>", lambda _event: self._send_chat())
        tk.Button(row, text="Send", command=self._send_chat).pack(side="left", padx=(8, 0))
        self._append_chat("Seven", "I’m here. What are we doing?")
        self._chat_entry.focus_set()

    def _send_chat(self):
        if not self._chat_entry:
            return
        message = self._chat_entry.get().strip()
        if not message:
            return
        self._chat_entry.delete(0, "end")
        self._append_chat(config.USER_NAME, message)

        def worker():
            try:
                self._results.put(("reply", self.agent.handle(message)))
            except Exception as exc:
                self._results.put(("reply", f"Error: {exc}"))

        threading.Thread(target=worker, name="seven-avatar-chat", daemon=True).start()

    def _poll_chat_results(self):
        try:
            while True:
                kind, value = self._results.get_nowait()
                if kind == "reply":
                    self._append_chat(config.BOT_NAME, value)
        except queue.Empty:
            return

    def _append_chat(self, who: str, text: str):
        if not self._chat_log:
            return
        self._chat_log.configure(state="normal")
        self._chat_log.insert("end", f"{who}> {text}\n\n")
        self._chat_log.see("end")
        self._chat_log.configure(state="disabled")

    def _show_mind(self):
        self.open_chat()
        state = self.agent.affect.status()
        self._append_chat(
            "Seven",
            (
                f"Current state: {state['dominant_emotion']} / "
                f"{state['secondary_emotion']}; energy {state['energy']:.0%}; "
                f"confidence {state['confidence']:.0%}."
            ),
        )

    def close(self):
        self._closing = True
        try:
            if self.on_quit:
                self.on_quit()
        finally:
            self.root.destroy()

    def run(self):
        self.root.mainloop()


def run_avatar(*, enable_api: bool = True) -> None:
    """Run one agent shared by floating avatar, chat, heartbeat, and API."""
    agent = Seven()
    agent.start_heartbeat()
    api_server = None
    if enable_api:
        from seven.ui.api_server import start_api_server

        api_server = start_api_server(background=True, agent=agent)

    def shutdown():
        if api_server is not None:
            api_server.shutdown_cleanly()
        agent.shutdown()

    SevenAvatar(agent, on_quit=shutdown).run()
