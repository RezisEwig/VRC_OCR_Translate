from types import SimpleNamespace

import openvr

from vrc_ocr_translate.app import _translation_mode
from vrc_ocr_translate.controls import SteamVRControllerInput


class _FakeControllerState:
    def __init__(self):
        self.ulButtonPressed = 0
        self.rAxis = [SimpleNamespace(x=0.0, y=0.0) for _ in range(5)]


class _FakeVRSystem:
    def __init__(self):
        self.device_index = 6
        self.state = _FakeControllerState()
        self.axis_types = {0: 2, 1: 3, 2: 3}

    def getTrackedDeviceIndexForControllerRole(self, _role):
        return self.device_index

    def getInt32TrackedDeviceProperty(self, _device_index, property_id):
        axis_index = property_id - openvr.Prop_Axis0Type_Int32
        if axis_index not in self.axis_types:
            raise RuntimeError("axis is unavailable")
        return self.axis_types[axis_index]

    def getStringTrackedDeviceProperty(self, _device_index, _property_id):
        return "oculus_touch"

    def getControllerState(self, _device_index):
        return True, self.state


class _FakeOpenVR:
    TrackedControllerRole_LeftHand = openvr.TrackedControllerRole_LeftHand
    k_unTrackedDeviceIndexInvalid = openvr.k_unTrackedDeviceIndexInvalid
    k_EButton_SteamVR_Trigger = openvr.k_EButton_SteamVR_Trigger
    k_EButton_Grip = openvr.k_EButton_Grip
    Prop_ControllerType_String = openvr.Prop_ControllerType_String
    Prop_Axis0Type_Int32 = openvr.Prop_Axis0Type_Int32
    Prop_Axis1Type_Int32 = openvr.Prop_Axis1Type_Int32
    Prop_Axis2Type_Int32 = openvr.Prop_Axis2Type_Int32
    Prop_Axis3Type_Int32 = openvr.Prop_Axis3Type_Int32
    Prop_Axis4Type_Int32 = openvr.Prop_Axis4Type_Int32


def _controls(system: _FakeVRSystem) -> SteamVRControllerInput:
    controls = SteamVRControllerInput(
        openvr_module=_FakeOpenVR(),
        vr_system=system,
    )
    controls.start()
    return controls


def test_controller_axes_emit_only_on_rising_edge():
    system = _FakeVRSystem()
    controls = _controls(system)

    assert not controls.poll().translate
    system.state.rAxis[1].x = 0.7
    assert controls.poll().translate
    assert not controls.poll().translate
    system.state.rAxis[1].x = 0.6
    assert not controls.poll().translate
    system.state.rAxis[1].x = 0.5
    assert not controls.poll().translate

    system.state.rAxis[2].x = 0.7
    assert controls.poll().clear


def test_controller_button_held_during_start_does_not_emit():
    system = _FakeVRSystem()
    system.state.rAxis[2].x = 0.8
    controls = _controls(system)

    assert not controls.poll().clear
    system.state.rAxis[2].x = 0.0
    assert not controls.poll().clear
    system.state.rAxis[2].x = 0.8
    assert controls.poll().clear


def test_grip_button_bit_is_supported_without_an_analog_grip_axis():
    system = _FakeVRSystem()
    system.axis_types = {0: 2, 1: 3}
    controls = _controls(system)

    system.state.ulButtonPressed = 1 << openvr.k_EButton_Grip
    assert controls.poll().clear


def test_missing_left_controller_fails_during_start():
    system = _FakeVRSystem()
    system.device_index = openvr.k_unTrackedDeviceIndexInvalid
    controls = SteamVRControllerInput(
        openvr_module=_FakeOpenVR(),
        vr_system=system,
    )

    try:
        controls.start()
    except RuntimeError as exc:
        assert "left controller" in str(exc)
    else:
        raise AssertionError("missing controller should fail")


def test_translation_mode_validation():
    assert _translation_mode("AUTOMATIC") == "automatic"
    assert _translation_mode(" manual ") == "manual"
