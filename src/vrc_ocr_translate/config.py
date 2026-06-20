from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .languages import (
    AUTO_SOURCE_LANGUAGE,
    DEFAULT_TARGET_LANGUAGE,
    normalize_language_code,
    normalize_source_language,
)

DEFAULT_POSITION_OFFSET_X_RATIO = -0.10
DEFAULT_POSITION_OFFSET_Y_RATIO = 0.12


@dataclass(slots=True)
class CaptureConfig:
    source: str = "vrchat_window"
    monitor: int = 1
    region: dict[str, int] | None = None
    interval_ms: int = 2000
    change_threshold: float = 2.5
    window_title: str = "VRChat"
    window_class: str = "UnityWndClass"
    restore_minimized_window: bool = True


@dataclass(slots=True)
class OcrConfig:
    confidence_threshold: float = 0.6
    max_dimension: int = 1920
    line_cluster_eps: float = 0.65
    line_max_gap_ratio: float = 4.0
    languages: list[str] = field(
        default_factory=lambda: [
            "ko",
            "ja",
            "zh-CN",
            "zh-TW",
            "en",
            "es",
            "fr",
            "de",
            "pt",
            "it",
        ]
    )
    auto_detect_languages: bool = True
    min_latin_letters: int = 2


@dataclass(slots=True)
class TranslationConfig:
    source_languages: list[str] = field(
        default_factory=lambda: [
            "KO", "JA", "ZH-CN", "ZH-TW", "EN", "ES", "FR", "DE", "PT", "IT"
        ]
    )
    source_language: str = AUTO_SOURCE_LANGUAGE
    target_language: str = DEFAULT_TARGET_LANGUAGE
    local_model_path: str = "models/translategemma-4b-it.Q4_K_M.gguf"
    local_server_executable: str = "tools/llama.cpp/b9610/llama-server.exe"
    local_server_host: str = "127.0.0.1"
    local_server_port: int = 18765
    local_context_size: int = 2048
    local_gpu_layers: str = "all"
    local_startup_timeout_seconds: float = 45.0
    local_max_tokens: int = 192
    local_cache_capacity: int = 512
    request_timeout_seconds: float = 30.0


@dataclass(slots=True)
class OverlayConfig:
    width_px: int = 1200
    height_px: int = 260
    width_m: float = 2.25
    distance_m: float = 1.2
    vertical_offset_m: float = 0.0
    font_path: str = "C:/Windows/Fonts/malgun.ttf"
    font_size: int = 48
    background_alpha: int = 190
    min_font_size: int = 10
    max_font_size: int = 54
    position_offset_x_ratio: float = DEFAULT_POSITION_OFFSET_X_RATIO
    position_offset_y_ratio: float = DEFAULT_POSITION_OFFSET_Y_RATIO
    position_scale_x: float = 1.0
    position_scale_y: float = 1.0
    calibration_step_ratio: float = 0.02
    collision_gap_px: int = 12


@dataclass(slots=True)
class ControlsConfig:
    start_mode: str = "automatic"
    poll_interval_ms: int = 50
    calibration_translate_interval_ms: int = 1000
    show_panel: bool = True


@dataclass(slots=True)
class AppConfig:
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    ocr: OcrConfig = field(default_factory=OcrConfig)
    translation: TranslationConfig = field(default_factory=TranslationConfig)
    overlay: OverlayConfig = field(default_factory=OverlayConfig)
    controls: ControlsConfig = field(default_factory=ControlsConfig)


def _section(cls: type[Any], data: dict[str, Any], key: str) -> Any:
    values = data.get(key, {})
    if not isinstance(values, dict):
        raise ValueError(f"'{key}' must be a JSON object")
    allowed = set(cls.__dataclass_fields__)
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(f"Unknown {key} settings: {', '.join(sorted(unknown))}")
    return cls(**values)


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        return AppConfig()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Configuration root must be a JSON object")
    config = AppConfig(
        capture=_section(CaptureConfig, data, "capture"),
        ocr=_section(OcrConfig, data, "ocr"),
        translation=_section(TranslationConfig, data, "translation"),
        overlay=_section(OverlayConfig, data, "overlay"),
        controls=_section(ControlsConfig, data, "controls"),
    )
    config.translation.target_language = normalize_language_code(
        config.translation.target_language
    )
    config.translation.source_language = normalize_source_language(
        config.translation.source_language
    )
    return config


def save_overlay_calibration(path: str | Path, overlay: OverlayConfig) -> None:
    config_path = Path(path)
    data: dict[str, Any] = {}
    if config_path.exists():
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("Configuration root must be a JSON object")
        data = loaded
    section = data.setdefault("overlay", {})
    if not isinstance(section, dict):
        raise ValueError("'overlay' must be a JSON object")
    section.update(
        {
            "position_offset_x_ratio": round(overlay.position_offset_x_ratio, 4),
            "position_offset_y_ratio": round(overlay.position_offset_y_ratio, 4),
            "position_scale_x": round(overlay.position_scale_x, 4),
            "position_scale_y": round(overlay.position_scale_y, 4),
            "calibration_step_ratio": round(overlay.calibration_step_ratio, 4),
        }
    )
    temporary = config_path.with_suffix(config_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(config_path)


def save_target_language(path: str | Path, language_code: str) -> None:
    _save_translation_setting(
        path,
        "target_language",
        normalize_language_code(language_code),
    )


def save_source_language(path: str | Path, language_code: str) -> None:
    _save_translation_setting(
        path,
        "source_language",
        normalize_source_language(language_code),
    )


def save_start_mode(path: str | Path, mode: str) -> None:
    normalized = mode.strip().lower()
    if normalized not in {"automatic", "manual"}:
        raise ValueError("controls.start_mode must be 'automatic' or 'manual'")
    _save_section_setting(path, "controls", "start_mode", normalized)


def _save_translation_setting(path: str | Path, key: str, value: str) -> None:
    _save_section_setting(path, "translation", key, value)


def _save_section_setting(
    path: str | Path,
    section_name: str,
    key: str,
    value: Any,
) -> None:
    config_path = Path(path)
    data: dict[str, Any] = {}
    if config_path.exists():
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("Configuration root must be a JSON object")
        data = loaded
    section = data.setdefault(section_name, {})
    if not isinstance(section, dict):
        raise ValueError(f"'{section_name}' must be a JSON object")
    section[key] = value
    temporary = config_path.with_suffix(config_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(config_path)
