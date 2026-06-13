from PIL import Image

from vrc_ocr_translate.change_detection import FrameChangeDetector


def test_skips_identical_frames_and_accepts_changed_frames():
    detector = FrameChangeDetector(2.5)
    black = Image.new("RGB", (320, 180), "black")
    white = Image.new("RGB", (320, 180), "white")
    assert detector.changed(black)[0]
    assert not detector.changed(black)[0]
    assert detector.changed(white)[0]
