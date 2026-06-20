from PIL import Image, ImageDraw

from vrc_ocr_translate.config import OverlayConfig
from vrc_ocr_translate.models import (
    BoundingBox,
    ImageTranslationResult,
    TranslationBlock,
)
from vrc_ocr_translate.renderer import PositionedTranslationRenderer, _Bubble, _overlap_area


def test_renders_translation_near_source_bounds():
    result = ImageTranslationResult(
        source_language="ja",
        target_language="ko",
        blocks=(
            TranslationBlock(
                source_text="ようこそ",
                target_text="어서 오세요",
                bounds=BoundingBox(200, 100, 500, 180),
            ),
        ),
    )
    config = OverlayConfig(
        position_offset_x_ratio=0.0,
        position_offset_y_ratio=0.0,
    )
    image = PositionedTranslationRenderer(config).render(result, (800, 450))
    assert image.mode == "RGBA"
    assert image.getbbox() is not None
    assert image.getpixel((350, 140))[3] > 0


def test_applies_hmd_position_scale_to_source_coordinates():
    result = ImageTranslationResult(
        source_language="ja",
        target_language="ko",
        blocks=(
            TranslationBlock(
                source_text="出口",
                target_text="출구",
                bounds=BoundingBox(180, 80, 220, 120),
            ),
        ),
    )
    config = OverlayConfig(
        position_scale_x=2.0,
        position_scale_y=2.0,
        position_offset_x_ratio=0.0,
        position_offset_y_ratio=0.0,
        min_font_size=18,
        max_font_size=18,
    )

    image = PositionedTranslationRenderer(config).render(result, (800, 400))

    assert image.getpixel((20, 20))[3] > 0
    assert image.getpixel((200, 100))[3] == 0


def test_places_overlapping_subtitle_boxes_in_separate_spaces():
    renderer = PositionedTranslationRenderer(OverlayConfig(collision_gap_px=12))
    font = renderer._font(24)
    first = _Bubble(
        TranslationBlock("一", "첫 번째", BoundingBox(100, 100, 200, 140)),
        font,
        24,
        "첫 번째",
        240,
        80,
        300,
        180,
    )
    second = _Bubble(
        TranslationBlock("二", "두 번째", BoundingBox(100, 100, 200, 140)),
        font,
        24,
        "두 번째",
        240,
        80,
        300,
        180,
    )
    first_rect = renderer._find_position(first, (800, 450), [])
    second_rect = renderer._find_position(second, (800, 450), [first_rect])

    assert _overlap_area(first_rect, second_rect, 12) == 0


def test_measured_bubble_coordinates_are_integers_at_vrchat_resolution():
    renderer = PositionedTranslationRenderer(OverlayConfig())
    image = Image.new("RGBA", (1920, 1009))
    bubble = renderer._measure_block(
        ImageDraw.Draw(image),
        image.size,
        TranslationBlock(
            "source",
            "translated subtitle",
            BoundingBox(1300, 70, 1750, 340),
        ),
    )

    assert isinstance(bubble.width, int)
    assert isinstance(bubble.height, int)
    assert isinstance(bubble.desired_left, int)
    assert isinstance(bubble.desired_top, int)


def test_tiny_source_text_uses_compact_default_subtitle_bubble():
    renderer = PositionedTranslationRenderer(OverlayConfig())
    image = Image.new("RGBA", (1920, 1009))
    bubble = renderer._measure_block(
        ImageDraw.Draw(image),
        image.size,
        TranslationBlock(
            "tiny",
            "작은 글씨",
            BoundingBox(800, 400, 840, 406),
        ),
    )

    assert bubble.font_size == 10
    assert bubble.height < 30


def test_dense_paragraph_uses_character_density_instead_of_box_height():
    renderer = PositionedTranslationRenderer(OverlayConfig())
    block = TranslationBlock(
        "小さい文字" * 60,
        "작은 글씨로 된 긴 문단입니다. " * 30,
        BoundingBox(800, 350, 1769, 420),
    )

    font_size = renderer._estimate_font_size(block)

    assert font_size <= 18
    assert font_size < int(block.bounds.height * 0.82)
