from __future__ import annotations

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
_JAPANESE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")
_JAPANESE_KANA = re.compile(r"[\u3040-\u30ff]")
_HANGUL = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]")
_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def normalize_text(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip()


def contains_japanese(value: str) -> bool:
    return bool(_JAPANESE.search(value))


def contains_japanese_kana(value: str) -> bool:
    return bool(_JAPANESE_KANA.search(value))


def contains_latin(value: str, minimum_letters: int = 1) -> bool:
    latin_letters = sum(
        1
        for character in value
        if character.isalpha()
        and "LATIN" in unicodedata.name(character, "")
    )
    return latin_letters >= max(1, minimum_letters)


def contains_hangul(value: str) -> bool:
    return bool(_HANGUL.search(value))


def contains_cjk(value: str) -> bool:
    return bool(_CJK.search(value))


def script_counts(value: str) -> dict[str, int]:
    counts = {"hangul": 0, "kana": 0, "cjk": 0, "latin": 0}
    for character in value:
        if _HANGUL.match(character):
            counts["hangul"] += 1
        elif _JAPANESE_KANA.match(character):
            counts["kana"] += 1
        elif _CJK.match(character):
            counts["cjk"] += 1
        elif character.isalpha() and "LATIN" in unicodedata.name(character, ""):
            counts["latin"] += 1
    return counts


def contains_configured_language(
    value: str,
    languages: list[str],
    minimum_latin_letters: int = 2,
) -> bool:
    normalized = {language.lower() for language in languages}
    has_east_asian = bool(
        {"ja", "jp", "japanese", "zh", "zh-cn", "zh-tw", "chinese"}
        & normalized
    ) and (contains_japanese(value) or contains_cjk(value))
    has_korean = bool({"ko", "kor", "korean"} & normalized) and contains_hangul(
        value
    )
    latin_languages = {
        "en",
        "eng",
        "english",
        "es",
        "fr",
        "de",
        "pt",
        "it",
    }
    has_latin = bool(latin_languages & normalized) and contains_latin(
        value,
        minimum_latin_letters,
    )
    return has_east_asian or has_korean or has_latin


def source_language_description(value: str, languages: list[str]) -> str:
    counts = script_counts(value)
    scripts = sum(count > 0 for count in counts.values())
    if scripts > 1:
        return "automatically detected mixed-language"
    if counts["hangul"]:
        return "Korean"
    if counts["kana"]:
        return "Japanese"
    if counts["cjk"]:
        return "Chinese or Japanese"
    if counts["latin"]:
        return "automatically detected Latin-script language"
    return "automatically detected source-language"
