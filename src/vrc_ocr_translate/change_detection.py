from __future__ import annotations

from PIL import Image, ImageChops, ImageStat


class FrameChangeDetector:
    def __init__(self, threshold: float) -> None:
        self.threshold = max(0.0, threshold)
        self._previous: Image.Image | None = None

    def changed(self, image: Image.Image) -> tuple[bool, float]:
        sample = image.convert("L").resize((64, 36))
        if self._previous is None:
            self._previous = sample
            return True, 255.0
        difference = ImageChops.difference(sample, self._previous)
        score = float(ImageStat.Stat(difference).mean[0])
        if score >= self.threshold:
            self._previous = sample
            return True, score
        return False, score
