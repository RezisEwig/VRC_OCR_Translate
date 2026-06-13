import json

import pytest

from vrc_ocr_translate.config import OverlayConfig, load_config, save_overlay_calibration


def test_loads_defaults_when_file_does_not_exist(tmp_path):
    config = load_config(tmp_path / "missing.json")
    assert config.capture.monitor == 1
    assert config.capture.source == "vrchat_window"
    assert config.overlay.position_offset_x_ratio == -0.1
    assert config.overlay.position_offset_y_ratio == 0.12
    assert config.capture.interval_ms == 2000
    assert config.controls.start_mode == "automatic"
    assert config.controls.poll_interval_ms == 50
    assert config.ocr.max_dimension == 1920
    assert config.ocr.languages == ["ja", "en"]
    assert config.translation.local_gpu_layers == "all"


def test_rejects_unknown_setting(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"capture": {"unknown": 1}}), encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown capture settings"):
        load_config(path)


def test_saves_calibration_without_removing_other_settings(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "translation": {"local_max_tokens": 128},
                "overlay": {"background_alpha": 170},
            }
        ),
        encoding="utf-8",
    )

    save_overlay_calibration(
        path,
        OverlayConfig(position_offset_x_ratio=-0.12, position_offset_y_ratio=0.08),
    )

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["translation"]["local_max_tokens"] == 128
    assert data["overlay"]["background_alpha"] == 170
    assert data["overlay"]["position_offset_x_ratio"] == -0.12
    assert data["overlay"]["position_offset_y_ratio"] == 0.08
