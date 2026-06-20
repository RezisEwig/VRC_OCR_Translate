from vrc_ocr_translate.config import OverlayConfig
from vrc_ocr_translate.control_panel import ControlPanelStatus
from vrc_ocr_translate.languages import (
    SUPPORTED_LANGUAGES,
    get_language,
    normalize_language_code,
    normalize_source_language,
    ui_text,
)


def test_exposes_ten_target_languages_with_complete_ui_text():
    required = {
        "local_translation",
        "my_language",
        "source_language",
        "auto_detect",
        "status_auto",
        "status_manual",
        "automatic",
        "manual",
        "quick_actions",
        "translate_now",
        "clear",
        "position",
        "shrink",
        "enlarge",
        "shortcut",
        "quit",
    }
    assert len(SUPPORTED_LANGUAGES) == 10
    for language in SUPPORTED_LANGUAGES:
        assert required <= language.ui.keys()
        assert all(language.ui[key] for key in required)


def test_normalizes_chinese_language_aliases():
    assert normalize_language_code("zh-cn") == "zh-CN"
    assert normalize_language_code("zh-Hant") == "zh-TW"
    assert get_language("zh_tw").native_name == "繁體中文"
    assert normalize_source_language("automatic") == "auto"
    assert normalize_source_language("JA") == "ja"


def test_control_panel_status_carries_selected_ui_language():
    status = ControlPanelStatus.from_overlay(
        "manual",
        OverlayConfig(),
        "de",
        "ja",
    )
    assert status.target_language == "de"
    assert status.source_language == "ja"
    assert ui_text(status.target_language, "manual") == "Manuell"
