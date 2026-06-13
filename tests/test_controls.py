import json
from types import SimpleNamespace

import openvr

from vrc_ocr_translate.app import _translation_mode
from vrc_ocr_translate.controls import SteamVRControllerInput


class _FakeVRInput:
    def __init__(self):
        self.manifest_path = None
        self.states = {101: False, 102: False}
        self.update_count = 0

    def setActionManifestPath(self, path):
        self.manifest_path = path

    def getActionSetHandle(self, _name):
        return 100

    def getActionHandle(self, name):
        return 101 if name.endswith("/translate") else 102

    def updateActionState(self, _sets):
        self.update_count += 1

    def getDigitalActionData(self, handle, _device):
        return SimpleNamespace(bActive=True, bState=self.states[handle])


class _FakeOpenVR:
    VRActiveActionSet_t = openvr.VRActiveActionSet_t
    k_ulInvalidInputValueHandle = openvr.k_ulInvalidInputValueHandle
    k_ulInvalidActionSetHandle = openvr.k_ulInvalidActionSetHandle
    k_nActionSetOverlayGlobalPriorityMin = (
        openvr.k_nActionSetOverlayGlobalPriorityMin
    )

    def __init__(self, vr_input):
        self._vr_input = vr_input

    def VRInput(self):
        return self._vr_input


def test_controller_buttons_emit_only_on_rising_edge(tmp_path):
    manifest = tmp_path / "actions.json"
    manifest.write_text("{}", encoding="utf-8")
    fake_input = _FakeVRInput()
    controls = SteamVRControllerInput(
        manifest,
        openvr_module=_FakeOpenVR(fake_input),
    )
    controls.start()

    assert not controls.poll().translate
    fake_input.states[101] = True
    assert controls.poll().translate
    assert not controls.poll().translate
    fake_input.states[101] = False
    assert not controls.poll().translate
    fake_input.states[102] = True
    assert controls.poll().clear


def test_controller_button_held_during_start_does_not_emit(tmp_path):
    manifest = tmp_path / "actions.json"
    manifest.write_text("{}", encoding="utf-8")
    fake_input = _FakeVRInput()
    fake_input.states[102] = True
    controls = SteamVRControllerInput(
        manifest,
        openvr_module=_FakeOpenVR(fake_input),
    )

    controls.start()

    assert not controls.poll().clear
    fake_input.states[102] = False
    assert not controls.poll().clear
    fake_input.states[102] = True
    assert controls.poll().clear


def test_action_manifest_binds_left_trigger_and_grip():
    directory = SteamVRControllerInput.default_manifest_path().parent
    manifest = json.loads((directory / "actions.json").read_text(encoding="utf-8"))
    controller_types = {item["controller_type"] for item in manifest["default_bindings"]}
    assert "vd_hand_controller" in controller_types
    assert "oculus_touch" in controller_types

    for item in manifest["default_bindings"]:
        binding = json.loads(
            (directory / item["binding_url"]).read_text(encoding="utf-8")
        )
        paths = {
            source["path"]
            for source in binding["bindings"]["/actions/translation"]["sources"]
        }
        assert "/user/hand/left/input/trigger" in paths
        assert "/user/hand/left/input/grip" in paths


def test_translation_mode_validation():
    assert _translation_mode("AUTOMATIC") == "automatic"
    assert _translation_mode(" manual ") == "manual"
