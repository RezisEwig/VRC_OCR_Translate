from __future__ import annotations

import logging
import time

from PIL import Image

from .config import AppConfig
from .grouping import group_ocr_lines
from .local_ocr import RapidJapaneseOcr
from .local_translation import LlamaServer, TranslateGemmaTranslator
from .models import ImageTranslationResult, TranslationBlock

LOGGER = logging.getLogger(__name__)


class LocalImageTranslator:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._ocr = RapidJapaneseOcr(config.ocr)
        self._server = LlamaServer(config.translation)
        self._translator = TranslateGemmaTranslator(config.translation, self._server)

    def start(self) -> None:
        self._server.start()

    def close(self) -> None:
        self._server.close()

    def translate(self, image: Image.Image) -> ImageTranslationResult:
        started = time.monotonic()
        raw_regions = self._ocr.recognize(image)
        regions = group_ocr_lines(
            raw_regions,
            eps=self._config.ocr.line_cluster_eps,
            max_gap_ratio=self._config.ocr.line_max_gap_ratio,
        )
        LOGGER.info(
            "OCR grouping: raw=%d lines=%d",
            len(raw_regions),
            len(regions),
        )

        blocks: list[TranslationBlock] = []
        for region in regions:
            try:
                translated = self._translator.translate(region.text)
            except Exception:
                LOGGER.exception("Local translation failed for: %s", region.text)
                continue
            blocks.append(
                TranslationBlock(
                    source_text=region.text,
                    target_text=translated,
                    bounds=region.bounds,
                    line_count=1,
                )
            )
        LOGGER.info(
            "Local OCR/translation cycle: %.3fs blocks=%d",
            time.monotonic() - started,
            len(blocks),
        )
        return ImageTranslationResult("ja", "ko", tuple(blocks))

    def __enter__(self) -> "LocalImageTranslator":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
