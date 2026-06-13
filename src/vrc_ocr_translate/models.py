from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoundingBox:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)


@dataclass(frozen=True, slots=True)
class OcrRegion:
    text: str
    confidence: float
    bounds: BoundingBox


@dataclass(frozen=True, slots=True)
class TranslationBlock:
    source_text: str
    target_text: str
    bounds: BoundingBox
    line_count: int = 1


@dataclass(frozen=True, slots=True)
class ImageTranslationResult:
    source_language: str
    target_language: str
    blocks: tuple[TranslationBlock, ...]
