from __future__ import annotations

import logging
import queue
import threading
from dataclasses import dataclass
from typing import Literal

from .config import OverlayConfig

LOGGER = logging.getLogger(__name__)

CommandName = Literal[
    "translate",
    "clear",
    "toggle_mode",
    "set_mode",
    "move",
    "scale",
    "reset",
    "quit",
]


@dataclass(frozen=True, slots=True)
class ControlPanelCommand:
    name: CommandName
    mode: str | None = None
    x_steps: int = 0
    y_steps: int = 0
    scale_steps: int = 0


@dataclass(frozen=True, slots=True)
class ControlPanelStatus:
    mode: str
    offset_x: float
    offset_y: float
    scale_x: float
    scale_y: float

    @classmethod
    def from_overlay(cls, mode: str, overlay: OverlayConfig) -> "ControlPanelStatus":
        return cls(
            mode=mode,
            offset_x=overlay.position_offset_x_ratio,
            offset_y=overlay.position_offset_y_ratio,
            scale_x=overlay.position_scale_x,
            scale_y=overlay.position_scale_y,
        )


class ControlPanel:
    def __init__(self) -> None:
        self._commands: queue.Queue[ControlPanelCommand] = queue.Queue()
        self._updates: queue.Queue[ControlPanelStatus | None] = queue.Queue()
        self._thread: threading.Thread | None = None

    def start(self, status: ControlPanelStatus) -> None:
        try:
            import tkinter as tk
            from tkinter import ttk
        except ImportError as exc:
            raise RuntimeError("Control panel requires tkinter") from exc

        self._thread = threading.Thread(
            target=self._run,
            args=(tk, ttk, status),
            name="VRC OCR Translate Control Panel",
            daemon=True,
        )
        self._thread.start()

    def poll(self) -> list[ControlPanelCommand]:
        commands: list[ControlPanelCommand] = []
        while True:
            try:
                commands.append(self._commands.get_nowait())
            except queue.Empty:
                return commands

    def update(self, status: ControlPanelStatus) -> None:
        self._updates.put(status)

    def close(self) -> None:
        self._updates.put(None)
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _run(self, tk: object, ttk: object, initial_status: ControlPanelStatus) -> None:
        root = tk.Tk()
        root.title("VRC OCR Translate")
        root.resizable(False, False)
        try:
            root.attributes("-topmost", True)
        except tk.TclError:
            pass

        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        mode_var = tk.StringVar()
        detail_var = tk.StringVar()

        def enqueue(command: ControlPanelCommand) -> None:
            self._commands.put(command)

        def request_quit() -> None:
            enqueue(ControlPanelCommand("quit"))
            root.destroy()

        def apply_status(status: ControlPanelStatus) -> None:
            mode_label = "자동 번역" if status.mode == "automatic" else "수동 번역"
            mode_var.set(f"현재 모드: {mode_label}")
            detail_var.set(
                "위치 "
                f"X {status.offset_x:+.3f} / Y {status.offset_y:+.3f}  "
                f"배율 {status.scale_x:.2f}x"
            )

        outer = ttk.Frame(root, padding=12)
        outer.grid(row=0, column=0, sticky="nsew")
        ttk.Label(
            outer,
            text="VRC OCR Translate",
            font=("Malgun Gothic", 13, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(outer, textvariable=mode_var).grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(8, 0),
        )
        ttk.Label(outer, textvariable=detail_var).grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(2, 8),
        )

        ttk.Button(
            outer,
            text="자동",
            command=lambda: enqueue(ControlPanelCommand("set_mode", mode="automatic")),
            width=10,
        ).grid(row=3, column=0, padx=(0, 4), pady=2)
        ttk.Button(
            outer,
            text="수동",
            command=lambda: enqueue(ControlPanelCommand("set_mode", mode="manual")),
            width=10,
        ).grid(row=3, column=1, padx=4, pady=2)
        ttk.Button(
            outer,
            text="전환",
            command=lambda: enqueue(ControlPanelCommand("toggle_mode")),
            width=10,
        ).grid(row=3, column=2, padx=(4, 0), pady=2)

        ttk.Button(
            outer,
            text="한 번 번역",
            command=lambda: enqueue(ControlPanelCommand("translate")),
        ).grid(row=4, column=0, columnspan=2, sticky="ew", padx=(0, 4), pady=(10, 2))
        ttk.Button(
            outer,
            text="자막 지우기",
            command=lambda: enqueue(ControlPanelCommand("clear")),
        ).grid(row=4, column=2, sticky="ew", padx=(4, 0), pady=(10, 2))

        position = ttk.LabelFrame(outer, text="자막 위치")
        position.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(10, 2))
        ttk.Button(
            position,
            text="▲",
            command=lambda: enqueue(ControlPanelCommand("move", y_steps=-1)),
            width=8,
        ).grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(
            position,
            text="◀",
            command=lambda: enqueue(ControlPanelCommand("move", x_steps=-1)),
            width=8,
        ).grid(row=1, column=0, padx=4, pady=4)
        ttk.Button(
            position,
            text="초기화",
            command=lambda: enqueue(ControlPanelCommand("reset")),
            width=8,
        ).grid(row=1, column=1, padx=4, pady=4)
        ttk.Button(
            position,
            text="▶",
            command=lambda: enqueue(ControlPanelCommand("move", x_steps=1)),
            width=8,
        ).grid(row=1, column=2, padx=4, pady=4)
        ttk.Button(
            position,
            text="▼",
            command=lambda: enqueue(ControlPanelCommand("move", y_steps=1)),
            width=8,
        ).grid(row=2, column=1, padx=4, pady=4)

        ttk.Button(
            outer,
            text="배율 -",
            command=lambda: enqueue(ControlPanelCommand("scale", scale_steps=-1)),
        ).grid(row=6, column=0, columnspan=1, sticky="ew", padx=(0, 4), pady=(10, 2))
        ttk.Button(
            outer,
            text="배율 +",
            command=lambda: enqueue(ControlPanelCommand("scale", scale_steps=1)),
        ).grid(row=6, column=1, columnspan=2, sticky="ew", padx=(4, 0), pady=(10, 2))

        ttk.Button(
            outer,
            text="프로그램 종료",
            command=request_quit,
        ).grid(row=7, column=0, columnspan=3, sticky="ew", pady=(12, 0))

        apply_status(initial_status)

        def process_updates() -> None:
            while True:
                try:
                    status = self._updates.get_nowait()
                except queue.Empty:
                    break
                if status is None:
                    root.destroy()
                    return
                apply_status(status)
            root.after(100, process_updates)

        root.protocol("WM_DELETE_WINDOW", request_quit)
        root.after(100, process_updates)
        try:
            root.mainloop()
        except Exception:
            LOGGER.exception("Control panel stopped unexpectedly")
