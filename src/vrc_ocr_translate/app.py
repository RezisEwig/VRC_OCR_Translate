from __future__ import annotations

import logging
import time
from contextlib import ExitStack
from typing import Any

from .calibration import PositionCalibrationController
from .capture import create_capture
from .change_detection import FrameChangeDetector
from .config import AppConfig
from .controls import ControlEvents, KeyboardModeToggle, SteamVRControllerInput
from .local_pipeline import LocalImageTranslator
from .overlay import SteamVROverlay
from .renderer import PositionedTranslationRenderer

LOGGER = logging.getLogger(__name__)


def _translation_mode(value: str) -> str:
    mode = value.strip().lower()
    if mode not in {"automatic", "manual"}:
        raise ValueError("controls.start_mode must be 'automatic' or 'manual'")
    return mode


class TranslationOverlayApp:
    def __init__(self, config: AppConfig, config_path: str = "config.json") -> None:
        self.config = config
        self.config_path = config_path

    def run(self) -> None:
        renderer = PositionedTranslationRenderer(self.config.overlay)
        detector = FrameChangeDetector(self.config.capture.change_threshold)
        automatic_interval = max(0.1, self.config.capture.interval_ms / 1000)
        poll_interval = max(0.02, self.config.controls.poll_interval_ms / 1000)
        calibration_interval = max(
            0.25,
            self.config.controls.calibration_translate_interval_ms / 1000,
        )
        mode = _translation_mode(self.config.controls.start_mode)
        previous_signature: tuple[tuple[object, ...], ...] = ()
        last_result: Any = None
        last_frame_size: tuple[int, int] | None = None
        skipped_frames = 0
        last_status_at = 0.0
        last_input_error_at = 0.0
        last_calibration_translation_at = float("-inf")
        next_automatic_at = time.monotonic()
        calibration = PositionCalibrationController(self.config.overlay, self.config_path)
        keyboard_toggle = KeyboardModeToggle()

        with ExitStack() as stack:
            translator: Any = stack.enter_context(LocalImageTranslator(self.config))
            overlay = stack.enter_context(SteamVROverlay(self.config.overlay))
            controller_input: SteamVRControllerInput | None
            try:
                controller_input = SteamVRControllerInput()
                controller_input.start()
            except Exception:
                controller_input = None
                LOGGER.exception(
                    "SteamVR controller input could not start; keyboard controls remain available"
                )
            capture = stack.enter_context(
                create_capture(self.config.capture, openvr_initialized=True)
            )
            LOGGER.info(
                "Positioned translation started: capture=%s mode=%s interval=%dms",
                self.config.capture.source,
                mode,
                self.config.capture.interval_ms,
            )
            LOGGER.info(
                "Controls: left trigger=translate, left grip=clear, Ctrl+Alt+T=toggle auto/manual"
            )
            LOGGER.info(
                "Position keys: Ctrl+Alt+arrows move, numpad +/- scales, Home resets"
            )
            LOGGER.info("Press Ctrl+C to stop.")

            while True:
                loop_started = time.monotonic()
                events = ControlEvents()
                if controller_input is not None:
                    try:
                        events = controller_input.poll()
                    except Exception:
                        now = time.monotonic()
                        if now - last_input_error_at >= 5.0:
                            LOGGER.exception("SteamVR controller input polling failed")
                            last_input_error_at = now

                if keyboard_toggle.poll():
                    mode = "manual" if mode == "automatic" else "automatic"
                    LOGGER.info("Translation mode changed: %s", mode)
                    if mode == "automatic":
                        next_automatic_at = time.monotonic()

                calibration_changed = calibration.poll()
                if calibration_changed:
                    if last_frame_size is not None:
                        overlay.update_position(last_frame_size)
                    if last_result is not None and last_frame_size is not None:
                        overlay.show(renderer.render(last_result, last_frame_size))

                if events.clear:
                    overlay.hide()
                    previous_signature = ()
                    last_result = None
                    last_frame_size = None
                    LOGGER.info("Translations cleared by left grip")

                now = time.monotonic()
                request_reason: str | None = None
                force_translation = False
                if events.translate and not events.clear:
                    request_reason = "left trigger"
                    force_translation = True
                elif (
                    mode == "manual"
                    and calibration_changed
                    and now - last_calibration_translation_at >= calibration_interval
                ):
                    request_reason = "position calibration"
                    force_translation = True
                    last_calibration_translation_at = now
                elif mode == "automatic" and now >= next_automatic_at:
                    request_reason = "automatic"
                    next_automatic_at = now + automatic_interval

                if request_reason is None:
                    elapsed = time.monotonic() - loop_started
                    time.sleep(max(0.0, poll_interval - elapsed))
                    continue

                frame = capture.grab()
                changed, change_score = detector.changed(frame)
                if not force_translation and not changed:
                    skipped_frames += 1
                    now = time.monotonic()
                    if now - last_status_at >= 5.0:
                        LOGGER.info(
                            "Waiting for screen changes: score=%.2f skipped=%d mode=%s",
                            change_score,
                            skipped_frames,
                            mode,
                        )
                        last_status_at = now
                else:
                    LOGGER.info(
                        "Processing %dx%d frame: reason=%s change=%.2f",
                        frame.width,
                        frame.height,
                        request_reason,
                        change_score,
                    )
                    request_started = time.monotonic()
                    try:
                        result = translator.translate(frame)
                    except Exception:
                        LOGGER.exception("Image translation request failed")
                    else:
                        request_seconds = time.monotonic() - request_started
                        signature = tuple(
                            (
                                block.target_text,
                                block.bounds.left,
                                block.bounds.top,
                                block.bounds.right,
                                block.bounds.bottom,
                            )
                            for block in result.blocks
                        )
                        LOGGER.info(
                            "Translation result: %.3fs blocks=%d reason=%s",
                            request_seconds,
                            len(result.blocks),
                            request_reason,
                        )
                        for index, block in enumerate(result.blocks, 1):
                            LOGGER.info(
                                "Block %d at (%d,%d)-(%d,%d): %s",
                                index,
                                block.bounds.left,
                                block.bounds.top,
                                block.bounds.right,
                                block.bounds.bottom,
                                block.target_text,
                            )
                        if result.blocks:
                            last_result = result
                            last_frame_size = frame.size
                            if force_translation or signature != previous_signature:
                                overlay.show(renderer.render(result, frame.size))
                                previous_signature = signature
                        else:
                            overlay.hide()
                            previous_signature = ()
                            last_result = None
                            last_frame_size = None

                elapsed = time.monotonic() - loop_started
                time.sleep(max(0.0, poll_interval - elapsed))
