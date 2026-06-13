from vrc_ocr_translate.text import (
    contains_configured_language,
    contains_japanese,
    contains_japanese_kana,
    normalize_text,
)


def test_detects_japanese_scripts():
    assert contains_japanese("こんにちは")
    assert contains_japanese("カタカナ")
    assert contains_japanese("日本語")
    assert not contains_japanese("한국어 only")


def test_normalizes_whitespace():
    assert normalize_text("  a\n  b  ") == "a b"


def test_detects_kana_separately_from_shared_cjk():
    assert contains_japanese_kana("美術館へようこそ")
    assert not contains_japanese_kana("美術館")


def test_accepts_configured_japanese_and_english_text():
    assert contains_configured_language("STARTを押す", ["ja", "en"])
    assert contains_configured_language("Press START", ["ja", "en"])
    assert not contains_configured_language("12345", ["ja", "en"])
