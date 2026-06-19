from __future__ import annotations

import ctypes
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
        del ttk
        background = "#0B0E14"
        card = "#141925"
        card_hover = "#1B2231"
        border = "#252D3D"
        text = "#F4F7FB"
        muted = "#8F9AAF"
        cyan = "#48D7FF"
        cyan_dark = "#123746"
        violet = "#9B7BFF"
        danger = "#FF6B7A"

        root = tk.Tk()
        root.title("VRC OCR Translate")
        root.resizable(False, False)
        root.configure(background=background)
        try:
            root.attributes("-topmost", True)
        except tk.TclError:
            pass
        try:
            root.update_idletasks()
            dark_title_bar = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                root.winfo_id(),
                20,
                ctypes.byref(dark_title_bar),
                ctypes.sizeof(dark_title_bar),
            )
        except Exception:
            pass

        mode_var = tk.StringVar()
        detail_var = tk.StringVar()

        def set_button_colors(
            widget: object,
            normal: str,
            hover: str,
            foreground: str = text,
        ) -> None:
            widget._normal_background = normal
            widget._hover_background = hover
            widget.configure(
                background=normal,
                foreground=foreground,
                activebackground=hover,
                activeforeground=foreground,
            )

        def make_button(
            parent: object,
            label: str,
            command: object,
            normal: str = card_hover,
            hover: str = border,
            foreground: str = text,
            font: tuple[str, int, str] = ("Malgun Gothic", 10, "bold"),
            padding_y: int = 10,
        ) -> object:
            widget = tk.Button(
                parent,
                text=label,
                command=command,
                relief="flat",
                borderwidth=0,
                highlightthickness=0,
                cursor="hand2",
                font=font,
                pady=padding_y,
                takefocus=False,
            )
            set_button_colors(widget, normal, hover, foreground)
            widget.bind(
                "<Enter>",
                lambda _event, button=widget: button.configure(
                    background=button._hover_background
                ),
            )
            widget.bind(
                "<Leave>",
                lambda _event, button=widget: button.configure(
                    background=button._normal_background
                ),
            )
            return widget

        def enqueue(command: ControlPanelCommand) -> None:
            self._commands.put(command)

        def request_quit() -> None:
            enqueue(ControlPanelCommand("quit"))
            root.destroy()

        def apply_status(status: ControlPanelStatus) -> None:
            mode_label = "자동 번역" if status.mode == "automatic" else "수동 번역"
            mode_var.set(f"●  {mode_label} 중")
            detail_var.set(
                f"X {status.offset_x:+.3f}   Y {status.offset_y:+.3f}   "
                f"Scale {status.scale_x:.2f}x"
            )
            if status.mode == "automatic":
                set_button_colors(auto_button, cyan, "#72E1FF", background)
                set_button_colors(manual_button, card_hover, border, muted)
                status_label.configure(foreground=cyan)
            else:
                set_button_colors(auto_button, card_hover, border, muted)
                set_button_colors(manual_button, violet, "#B39DFF", background)
                status_label.configure(foreground=violet)

        outer = tk.Frame(root, background=background, padx=18, pady=16)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)

        header = tk.Frame(outer, background=background)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        logo = tk.Canvas(
            header,
            width=42,
            height=42,
            background=background,
            highlightthickness=0,
        )
        logo.grid(row=0, column=0, rowspan=2, padx=(0, 10))
        logo.create_arc(7, 7, 35, 35, start=15, extent=150, style="arc", width=3, outline=cyan)
        logo.create_rectangle(6, 18, 36, 33, width=3, outline=text)
        logo.create_line(17, 25, 25, 25, fill=violet, width=3)
        tk.Label(
            header,
            text="VRC OCR TRANSLATE",
            background=background,
            foreground=text,
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=1, sticky="sw")
        tk.Label(
            header,
            text="LOCAL VR TRANSLATION",
            background=background,
            foreground=muted,
            font=("Segoe UI", 8, "normal"),
        ).grid(row=1, column=1, sticky="nw")

        mode_card = tk.Frame(
            outer,
            background=card,
            highlightbackground=border,
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        mode_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        mode_card.grid_columnconfigure(0, weight=1)
        mode_card.grid_columnconfigure(1, weight=1)
        status_label = tk.Label(
            mode_card,
            textvariable=mode_var,
            background=card,
            foreground=cyan,
            font=("Malgun Gothic", 10, "bold"),
        )
        status_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        auto_button = make_button(
            mode_card,
            "자동 번역",
            lambda: enqueue(ControlPanelCommand("set_mode", mode="automatic")),
        )
        auto_button.grid(row=1, column=0, sticky="ew", padx=(0, 4))
        manual_button = make_button(
            mode_card,
            "수동 번역",
            lambda: enqueue(ControlPanelCommand("set_mode", mode="manual")),
        )
        manual_button.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        action_card = tk.Frame(
            outer,
            background=card,
            highlightbackground=border,
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        action_card.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        action_card.grid_columnconfigure(0, weight=2)
        action_card.grid_columnconfigure(1, weight=1)
        tk.Label(
            action_card,
            text="빠른 동작",
            background=card,
            foreground=muted,
            font=("Malgun Gothic", 9, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        translate_button = make_button(
            action_card,
            "지금 번역",
            lambda: enqueue(ControlPanelCommand("translate")),
            normal=cyan,
            hover="#72E1FF",
            foreground=background,
            padding_y=12,
        )
        translate_button.grid(row=1, column=0, sticky="ew", padx=(0, 4))
        clear_button = make_button(
            action_card,
            "자막 지우기",
            lambda: enqueue(ControlPanelCommand("clear")),
            normal=card_hover,
            hover="#3A2430",
            foreground=danger,
            padding_y=12,
        )
        clear_button.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        position_card = tk.Frame(
            outer,
            background=card,
            highlightbackground=border,
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        position_card.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        position_card.grid_columnconfigure(0, weight=1)
        position_card.grid_columnconfigure(1, weight=1)
        position_card.grid_columnconfigure(2, weight=1)
        tk.Label(
            position_card,
            text="자막 위치",
            background=card,
            foreground=text,
            font=("Malgun Gothic", 10, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            position_card,
            textvariable=detail_var,
            background=card,
            foreground=muted,
            font=("Segoe UI", 8, "normal"),
        ).grid(row=0, column=1, columnspan=2, sticky="e")

        direction_specs = (
            ("▲", 1, 1, ControlPanelCommand("move", y_steps=-1)),
            ("◀", 2, 0, ControlPanelCommand("move", x_steps=-1)),
            ("↺", 2, 1, ControlPanelCommand("reset")),
            ("▶", 2, 2, ControlPanelCommand("move", x_steps=1)),
            ("▼", 3, 1, ControlPanelCommand("move", y_steps=1)),
        )
        for label, row, column, command in direction_specs:
            direction = make_button(
                position_card,
                label,
                lambda item=command: enqueue(item),
                font=("Segoe UI Symbol", 12, "bold"),
                padding_y=8,
            )
            direction.grid(row=row, column=column, sticky="ew", padx=4, pady=3)

        shrink_button = make_button(
            position_card,
            "−  축소",
            lambda: enqueue(ControlPanelCommand("scale", scale_steps=-1)),
            foreground=muted,
            padding_y=8,
        )
        shrink_button.grid(row=4, column=0, sticky="ew", padx=(4, 3), pady=(8, 2))
        grow_button = make_button(
            position_card,
            "+  확대",
            lambda: enqueue(ControlPanelCommand("scale", scale_steps=1)),
            foreground=muted,
            padding_y=8,
        )
        grow_button.grid(row=4, column=1, columnspan=2, sticky="ew", padx=(3, 4), pady=(8, 2))

        footer = tk.Frame(outer, background=background)
        footer.grid(row=4, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        tk.Label(
            footer,
            text="Ctrl + Alt + T  모드 전환",
            background=background,
            foreground=muted,
            font=("Malgun Gothic", 8, "normal"),
        ).grid(row=0, column=0, sticky="w")
        quit_button = make_button(
            footer,
            "종료",
            request_quit,
            normal=background,
            hover="#2A1720",
            foreground=danger,
            font=("Malgun Gothic", 8, "bold"),
            padding_y=5,
        )
        quit_button.grid(row=0, column=1, sticky="e")

        apply_status(initial_status)

        root.update_idletasks()
        width = 420
        height = root.winfo_reqheight()
        x = max(20, root.winfo_screenwidth() - width - 28)
        root.geometry(f"{width}x{height}+{x}+40")

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
