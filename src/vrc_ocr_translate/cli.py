from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

from .app import TranslationOverlayApp
from .capture import ScreenCapture, create_capture
from .config import AppConfig, load_config
from .local_ocr import RapidJapaneseOcr
from .local_pipeline import LocalImageTranslator
from .local_translation import LlamaServer, TranslateGemmaTranslator
from .overlay import SteamVROverlay
from .renderer import PositionedTranslationRenderer, SubtitleRenderer


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VRChat Japanese OCR translation overlay")
    parser.add_argument("--config", default="config.json", help="JSON configuration path")
    parser.add_argument("--list-monitors", action="store_true", help="list capture monitors")
    parser.add_argument("--demo-overlay", action="store_true", help="show a SteamVR test subtitle")
    parser.add_argument("--render-demo", metavar="PATH", help="render a test subtitle PNG")
    parser.add_argument("--capture-preview", metavar="PATH", help="save the configured capture area")
    parser.add_argument("--check-local", action="store_true", help="test local GPU translation")
    parser.add_argument("--ocr-image", metavar="PATH", help="run RapidOCR on an image")
    parser.add_argument(
        "--translate-image",
        metavar="PATH",
        help="translate an image and save a positioned overlay preview",
    )
    return parser


def _demo_image(config: AppConfig):
    return SubtitleRenderer(config.overlay).render(
        "Positioned translation overlay test\nSteamVR connection is working."
    )


def _configure_logging() -> Path:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / "vrc-ocr-translate.log"
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console, file_handler],
        force=True,
    )
    return log_path


def main() -> None:
    args = _parser().parse_args()
    log_path = _configure_logging()
    logging.getLogger(__name__).info("Log file: %s", log_path.resolve())
    config = load_config(args.config)

    if args.check_local:
        server = LlamaServer(config.translation)
        with server:
            translated = TranslateGemmaTranslator(config.translation, server).translate(
                "謎の美術館へようこそ。出口を探してください。"
            )
        print(f"TranslateGemma OK: {translated}")
        RapidJapaneseOcr(config.ocr)
        print("RapidOCR OK")
        return
    if args.list_monitors:
        with ScreenCapture(config.capture) as capture:
            for index, monitor in enumerate(capture.monitors):
                print(f"{index}: {monitor}")
        return
    if args.render_demo:
        output = Path(args.render_demo).resolve()
        _demo_image(config).save(output)
        print(output)
        return
    if args.capture_preview:
        output = Path(args.capture_preview).resolve()
        with create_capture(config.capture) as capture:
            capture.grab().save(output)
        print(output)
        return
    if args.ocr_image:
        from PIL import Image

        with Image.open(args.ocr_image) as image:
            observations = RapidJapaneseOcr(config.ocr).recognize(image.convert("RGB"))
        print(
            json.dumps(
                [
                    {
                        "text": item.text,
                        "confidence": item.confidence,
                        "bounds": {
                            "left": item.bounds.left,
                            "top": item.bounds.top,
                            "right": item.bounds.right,
                            "bottom": item.bounds.bottom,
                        },
                    }
                    for item in observations
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    if args.translate_image:
        from PIL import Image

        source = Path(args.translate_image)
        with Image.open(source) as image:
            frame = image.convert("RGB")
        with LocalImageTranslator(config) as translator:
            result = translator.translate(frame)
        output = source.with_name(f"{source.stem}-translated-overlay.png").resolve()
        PositionedTranslationRenderer(config.overlay).render(result, frame.size).save(output)
        print(f"blocks={len(result.blocks)}")
        print(output)
        return
    if args.demo_overlay:
        with SteamVROverlay(config.overlay) as overlay:
            overlay.show(_demo_image(config))
            print("Test overlay is visible for 15 seconds.")
            time.sleep(15)
        return

    try:
        TranslationOverlayApp(config, args.config).run()
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Stopped by user")
    except Exception:
        logging.getLogger(__name__).exception("Application stopped")
        sys.exit(1)


if __name__ == "__main__":
    main()
