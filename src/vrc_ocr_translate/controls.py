from __future__ import annotations

import ctypes
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

VK_CONTROL = 0x11
VK_MENU = 0x12
VK_T = 0x54


@dataclass(frozen=True, slots=True)
class ControlEvents:
    translate: bool = False
    clear: bool = False


class KeyboardModeToggle:
    def __init__(self) -> None:
        self._user32 = ctypes.windll.user32 if os.name == "nt" else None
        self._was_down = False

    def poll(self) -> bool:
        if self._user32 is None:
            return False
        down = all(
            self._user32.GetAsyncKeyState(key) & 0x8000
            for key in (VK_CONTROL, VK_MENU, VK_T)
        )
        triggered = bool(down and not self._was_down)
        self._was_down = bool(down)
        return triggered


class SteamVRControllerInput:
    ACTION_SET = "/actions/translation"
    TRANSLATE_ACTION = "/actions/translation/in/translate"
    CLEAR_ACTION = "/actions/translation/in/clear"

    def __init__(
        self,
        manifest_path: str | Path | None = None,
        openvr_module: Any = None,
    ) -> None:
        if openvr_module is None:
            try:
                import openvr as openvr_module
            except ImportError as exc:
                raise RuntimeError("Controller input requires the 'openvr' package") from exc
        self._openvr = openvr_module
        self._manifest_path = Path(manifest_path or self.default_manifest_path())
        self._input: Any = None
        self._active_sets: Any = None
        self._translate_handle: int | None = None
        self._clear_handle: int | None = None
        self._translate_down = False
        self._clear_down = False

    @staticmethod
    def default_manifest_path() -> Path:
        return Path(__file__).resolve().parent / "openvr_actions" / "actions.json"

    def start(self) -> None:
        manifest = self._manifest_path.resolve()
        if not manifest.exists():
            raise FileNotFoundError(f"OpenVR action manifest was not found: {manifest}")

        vr_input = self._openvr.VRInput()
        vr_input.setActionManifestPath(str(manifest))
        action_set_handle = vr_input.getActionSetHandle(self.ACTION_SET)
        self._translate_handle = vr_input.getActionHandle(self.TRANSLATE_ACTION)
        self._clear_handle = vr_input.getActionHandle(self.CLEAR_ACTION)

        active_sets = (self._openvr.VRActiveActionSet_t * 1)()
        active_sets[0].ulActionSet = action_set_handle
        active_sets[0].ulRestrictedToDevice = self._openvr.k_ulInvalidInputValueHandle
        active_sets[0].ulSecondaryActionSet = self._openvr.k_ulInvalidActionSetHandle
        active_sets[0].nPriority = self._openvr.k_nActionSetOverlayGlobalPriorityMin
        self._input = vr_input
        self._active_sets = active_sets
        self._input.updateActionState(self._active_sets)
        self._translate_down = self._action_down(self._translate_handle)
        self._clear_down = self._action_down(self._clear_handle)
        LOGGER.info("SteamVR controller actions loaded: left trigger=translate, grip=clear")

    def poll(self) -> ControlEvents:
        if self._input is None or self._active_sets is None:
            return ControlEvents()
        self._input.updateActionState(self._active_sets)
        translate_down = self._action_down(self._translate_handle)
        clear_down = self._action_down(self._clear_handle)
        events = ControlEvents(
            translate=translate_down and not self._translate_down,
            clear=clear_down and not self._clear_down,
        )
        self._translate_down = translate_down
        self._clear_down = clear_down
        return events

    def _action_down(self, handle: int | None) -> bool:
        if handle is None:
            return False
        data = self._input.getDigitalActionData(
            handle,
            self._openvr.k_ulInvalidInputValueHandle,
        )
        return bool(data.bActive and data.bState)
