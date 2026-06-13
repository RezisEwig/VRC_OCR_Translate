from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import OverlayConfig
from .models import ImageTranslationResult, TranslationBlock


@dataclass(slots=True)
class _Bubble:
    block: TranslationBlock
    font: ImageFont.FreeTypeFont
    font_size: int
    wrapped: str
    width: int
    height: int
    desired_left: int
    desired_top: int


class SubtitleRenderer:
    def __init__(self, config: OverlayConfig) -> None:
        self.config = config
        font_path = Path(config.font_path)
        if not font_path.exists():
            raise FileNotFoundError(f"Korean font was not found: {font_path}")
        self._font = ImageFont.truetype(str(font_path), config.font_size)

    def render(self, text: str) -> Image.Image:
        image = Image.new("RGBA", (self.config.width_px, self.config.height_px), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        margin = 28
        radius = 24
        draw.rounded_rectangle(
            (4, 4, self.config.width_px - 4, self.config.height_px - 4),
            radius=radius,
            fill=(10, 12, 18, self.config.background_alpha),
            outline=(255, 255, 255, 70),
            width=2,
        )
        wrapped = self._wrap(draw, text, self.config.width_px - margin * 2)
        bbox = draw.multiline_textbbox((0, 0), wrapped, font=self._font, spacing=10, align="center")
        text_height = bbox[3] - bbox[1]
        y = max(margin, (self.config.height_px - text_height) // 2)
        draw.multiline_text(
            (self.config.width_px // 2, y),
            wrapped,
            font=self._font,
            fill=(255, 255, 255, 255),
            anchor="ma",
            spacing=10,
            align="center",
            stroke_width=2,
            stroke_fill=(0, 0, 0, 210),
        )
        return image

    def _wrap(self, draw: ImageDraw.ImageDraw, text: str, max_width: int) -> str:
        lines: list[str] = []
        for paragraph in text.splitlines() or [""]:
            current = ""
            for char in paragraph:
                candidate = current + char
                width = draw.textlength(candidate, font=self._font)
                if current and width > max_width:
                    lines.append(current)
                    current = char
                else:
                    current = candidate
            lines.append(current)
        return "\n".join(lines[:3])


class PositionedTranslationRenderer:
    def __init__(self, config: OverlayConfig) -> None:
        self.config = config
        self._font_path = Path(config.font_path)
        if not self._font_path.exists():
            raise FileNotFoundError(f"Korean font was not found: {self._font_path}")
        self._fonts: dict[int, ImageFont.FreeTypeFont] = {}

    def render(
        self,
        result: ImageTranslationResult,
        image_size: tuple[int, int],
    ) -> Image.Image:
        image = Image.new("RGBA", image_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        occupied: list[tuple[int, int, int, int]] = []
        for block in sorted(result.blocks, key=lambda item: item.bounds.top):
            bubble = self._measure_block(draw, image_size, block)
            rectangle = self._find_position(bubble, image_size, occupied)
            self._draw_bubble(draw, bubble, rectangle)
            occupied.append(rectangle)
        return image

    def _measure_block(
        self,
        draw: ImageDraw.ImageDraw,
        image_size: tuple[int, int],
        block: TranslationBlock,
    ) -> _Bubble:
        image_width, image_height = image_size
        average_line_height = block.bounds.height / max(1, block.line_count)
        font_size = int(average_line_height * 0.82)
        font_size = max(
            self.config.min_font_size,
            min(self.config.max_font_size, font_size),
        )
        font = self._font(font_size)
        padding_x = max(10, font_size // 3)
        padding_y = max(7, font_size // 4)
        max_text_width = min(
            int(image_width * 0.55),
            max(180, int(block.bounds.width * 1.35)),
        )
        wrapped = self._wrap(draw, block.target_text, font, max_text_width)
        text_box = draw.multiline_textbbox(
            (0, 0), wrapped, font=font, spacing=max(3, font_size // 5), align="center"
        )
        text_width = math.ceil(text_box[2] - text_box[0])
        text_height = math.ceil(text_box[3] - text_box[1])
        bubble_width = min(image_width - 8, text_width + padding_x * 2)
        bubble_height = min(image_height - 8, text_height + padding_y * 2)

        source_center_x = (block.bounds.left + block.bounds.right) / 2
        source_center_y = (block.bounds.top + block.bounds.bottom) / 2
        center_x = round(
            image_width
            * (
                0.5
                + (source_center_x / image_width - 0.5) * self.config.position_scale_x
                + self.config.position_offset_x_ratio
            )
        )
        center_y = round(
            image_height
            * (
                0.5
                + (source_center_y / image_height - 0.5) * self.config.position_scale_y
                + self.config.position_offset_y_ratio
            )
        )
        left = max(4, min(image_width - bubble_width - 4, center_x - bubble_width // 2))
        top = max(4, min(image_height - bubble_height - 4, center_y - bubble_height // 2))
        return _Bubble(
            block=block,
            font=font,
            font_size=font_size,
            wrapped=wrapped,
            width=bubble_width,
            height=bubble_height,
            desired_left=left,
            desired_top=top,
        )

    def _find_position(
        self,
        bubble: _Bubble,
        image_size: tuple[int, int],
        occupied: list[tuple[int, int, int, int]],
    ) -> tuple[int, int, int, int]:
        image_width, image_height = image_size
        margin = 4
        max_left = max(margin, image_width - bubble.width - margin)
        max_top = max(margin, image_height - bubble.height - margin)
        gap = max(0, self.config.collision_gap_px)

        x_step = max(24, bubble.width // 4)
        y_step = max(18, bubble.height // 2)
        x_values = list(range(margin, max_left + 1, x_step)) + [
            bubble.desired_left,
            max_left,
        ]
        y_values = list(range(margin, max_top + 1, y_step)) + [
            bubble.desired_top,
            max_top,
        ]
        candidates = {
            (
                max(margin, min(max_left, left)),
                max(margin, min(max_top, top)),
            )
            for left in x_values
            for top in y_values
        }
        ordered = sorted(
            candidates,
            key=lambda point: (
                (point[0] - bubble.desired_left) ** 2
                + (point[1] - bubble.desired_top) ** 2
            ),
        )

        best: tuple[int, int, int, int] | None = None
        best_overlap: int | None = None
        for left, top in ordered:
            rectangle = (left, top, left + bubble.width, top + bubble.height)
            overlap = sum(_overlap_area(rectangle, other, gap) for other in occupied)
            if overlap == 0:
                return rectangle
            if best_overlap is None or overlap < best_overlap:
                best = rectangle
                best_overlap = overlap
        return best or (
            bubble.desired_left,
            bubble.desired_top,
            bubble.desired_left + bubble.width,
            bubble.desired_top + bubble.height,
        )

    def _draw_bubble(
        self,
        draw: ImageDraw.ImageDraw,
        bubble: _Bubble,
        rectangle: tuple[int, int, int, int],
    ) -> None:
        left, top, right, bottom = rectangle

        draw.rounded_rectangle(
            (left, top, right, bottom),
            radius=max(8, bubble.font_size // 3),
            fill=(8, 10, 16, self.config.background_alpha),
            outline=(255, 255, 255, 100),
            width=2,
        )
        draw.multiline_text(
            ((left + right) // 2, (top + bottom) // 2),
            bubble.wrapped,
            font=bubble.font,
            fill=(255, 255, 255, 255),
            anchor="mm",
            spacing=max(3, bubble.font_size // 5),
            align="center",
            stroke_width=max(1, bubble.font_size // 24),
            stroke_fill=(0, 0, 0, 230),
        )

    def _font(self, size: int) -> ImageFont.FreeTypeFont:
        if size not in self._fonts:
            self._fonts[size] = ImageFont.truetype(str(self._font_path), size)
        return self._fonts[size]

    @staticmethod
    def _wrap(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
    ) -> str:
        lines: list[str] = []
        current = ""
        for char in text:
            candidate = current + char
            if current and draw.textlength(candidate, font=font) > max_width:
                lines.append(current)
                current = char
            else:
                current = candidate
        if current:
            lines.append(current)
        return "\n".join(lines or [text])


def _overlap_area(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
    gap: int = 0,
) -> int:
    left = max(first[0], second[0] - gap)
    top = max(first[1], second[1] - gap)
    right = min(first[2], second[2] + gap)
    bottom = min(first[3], second[3] + gap)
    return max(0, right - left) * max(0, bottom - top)
