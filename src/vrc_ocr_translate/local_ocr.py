from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np
from PIL import Image

from .config import OcrConfig
from .models import BoundingBox, OcrRegion
from .text import contains_configured_language, normalize_text

LOGGER = logging.getLogger(__name__)


class RapidJapaneseOcr:
    def __init__(self, config: OcrConfig) -> None:
        self._config = config
        try:
            from rapidocr import (
                EngineType,
                LangDet,
                LangRec,
                ModelType,
                OCRVersion,
                RapidOCR,
            )
        except ImportError as exc:
            raise RuntimeError(
                "RapidOCR is not installed. Run RUN_TRANSLATOR.bat again."
            ) from exc

        started = time.monotonic()
        params = {
            "Det.engine_type": EngineType.ONNXRUNTIME,
            "Det.lang_type": LangDet.CH,
            "Det.model_type": ModelType.MOBILE,
            "Det.ocr_version": OCRVersion.PPOCRV4,
            "Rec.engine_type": EngineType.ONNXRUNTIME,
            "Rec.lang_type": LangRec.JAPAN,
            "Rec.model_type": ModelType.MOBILE,
            "Rec.ocr_version": OCRVersion.PPOCRV4,
            "Cls.engine_type": EngineType.ONNXRUNTIME,
            "Cls.lang_type": LangDet.CH,
            "Cls.model_type": ModelType.MOBILE,
            "Cls.ocr_version": OCRVersion.PPOCRV4,
        }
        self._engine = RapidOCR(params=params)
        LOGGER.info("RapidOCR initialized on CPU in %.2fs", time.monotonic() - started)

    def recognize(self, image: Image.Image) -> list[OcrRegion]:
        original_width, original_height = image.size
        working = _fit_within_limit(image, self._config.max_dimension)
        started = time.monotonic()
        result = self._engine(np.asarray(working.convert("RGB")))
        elapsed = time.monotonic() - started

        boxes = getattr(result, "boxes", None)
        texts = getattr(result, "txts", None)
        scores = getattr(result, "scores", None)
        if boxes is None or texts is None or scores is None:
            LOGGER.info("RapidOCR: %.3fs regions=0", elapsed)
            return []

        scale_x = original_width / working.width
        scale_y = original_height / working.height
        regions: list[OcrRegion] = []
        for box, text, score in zip(boxes, texts, scores, strict=False):
            normalized = normalize_text(str(text))
            confidence = float(score)
            if (
                confidence < self._config.confidence_threshold
                or not normalized
                or not contains_configured_language(
                    normalized,
                    self._config.languages,
                    self._config.min_latin_letters,
                )
            ):
                continue
            bounds = _bounds_from_quad(box, scale_x, scale_y)
            if bounds.width < 2 or bounds.height < 2:
                continue
            regions.append(OcrRegion(normalized, confidence, bounds))

        LOGGER.info(
            "RapidOCR: %.3fs candidates=%d accepted=%d languages=%s",
            elapsed,
            len(texts),
            len(regions),
            ",".join(self._config.languages),
        )
        return regions


def _fit_within_limit(image: Image.Image, max_dimension: int) -> Image.Image:
    limit = max(640, max_dimension)
    if max(image.size) <= limit:
        return image
    scale = limit / max(image.size)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


def _bounds_from_quad(box: Any, scale_x: float, scale_y: float) -> BoundingBox:
    points = np.asarray(box, dtype=float).reshape(-1, 2)
    xs = points[:, 0]
    ys = points[:, 1]
    return BoundingBox(
        left=round(float(xs.min()) * scale_x),
        top=round(float(ys.min()) * scale_y),
        right=round(float(xs.max()) * scale_x),
        bottom=round(float(ys.max()) * scale_y),
    )
