from __future__ import annotations

import ctypes
import logging
import os
from dataclasses import dataclass
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
    PRESS_THRESHOLD = 0.65
    RELEASE_THRESHOLD = 0.55
    CONTROLLER_AXIS_TYPE_TRIGGER = 3

    def __init__(
        self,
        openvr_module: Any = None,
        vr_system: Any = None,
    ) -> None:
        if openvr_module is None:
            try:
                import openvr as openvr_module
            except ImportError as exc:
                raise RuntimeError("Controller input requires the 'openvr' package") from exc
        self._openvr = openvr_module
        self._system = vr_system
        self._left_device_index: int | None = None
        self._trigger_axis: int | None = None
        self._grip_axis: int | None = None
        self._translate_down = False
        self._clear_down = False

    def start(self) -> None:
        if self._system is None:
            self._system = self._openvr.VRSystem()
        self._refresh_left_controller(required=True)
        self._translate_down, self._clear_down = self._read_button_states()
        LOGGER.info(
            "Passive SteamVR controller monitoring loaded: left trigger=translate, "
            "grip=clear; inputs continue to VRChat"
        )

    def poll(self) -> ControlEvents:
        if self._system is None:
            return ControlEvents()
        self._refresh_left_controller(required=False)
        translate_down, clear_down = self._read_button_states()
        events = ControlEvents(
            translate=translate_down and not self._translate_down,
            clear=clear_down and not self._clear_down,
        )
        self._translate_down = translate_down
        self._clear_down = clear_down
        return events

    def _refresh_left_controller(self, required: bool) -> None:
        device_index = self._system.getTrackedDeviceIndexForControllerRole(
            self._openvr.TrackedControllerRole_LeftHand
        )
        if device_index == self._openvr.k_unTrackedDeviceIndexInvalid:
            self._left_device_index = None
            self._trigger_axis = None
            self._grip_axis = None
            if required:
                raise RuntimeError("SteamVR left controller was not found")
            return
        if device_index == self._left_device_index:
            return

        self._left_device_index = device_index
        trigger_axes: list[int] = []
        for axis_index in range(5):
            property_id = getattr(
                self._openvr,
                f"Prop_Axis{axis_index}Type_Int32",
            )
            try:
                axis_type = self._system.getInt32TrackedDeviceProperty(
                    device_index,
                    property_id,
                )
            except Exception:
                continue
            if axis_type == self.CONTROLLER_AXIS_TYPE_TRIGGER:
                trigger_axes.append(axis_index)

        self._trigger_axis = trigger_axes[0] if trigger_axes else None
        self._grip_axis = trigger_axes[1] if len(trigger_axes) > 1 else None
        try:
            controller_type = self._system.getStringTrackedDeviceProperty(
                device_index,
                self._openvr.Prop_ControllerType_String,
            )
        except Exception:
            controller_type = "unknown"
        LOGGER.info(
            "Left controller detected: type=%s device=%d trigger_axis=%s grip_axis=%s",
            controller_type,
            device_index,
            self._trigger_axis,
            self._grip_axis,
        )

    def _read_button_states(self) -> tuple[bool, bool]:
        if self._left_device_index is None:
            return False, False
        success, state = self._system.getControllerState(self._left_device_index)
        if not success:
            return False, False

        trigger_mask = 1 << self._openvr.k_EButton_SteamVR_Trigger
        grip_mask = 1 << self._openvr.k_EButton_Grip
        trigger_down = bool(state.ulButtonPressed & trigger_mask) or self._axis_down(
            state,
            self._trigger_axis,
            self._translate_down,
        )
        grip_down = bool(state.ulButtonPressed & grip_mask) or self._axis_down(
            state,
            self._grip_axis,
            self._clear_down,
        )
        return trigger_down, grip_down

    def _axis_down(self, state: Any, axis_index: int | None, was_down: bool) -> bool:
        if axis_index is None:
            return False
        threshold = self.RELEASE_THRESHOLD if was_down else self.PRESS_THRESHOLD
        return float(state.rAxis[axis_index].x) >= threshold
