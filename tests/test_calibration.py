import json

import pytest

from vrc_ocr_translate.calibration import PositionCalibrationController
from vrc_ocr_translate.config import (
    DEFAULT_POSITION_OFFSET_X_RATIO,
    DEFAULT_POSITION_OFFSET_Y_RATIO,
    OverlayConfig,
)


def test_move_command_updates_offsets_and_saves_config(tmp_path):
    path = tmp_path / "config.json"
    config = OverlayConfig(
        position_offset_x_ratio=-0.1,
        position_offset_y_ratio=0.12,
        calibration_step_ratio=0.02,
    )
    calibration = PositionCalibrationController(config, path)

    assert calibration.move(x_steps=1, y_steps=-1)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert config.position_offset_x_ratio == pytest.approx(-0.08)
    assert config.position_offset_y_ratio == pytest.approx(0.10)
    assert data["overlay"]["position_offset_x_ratio"] == -0.08
    assert data["overlay"]["position_offset_y_ratio"] == 0.1


def test_scale_and_reset_commands_update_saved_calibration(tmp_path):
    path = tmp_path / "config.json"
    config = OverlayConfig(
        position_offset_x_ratio=0.2,
        position_offset_y_ratio=-0.2,
        position_scale_x=1.0,
        position_scale_y=1.0,
        calibration_step_ratio=0.02,
    )
    calibration = PositionCalibrationController(config, path)

    assert calibration.scale(1)
    assert config.position_scale_x == pytest.approx(1.02)
    assert config.position_scale_y == pytest.approx(1.02)

    assert calibration.reset()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert config.position_offset_x_ratio == DEFAULT_POSITION_OFFSET_X_RATIO
    assert config.position_offset_y_ratio == DEFAULT_POSITION_OFFSET_Y_RATIO
    assert data["overlay"]["position_scale_x"] == 1.0
    assert data["overlay"]["position_scale_y"] == 1.0


def test_move_command_clamps_offsets(tmp_path):
    config = OverlayConfig(
        position_offset_x_ratio=0.49,
        position_offset_y_ratio=-0.49,
        calibration_step_ratio=0.05,
    )
    calibration = PositionCalibrationController(config, tmp_path / "config.json")

    assert calibration.move(x_steps=1, y_steps=-1)

    assert config.position_offset_x_ratio == 0.5
    assert config.position_offset_y_ratio == -0.5
