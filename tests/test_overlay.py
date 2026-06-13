import pytest

from vrc_ocr_translate.config import OverlayConfig
from vrc_ocr_translate.overlay import calibration_translation


def test_converts_screen_ratio_offset_to_openvr_plane_translation():
    config = OverlayConfig(
        width_m=2.0,
        vertical_offset_m=0.1,
        position_offset_x_ratio=-0.2,
        position_offset_y_ratio=0.25,
    )

    x_m, y_m = calibration_translation(config, (1920, 1080))

    assert x_m == pytest.approx(-0.4)
    assert y_m == pytest.approx(-0.18125)
