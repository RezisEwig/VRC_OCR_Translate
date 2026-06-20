from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np
from PIL import Image

from .config import OcrConfig
from .languages import AUTO_SOURCE_LANGUAGE, normalize_source_language
from .models import BoundingBox, OcrRegion
from .text import (
    contains_configured_language,
    normalize_text,
    script_counts,
)

LOGGER = logging.getLogger(__name__)


class RapidMultilingualOcr:
    PACK_JAPANESE = "japanese"
    PACK_EAST_ASIA = "east_asia"
    PACK_KOREAN = "korean"
    PACK_LATIN = "latin"

    def __init__(
        self,
        config: OcrConfig,
        source_language: str = AUTO_SOURCE_LANGUAGE,
    ) -> None:
        self._config = config
        self._source_language = normalize_source_language(source_language)
        try:
            from rapidocr import (
                EngineType,
                LangCls,
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

        self._rapid_ocr = RapidOCR
        self._base_params = {
            "Det.engine_type": EngineType.ONNXRUNTIME,
            "Det.lang_type": LangDet.CH,
            "Det.model_type": ModelType.MOBILE,
            "Det.ocr_version": OCRVersion.PPOCRV5,
            "Cls.engine_type": EngineType.ONNXRUNTIME,
            "Cls.lang_type": LangCls.CH,
            "Cls.model_type": ModelType.MOBILE,
            "Cls.ocr_version": OCRVersion.PPOCRV5,
            "Rec.engine_type": EngineType.ONNXRUNTIME,
            "Rec.model_type": ModelType.MOBILE,
            "Rec.ocr_version": OCRVersion.PPOCRV5,
        }
        started = time.monotonic()
        self._detector = RapidOCR(
            params={
                **self._base_params,
                "Global.use_rec": False,
                "Rec.lang_type": LangRec.CH,
            }
        )
        self._recognizer_languages = {
            self.PACK_JAPANESE: LangRec.JAPAN,
            self.PACK_EAST_ASIA: LangRec.CH,
            self.PACK_KOREAN: LangRec.KOREAN,
            self.PACK_LATIN: LangRec.LATIN,
        }
        self._recognizer_versions = {
            self.PACK_JAPANESE: OCRVersion.PPOCRV4,
            self.PACK_EAST_ASIA: OCRVersion.PPOCRV5,
            self.PACK_KOREAN: OCRVersion.PPOCRV5,
            self.PACK_LATIN: OCRVersion.PPOCRV5,
        }
        self._recognizers = {self.PACK_EAST_ASIA: self._detector}
        for pack in self._active_packs():
            self._get_recognizer(pack)
        LOGGER.info(
            "RapidOCR multilingual models initialized on CPU in %.2fs: %s",
            time.monotonic() - started,
            ",".join(self._active_packs()),
        )

    def set_source_language(self, language_code: str) -> None:
        normalized = normalize_source_language(language_code)
        if normalized == self._source_language:
            return
        self._source_language = normalized
        for pack in self._active_packs():
            self._get_recognizer(pack)
        LOGGER.info(
            "OCR source language changed: %s packs=%s",
            normalized,
            ",".join(self._active_packs()),
        )

    def _active_packs(self) -> tuple[str, ...]:
        return _recognition_packs_for_language(self._source_language)

    def _get_recognizer(self, pack: str) -> Any:
        recognizer = self._recognizers.get(pack)
        if recognizer is not None:
            return recognizer
        recognizer = self._rapid_ocr(
            params={
                **self._base_params,
                "Global.use_det": False,
                "Global.use_cls": False,
                "Rec.lang_type": self._recognizer_languages[pack],
                "Rec.ocr_version": self._recognizer_versions[pack],
            }
        )
        self._recognizers[pack] = recognizer
        return recognizer

    def recognize(self, image: Image.Image) -> list[OcrRegion]:
        original_width, original_height = image.size
        working = _fit_within_limit(image, self._config.max_dimension)
        working_array = np.asarray(working.convert("RGB"))
        started = time.monotonic()
        detection = self._detector(
            working_array,
            use_det=True,
            use_cls=False,
            use_rec=False,
        )
        boxes = getattr(detection, "boxes", None)
        if boxes is None or len(boxes) == 0:
            LOGGER.info("RapidOCR multilingual: %.3fs regions=0", time.monotonic() - started)
            return []

        crops = self._detector.crop_text_regions(working_array, np.asarray(boxes))
        try:
            crops, _classification = self._detector.cls_and_rotate(crops)
        except Exception:
            LOGGER.debug("RapidOCR orientation classification failed", exc_info=True)

        pack_results: dict[str, tuple[tuple[str, ...], tuple[float, ...]]] = {}
        active_packs = self._active_packs()
        for pack in active_packs:
            recognizer = self._get_recognizer(pack)
            result = recognizer.recognize_txt(crops)
            texts = tuple(getattr(result, "txts", ()) or ())
            scores = tuple(float(score) for score in (getattr(result, "scores", ()) or ()))
            pack_results[pack] = (texts, scores)

        scale_x = original_width / working.width
        scale_y = original_height / working.height
        regions: list[OcrRegion] = []
        wins = {
            self.PACK_JAPANESE: 0,
            self.PACK_EAST_ASIA: 0,
            self.PACK_KOREAN: 0,
            self.PACK_LATIN: 0,
        }
        for index, box in enumerate(boxes):
            candidates: list[tuple[str, str, float]] = []
            for pack, (texts, scores) in pack_results.items():
                if index >= len(texts) or index >= len(scores):
                    continue
                text = normalize_text(texts[index])
                confidence = scores[index]
                if text:
                    candidates.append((pack, text, confidence))
            selected = _select_candidate(candidates)
            if selected is None:
                continue
            pack, text, confidence = selected
            if confidence < self._config.confidence_threshold:
                continue
            if not self._accept_text(text):
                continue
            bounds = _bounds_from_quad(box, scale_x, scale_y)
            if bounds.width < 2 or bounds.height < 2:
                continue
            wins[pack] += 1
            regions.append(OcrRegion(text, confidence, bounds))

        elapsed = time.monotonic() - started
        LOGGER.info(
            "RapidOCR multilingual: %.3fs candidates=%d accepted=%d "
            "packs=japanese:%d,east_asia:%d,korean:%d,latin:%d",
            elapsed,
            len(boxes),
            len(regions),
            wins[self.PACK_JAPANESE],
            wins[self.PACK_EAST_ASIA],
            wins[self.PACK_KOREAN],
            wins[self.PACK_LATIN],
        )
        return regions

    def _accept_text(self, text: str) -> bool:
        if self._source_language != AUTO_SOURCE_LANGUAGE:
            return contains_configured_language(
                text,
                [self._source_language],
                self._config.min_latin_letters,
            )
        if self._config.auto_detect_languages:
            counts = script_counts(text)
            return (
                counts["hangul"] > 0
                or counts["kana"] > 0
                or counts["cjk"] > 0
                or counts["latin"] >= max(1, self._config.min_latin_letters)
            )
        return contains_configured_language(
            text,
            self._config.languages,
            self._config.min_latin_letters,
        )


RapidJapaneseOcr = RapidMultilingualOcr


def _recognition_packs_for_language(language_code: str) -> tuple[str, ...]:
    normalized = normalize_source_language(language_code)
    if normalized == AUTO_SOURCE_LANGUAGE:
        return (
            RapidMultilingualOcr.PACK_JAPANESE,
            RapidMultilingualOcr.PACK_EAST_ASIA,
            RapidMultilingualOcr.PACK_KOREAN,
            RapidMultilingualOcr.PACK_LATIN,
        )
    if normalized == "ko":
        return (RapidMultilingualOcr.PACK_KOREAN,)
    if normalized == "ja":
        return (RapidMultilingualOcr.PACK_JAPANESE,)
    if normalized in {"zh-CN", "zh-TW"}:
        return (RapidMultilingualOcr.PACK_EAST_ASIA,)
    return (RapidMultilingualOcr.PACK_LATIN,)


def _select_candidate(
    candidates: list[tuple[str, str, float]],
) -> tuple[str, str, float] | None:
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda candidate: _candidate_score(*candidate),
    )


def _candidate_score(pack: str, text: str, confidence: float) -> float:
    counts = script_counts(text)
    score = confidence
    if pack == RapidMultilingualOcr.PACK_JAPANESE:
        if counts["kana"]:
            score += 0.35
        elif counts["cjk"]:
            score += 0.15
        if counts["hangul"]:
            score -= 0.40
    elif pack == RapidMultilingualOcr.PACK_EAST_ASIA:
        if counts["cjk"]:
            score += 0.25
        elif counts["kana"]:
            score += 0.10
        if counts["hangul"]:
            score -= 0.40
    elif pack == RapidMultilingualOcr.PACK_KOREAN:
        if counts["hangul"]:
            score += 0.30
        if counts["kana"] or counts["cjk"]:
            score -= 0.35
    elif pack == RapidMultilingualOcr.PACK_LATIN:
        if counts["latin"]:
            score += 0.15
        if counts["hangul"] or counts["kana"] or counts["cjk"]:
            score -= 0.50
    return score


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
