import pytest

from vrc_ocr_translate.capture import ScreenCapture, VRChatWindowCapture, create_capture
from vrc_ocr_translate.config import CaptureConfig


def test_selects_vrchat_window_capture_by_default():
    capture = create_capture(CaptureConfig())
    assert isinstance(capture, VRChatWindowCapture)


def test_selects_monitor_capture_when_explicitly_configured():
    capture = create_capture(CaptureConfig(source="monitor"))
    try:
        assert isinstance(capture, ScreenCapture)
    finally:
        capture.close()


def test_rejects_unknown_capture_source():
    with pytest.raises(ValueError, match="capture.source"):
        create_capture(CaptureConfig(source="unknown"))


def test_rejects_unreliable_steamvr_mirror_source():
    with pytest.raises(ValueError, match="InvalidTexture"):
        create_capture(CaptureConfig(source="steamvr_mirror"))
