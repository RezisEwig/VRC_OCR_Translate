from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")
_JAPANESE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")
_JAPANESE_KANA = re.compile(r"[\u3040-\u30ff]")
_LATIN = re.compile(r"[A-Za-z]")


def normalize_text(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip()


def contains_japanese(value: str) -> bool:
    return bool(_JAPANESE.search(value))


def contains_japanese_kana(value: str) -> bool:
    return bool(_JAPANESE_KANA.search(value))


def contains_latin(value: str, minimum_letters: int = 1) -> bool:
    return len(_LATIN.findall(value)) >= max(1, minimum_letters)


def contains_configured_language(
    value: str,
    languages: list[str],
    minimum_latin_letters: int = 2,
) -> bool:
    normalized = {language.lower() for language in languages}
    return (
        bool({"ja", "jp", "japanese"} & normalized) and contains_japanese(value)
    ) or (
        bool({"en", "eng", "english"} & normalized)
        and contains_latin(value, minimum_latin_letters)
    )


def source_language_description(value: str, languages: list[str]) -> str:
    has_japanese = contains_japanese(value)
    has_english = contains_latin(value)
    if has_japanese and has_english:
        return "mixed Japanese and English"
    if has_japanese:
        return "Japanese"
    if has_english:
        return "English"
    names = [
        {"ja": "Japanese", "jp": "Japanese", "en": "English"}.get(
            language.lower(), language
        )
        for language in languages
    ]
    return " and ".join(names) or "source-language"
