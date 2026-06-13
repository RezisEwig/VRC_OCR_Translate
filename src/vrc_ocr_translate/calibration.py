from __future__ import annotations

import ctypes
import logging
import os
import time
from pathlib import Path

from .config import (
    DEFAULT_POSITION_OFFSET_X_RATIO,
    DEFAULT_POSITION_OFFSET_Y_RATIO,
    OverlayConfig,
    save_overlay_calibration,
)

LOGGER = logging.getLogger(__name__)

VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_HOME = 0x24
VK_ADD = 0x6B
VK_SUBTRACT = 0x6D


class PositionCalibrationController:
    def __init__(self, config: OverlayConfig, config_path: str | Path) -> None:
        self._config = config
        self._config_path = Path(config_path)
        self._user32 = ctypes.windll.user32 if os.name == "nt" else None
        self._last_repeat_at: dict[int, float] = {}

    def poll(self) -> bool:
        if self._user32 is None or not self._down(VK_CONTROL) or not self._down(VK_MENU):
            return False

        changed = False
        step = max(0.002, min(0.1, self._config.calibration_step_ratio))
        if self._repeat(VK_LEFT):
            self._config.position_offset_x_ratio -= step
            changed = True
        if self._repeat(VK_RIGHT):
            self._config.position_offset_x_ratio += step
            changed = True
        if self._repeat(VK_UP):
            self._config.position_offset_y_ratio -= step
            changed = True
        if self._repeat(VK_DOWN):
            self._config.position_offset_y_ratio += step
            changed = True
        if self._repeat(VK_ADD):
            self._config.position_scale_x = min(2.0, self._config.position_scale_x + step)
            self._config.position_scale_y = min(2.0, self._config.position_scale_y + step)
            changed = True
        if self._repeat(VK_SUBTRACT):
            self._config.position_scale_x = max(0.25, self._config.position_scale_x - step)
            self._config.position_scale_y = max(0.25, self._config.position_scale_y - step)
            changed = True
        if self._repeat(VK_HOME):
            self._config.position_offset_x_ratio = DEFAULT_POSITION_OFFSET_X_RATIO
            self._config.position_offset_y_ratio = DEFAULT_POSITION_OFFSET_Y_RATIO
            self._config.position_scale_x = 1.0
            self._config.position_scale_y = 1.0
            changed = True

        if changed:
            self._clamp()
            save_overlay_calibration(self._config_path, self._config)
            LOGGER.info(
                "Position calibration saved: x=%+.3f y=%+.3f scale_x=%.3f scale_y=%.3f",
                self._config.position_offset_x_ratio,
                self._config.position_offset_y_ratio,
                self._config.position_scale_x,
                self._config.position_scale_y,
            )
        return changed

    def _down(self, key: int) -> bool:
        return bool(self._user32.GetAsyncKeyState(key) & 0x8000)

    def _repeat(self, key: int) -> bool:
        if not self._down(key):
            self._last_repeat_at.pop(key, None)
            return False
        now = time.monotonic()
        last = self._last_repeat_at.get(key)
        if last is not None and now - last < 0.12:
            return False
        self._last_repeat_at[key] = now
        return True

    def _clamp(self) -> None:
        self._config.position_offset_x_ratio = max(
            -0.5, min(0.5, self._config.position_offset_x_ratio)
        )
        self._config.position_offset_y_ratio = max(
            -0.5, min(0.5, self._config.position_offset_y_ratio)
        )
