from vrc_ocr_translate.local_ocr import (
    RapidMultilingualOcr,
    _bounds_from_quad,
    _recognition_packs_for_language,
    _select_candidate,
)
from vrc_ocr_translate.models import BoundingBox


def test_restores_ocr_quad_to_original_image_coordinates():
    bounds = _bounds_from_quad(
        [[10, 20], [100, 20], [100, 50], [10, 50]],
        scale_x=2.0,
        scale_y=1.5,
    )
    assert bounds == BoundingBox(20, 30, 200, 75)


def test_selects_recognizer_matching_detected_script():
    assert _select_candidate(
        [
            (RapidMultilingualOcr.PACK_JAPANESE, "出口はこちら", 0.81),
            (RapidMultilingualOcr.PACK_EAST_ASIA, "出口はこちら", 0.82),
            (RapidMultilingualOcr.PACK_KOREAN, "출구", 0.70),
            (RapidMultilingualOcr.PACK_LATIN, "EH", 0.75),
        ]
    ) == (RapidMultilingualOcr.PACK_JAPANESE, "出口はこちら", 0.81)

    assert _select_candidate(
        [
            (RapidMultilingualOcr.PACK_EAST_ASIA, "望咀", 0.71),
            (RapidMultilingualOcr.PACK_KOREAN, "환영합니다", 0.80),
            (RapidMultilingualOcr.PACK_LATIN, "g", 0.66),
        ]
    ) == (RapidMultilingualOcr.PACK_KOREAN, "환영합니다", 0.80)

    assert _select_candidate(
        [
            (RapidMultilingualOcr.PACK_EAST_ASIA, "Espafiol", 0.73),
            (RapidMultilingualOcr.PACK_KOREAN, "Espafiol", 0.72),
            (RapidMultilingualOcr.PACK_LATIN, "Español", 0.88),
        ]
    ) == (RapidMultilingualOcr.PACK_LATIN, "Español", 0.88)


def test_selects_only_the_needed_recognizer_pack_for_fixed_source_language():
    assert _recognition_packs_for_language("auto") == (
        RapidMultilingualOcr.PACK_JAPANESE,
        RapidMultilingualOcr.PACK_EAST_ASIA,
        RapidMultilingualOcr.PACK_KOREAN,
        RapidMultilingualOcr.PACK_LATIN,
    )
    assert _recognition_packs_for_language("ko") == (
        RapidMultilingualOcr.PACK_KOREAN,
    )
    assert _recognition_packs_for_language("ja") == (
        RapidMultilingualOcr.PACK_JAPANESE,
    )
    assert _recognition_packs_for_language("zh-CN") == (
        RapidMultilingualOcr.PACK_EAST_ASIA,
    )
    assert _recognition_packs_for_language("fr") == (
        RapidMultilingualOcr.PACK_LATIN,
    )
