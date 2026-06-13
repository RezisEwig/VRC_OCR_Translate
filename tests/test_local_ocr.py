from vrc_ocr_translate.local_ocr import _bounds_from_quad
from vrc_ocr_translate.models import BoundingBox


def test_restores_ocr_quad_to_original_image_coordinates():
    bounds = _bounds_from_quad(
        [[10, 20], [100, 20], [100, 50], [10, 50]],
        scale_x=2.0,
        scale_y=1.5,
    )
    assert bounds == BoundingBox(20, 30, 200, 75)
