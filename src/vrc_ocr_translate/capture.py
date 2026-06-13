from __future__ import annotations

import ctypes
import logging
import threading
import time
from ctypes import wintypes
from typing import Any

from PIL import Image

from .config import CaptureConfig

LOGGER = logging.getLogger(__name__)


class ScreenCapture:
    def __init__(self, config: CaptureConfig) -> None:
        try:
            import mss
        except ImportError as exc:
            raise RuntimeError("Screen capture requires the 'mss' package") from exc
        self._capture = mss.MSS()
        self._config = config

    @property
    def monitors(self) -> list[dict[str, int]]:
        return [dict(monitor) for monitor in self._capture.monitors]

    def _target(self) -> dict[str, int]:
        monitors = self._capture.monitors
        if not 0 <= self._config.monitor < len(monitors):
            raise ValueError(
                f"Monitor {self._config.monitor} does not exist; "
                f"available indexes are 0..{len(monitors) - 1}"
            )
        monitor = dict(monitors[self._config.monitor])
        region = self._config.region
        if region is None:
            return monitor
        required = {"left", "top", "width", "height"}
        missing = required - set(region)
        if missing:
            raise ValueError(f"Capture region is missing: {', '.join(sorted(missing))}")
        return {
            "left": monitor["left"] + int(region["left"]),
            "top": monitor["top"] + int(region["top"]),
            "width": int(region["width"]),
            "height": int(region["height"]),
        }

    def grab(self) -> Image.Image:
        frame: Any = self._capture.grab(self._target())
        return Image.frombytes("RGB", frame.size, frame.rgb)

    def close(self) -> None:
        self._capture.close()

    def __enter__(self) -> "ScreenCapture":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class VRChatWindowCapture:
    """Capture only the VRChat Unity window, before SteamVR overlays are composed."""

    _SW_SHOWNOACTIVATE = 4
    _SW_MINIMIZE = 6
    _DWMWA_EXTENDED_FRAME_BOUNDS = 9

    def __init__(self, config: CaptureConfig) -> None:
        try:
            from windows_capture import WindowsCapture
        except ImportError as exc:
            raise RuntimeError(
                "VRChat window capture requires the 'windows-capture' package"
            ) from exc

        self._windows_capture_class = WindowsCapture
        self._config = config
        self._condition = threading.Condition()
        self._latest_frame: Image.Image | None = None
        self._closed_error: RuntimeError | None = None
        self._capture: Any = None
        self._control: Any = None
        self._hwnd: int | None = None
        self._was_minimized = False
        self._stopping = False
        self._crop_shape: tuple[int, int] | None = None
        self._crop_box: tuple[int, int, int, int] | None = None

    @staticmethod
    def _window_text(hwnd: int) -> str:
        user32 = ctypes.windll.user32
        length = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, len(buffer))
        return buffer.value

    @staticmethod
    def _window_class(hwnd: int) -> str:
        buffer = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetClassNameW(hwnd, buffer, len(buffer))
        return buffer.value

    def _find_window(self) -> int:
        expected_title = self._config.window_title.casefold()
        expected_class = self._config.window_class.casefold()
        matches: list[int] = []
        callback_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
        )

        @callback_type
        def visit(hwnd: int, _lparam: int) -> bool:
            title = self._window_text(hwnd)
            class_name = self._window_class(hwnd)
            title_matches = not expected_title or expected_title in title.casefold()
            class_matches = not expected_class or expected_class == class_name.casefold()
            if title_matches and class_matches:
                matches.append(int(hwnd))
                return False
            return True

        ctypes.windll.user32.EnumWindows(visit, 0)
        if not matches:
            raise RuntimeError(
                "VRChat game window was not found. Start VRChat and wait until the "
                "game window appears before running the translator."
            )
        return matches[0]

    def _client_crop(
        self, frame_width: int, frame_height: int
    ) -> tuple[int, int, int, int]:
        shape = (frame_width, frame_height)
        if self._crop_shape == shape and self._crop_box is not None:
            return self._crop_box
        if self._hwnd is None:
            return (0, 0, frame_width, frame_height)

        user32 = ctypes.windll.user32
        bounds = wintypes.RECT()
        result = ctypes.windll.dwmapi.DwmGetWindowAttribute(
            self._hwnd,
            self._DWMWA_EXTENDED_FRAME_BOUNDS,
            ctypes.byref(bounds),
            ctypes.sizeof(bounds),
        )
        if result != 0:
            user32.GetWindowRect(self._hwnd, ctypes.byref(bounds))

        client = wintypes.RECT()
        origin = wintypes.POINT(0, 0)
        if not user32.GetClientRect(self._hwnd, ctypes.byref(client)):
            return (0, 0, frame_width, frame_height)
        if not user32.ClientToScreen(self._hwnd, ctypes.byref(origin)):
            return (0, 0, frame_width, frame_height)

        left = max(0, origin.x - bounds.left)
        top = max(0, origin.y - bounds.top)
        right = min(frame_width, left + client.right - client.left)
        bottom = min(frame_height, top + client.bottom - client.top)
        if right <= left or bottom <= top:
            crop = (0, 0, frame_width, frame_height)
        else:
            crop = (left, top, right, bottom)
        self._crop_shape = shape
        self._crop_box = crop
        return crop

    def start(self) -> None:
        if self._control is not None:
            return
        self._hwnd = self._find_window()
        user32 = ctypes.windll.user32
        self._was_minimized = bool(user32.IsIconic(self._hwnd))
        if self._was_minimized:
            if not self._config.restore_minimized_window:
                raise RuntimeError(
                    "VRChat is minimized and Windows cannot capture minimized windows. "
                    "Restore VRChat or enable capture.restore_minimized_window."
                )
            LOGGER.info("Restoring minimized VRChat window without activating it")
            user32.ShowWindow(self._hwnd, self._SW_SHOWNOACTIVATE)
            deadline = time.monotonic() + 3.0
            while user32.IsIconic(self._hwnd) and time.monotonic() < deadline:
                time.sleep(0.05)
            if user32.IsIconic(self._hwnd):
                raise RuntimeError("VRChat window could not be restored for capture")

        LOGGER.info(
            "Capturing VRChat window: hwnd=0x%x title=%r class=%r",
            self._hwnd,
            self._window_text(self._hwnd),
            self._window_class(self._hwnd),
        )
        capture = self._windows_capture_class(
            cursor_capture=False,
            draw_border=False,
            minimum_update_interval=100,
            window_hwnd=self._hwnd,
        )

        @capture.event
        def on_frame_arrived(frame: Any, _control: Any) -> None:
            try:
                left, top, right, bottom = self._client_crop(
                    frame.width, frame.height
                )
                bgra = frame.frame_buffer[top:bottom, left:right]
                rgb = bgra[:, :, [2, 1, 0]].copy()
                image = Image.fromarray(rgb)
            except Exception as exc:
                with self._condition:
                    self._closed_error = RuntimeError(
                        f"Could not convert the VRChat capture frame: {exc}"
                    )
                    self._condition.notify_all()
                return
            with self._condition:
                self._latest_frame = image
                self._condition.notify_all()

        @capture.event
        def on_closed() -> None:
            with self._condition:
                if not self._stopping:
                    self._closed_error = RuntimeError(
                        "VRChat window capture stopped. The game may have closed or "
                        "recreated its window. Restart the translator."
                    )
                self._condition.notify_all()

        self._capture = capture
        self._control = capture.start_free_threaded()

    def grab(self) -> Image.Image:
        if self._control is None:
            raise RuntimeError("VRChat window capture has not been started")
        deadline = time.monotonic() + 10.0
        with self._condition:
            while self._latest_frame is None and self._closed_error is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._condition.wait(remaining)
            if self._closed_error is not None:
                raise self._closed_error
            if self._latest_frame is None:
                raise RuntimeError(
                    "No frame arrived from VRChat within 10 seconds. Make sure the "
                    "game window is restored and rendering."
                )
            return self._latest_frame.copy()

    def close(self) -> None:
        self._stopping = True
        if self._control is not None:
            try:
                self._control.stop()
                self._control.wait()
            except Exception:
                LOGGER.debug("Error while stopping VRChat capture", exc_info=True)
        self._control = None
        self._capture = None
        if self._was_minimized and self._hwnd is not None:
            if ctypes.windll.user32.IsWindow(self._hwnd):
                ctypes.windll.user32.ShowWindow(self._hwnd, self._SW_MINIMIZE)
        self._hwnd = None

    def __enter__(self) -> "VRChatWindowCapture":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def create_capture(
    config: CaptureConfig,
    openvr_initialized: bool = False,
) -> ScreenCapture | VRChatWindowCapture:
    del openvr_initialized
    source = config.source.lower()
    if source == "monitor":
        return ScreenCapture(config)
    if source == "vrchat_window":
        return VRChatWindowCapture(config)
    if source == "steamvr_mirror":
        raise ValueError(
            "capture.source='steamvr_mirror' is disabled because SteamVR returns "
            "InvalidTexture on this system. Use 'vrchat_window'."
        )
    raise ValueError("capture.source must be 'vrchat_window' or 'monitor'")
