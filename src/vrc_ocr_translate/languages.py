from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LanguageDefinition:
    code: str
    english_name: str
    native_name: str
    ui: dict[str, str]


SUPPORTED_LANGUAGES = (
    LanguageDefinition(
        "ko",
        "Korean",
        "한국어",
        {
            "local_translation": "로컬 VR 번역",
            "my_language": "내 언어",
            "source_language": "번역할 언어",
            "auto_detect": "자동 인식",
            "status_auto": "자동 번역 중",
            "status_manual": "수동 번역 중",
            "automatic": "자동 번역",
            "manual": "수동 번역",
            "quick_actions": "빠른 동작",
            "translate_now": "지금 번역",
            "clear": "자막 지우기",
            "position": "자막 위치",
            "shrink": "축소",
            "enlarge": "확대",
            "shortcut": "Ctrl + Alt + T  모드 전환",
            "quit": "종료",
        },
    ),
    LanguageDefinition(
        "ja",
        "Japanese",
        "日本語",
        {
            "local_translation": "ローカルVR翻訳",
            "my_language": "表示言語",
            "source_language": "翻訳する言語",
            "auto_detect": "自動検出",
            "status_auto": "自動翻訳中",
            "status_manual": "手動翻訳中",
            "automatic": "自動翻訳",
            "manual": "手動翻訳",
            "quick_actions": "クイック操作",
            "translate_now": "今すぐ翻訳",
            "clear": "字幕を消去",
            "position": "字幕位置",
            "shrink": "縮小",
            "enlarge": "拡大",
            "shortcut": "Ctrl + Alt + T  モード切替",
            "quit": "終了",
        },
    ),
    LanguageDefinition(
        "zh-CN",
        "Simplified Chinese",
        "简体中文",
        {
            "local_translation": "本地VR翻译",
            "my_language": "我的语言",
            "source_language": "待翻译语言",
            "auto_detect": "自动检测",
            "status_auto": "自动翻译中",
            "status_manual": "手动翻译中",
            "automatic": "自动翻译",
            "manual": "手动翻译",
            "quick_actions": "快捷操作",
            "translate_now": "立即翻译",
            "clear": "清除字幕",
            "position": "字幕位置",
            "shrink": "缩小",
            "enlarge": "放大",
            "shortcut": "Ctrl + Alt + T  切换模式",
            "quit": "退出",
        },
    ),
    LanguageDefinition(
        "zh-TW",
        "Traditional Chinese",
        "繁體中文",
        {
            "local_translation": "本機VR翻譯",
            "my_language": "我的語言",
            "source_language": "要翻譯的語言",
            "auto_detect": "自動偵測",
            "status_auto": "自動翻譯中",
            "status_manual": "手動翻譯中",
            "automatic": "自動翻譯",
            "manual": "手動翻譯",
            "quick_actions": "快速操作",
            "translate_now": "立即翻譯",
            "clear": "清除字幕",
            "position": "字幕位置",
            "shrink": "縮小",
            "enlarge": "放大",
            "shortcut": "Ctrl + Alt + T  切換模式",
            "quit": "結束",
        },
    ),
    LanguageDefinition(
        "en",
        "English",
        "English",
        {
            "local_translation": "LOCAL VR TRANSLATION",
            "my_language": "My language",
            "source_language": "Source language",
            "auto_detect": "Auto detect",
            "status_auto": "Automatic translation",
            "status_manual": "Manual translation",
            "automatic": "Automatic",
            "manual": "Manual",
            "quick_actions": "Quick actions",
            "translate_now": "Translate now",
            "clear": "Clear subtitles",
            "position": "Subtitle position",
            "shrink": "Smaller",
            "enlarge": "Larger",
            "shortcut": "Ctrl + Alt + T  Switch mode",
            "quit": "Exit",
        },
    ),
    LanguageDefinition(
        "es",
        "Spanish",
        "Español",
        {
            "local_translation": "TRADUCCIÓN VR LOCAL",
            "my_language": "Mi idioma",
            "source_language": "Idioma de origen",
            "auto_detect": "Detección automática",
            "status_auto": "Traducción automática",
            "status_manual": "Traducción manual",
            "automatic": "Automática",
            "manual": "Manual",
            "quick_actions": "Acciones rápidas",
            "translate_now": "Traducir ahora",
            "clear": "Borrar subtítulos",
            "position": "Posición de subtítulos",
            "shrink": "Reducir",
            "enlarge": "Ampliar",
            "shortcut": "Ctrl + Alt + T  Cambiar modo",
            "quit": "Salir",
        },
    ),
    LanguageDefinition(
        "fr",
        "French",
        "Français",
        {
            "local_translation": "TRADUCTION VR LOCALE",
            "my_language": "Ma langue",
            "source_language": "Langue source",
            "auto_detect": "Détection automatique",
            "status_auto": "Traduction automatique",
            "status_manual": "Traduction manuelle",
            "automatic": "Automatique",
            "manual": "Manuelle",
            "quick_actions": "Actions rapides",
            "translate_now": "Traduire maintenant",
            "clear": "Effacer les sous-titres",
            "position": "Position des sous-titres",
            "shrink": "Réduire",
            "enlarge": "Agrandir",
            "shortcut": "Ctrl + Alt + T  Changer de mode",
            "quit": "Quitter",
        },
    ),
    LanguageDefinition(
        "de",
        "German",
        "Deutsch",
        {
            "local_translation": "LOKALE VR-ÜBERSETZUNG",
            "my_language": "Meine Sprache",
            "source_language": "Ausgangssprache",
            "auto_detect": "Automatisch erkennen",
            "status_auto": "Automatische Übersetzung",
            "status_manual": "Manuelle Übersetzung",
            "automatic": "Automatisch",
            "manual": "Manuell",
            "quick_actions": "Schnellaktionen",
            "translate_now": "Jetzt übersetzen",
            "clear": "Untertitel löschen",
            "position": "Untertitelposition",
            "shrink": "Verkleinern",
            "enlarge": "Vergrößern",
            "shortcut": "Ctrl + Alt + T  Modus wechseln",
            "quit": "Beenden",
        },
    ),
    LanguageDefinition(
        "pt",
        "Portuguese",
        "Português",
        {
            "local_translation": "TRADUÇÃO VR LOCAL",
            "my_language": "Meu idioma",
            "source_language": "Idioma de origem",
            "auto_detect": "Detectar automaticamente",
            "status_auto": "Tradução automática",
            "status_manual": "Tradução manual",
            "automatic": "Automática",
            "manual": "Manual",
            "quick_actions": "Ações rápidas",
            "translate_now": "Traduzir agora",
            "clear": "Limpar legendas",
            "position": "Posição das legendas",
            "shrink": "Diminuir",
            "enlarge": "Aumentar",
            "shortcut": "Ctrl + Alt + T  Alternar modo",
            "quit": "Sair",
        },
    ),
    LanguageDefinition(
        "it",
        "Italian",
        "Italiano",
        {
            "local_translation": "TRADUZIONE VR LOCALE",
            "my_language": "La mia lingua",
            "source_language": "Lingua di origine",
            "auto_detect": "Rilevamento automatico",
            "status_auto": "Traduzione automatica",
            "status_manual": "Traduzione manuale",
            "automatic": "Automatica",
            "manual": "Manuale",
            "quick_actions": "Azioni rapide",
            "translate_now": "Traduci ora",
            "clear": "Cancella sottotitoli",
            "position": "Posizione sottotitoli",
            "shrink": "Riduci",
            "enlarge": "Ingrandisci",
            "shortcut": "Ctrl + Alt + T  Cambia modalità",
            "quit": "Esci",
        },
    ),
)

LANGUAGE_BY_CODE = {language.code: language for language in SUPPORTED_LANGUAGES}
LANGUAGE_CODE_BY_NATIVE_NAME = {
    language.native_name: language.code for language in SUPPORTED_LANGUAGES
}
DEFAULT_TARGET_LANGUAGE = "ko"
AUTO_SOURCE_LANGUAGE = "auto"


def normalize_language_code(value: str) -> str:
    aliases = {
        **{code.lower(): code for code in LANGUAGE_BY_CODE},
        "zh": "zh-CN",
        "zh-cn": "zh-CN",
        "zh_cn": "zh-CN",
        "zh-hans": "zh-CN",
        "zh-tw": "zh-TW",
        "zh_tw": "zh-TW",
        "zh-hant": "zh-TW",
    }
    normalized = aliases.get(value.strip().lower(), value.strip())
    if normalized not in LANGUAGE_BY_CODE:
        supported = ", ".join(LANGUAGE_BY_CODE)
        raise ValueError(f"Unsupported target language '{value}'. Choose: {supported}")
    return normalized


def normalize_source_language(value: str) -> str:
    normalized = value.strip()
    if normalized.lower() in {"auto", "automatic", "detect"}:
        return AUTO_SOURCE_LANGUAGE
    return normalize_language_code(normalized)


def get_language(code: str) -> LanguageDefinition:
    return LANGUAGE_BY_CODE[normalize_language_code(code)]


def ui_text(code: str, key: str) -> str:
    language = get_language(code)
    return language.ui.get(key, LANGUAGE_BY_CODE[DEFAULT_TARGET_LANGUAGE].ui[key])


def font_path_for_language(code: str, fallback: str) -> str:
    candidates = {
        "ko": (fallback, "C:/Windows/Fonts/malgun.ttf"),
        "ja": ("C:/Windows/Fonts/YuGothM.ttc", "C:/Windows/Fonts/meiryo.ttc"),
        "zh-CN": ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simsun.ttc"),
        "zh-TW": ("C:/Windows/Fonts/msjh.ttc", "C:/Windows/Fonts/mingliu.ttc"),
        "en": ("C:/Windows/Fonts/segoeui.ttf", fallback),
        "es": ("C:/Windows/Fonts/segoeui.ttf", fallback),
        "fr": ("C:/Windows/Fonts/segoeui.ttf", fallback),
        "de": ("C:/Windows/Fonts/segoeui.ttf", fallback),
        "pt": ("C:/Windows/Fonts/segoeui.ttf", fallback),
        "it": ("C:/Windows/Fonts/segoeui.ttf", fallback),
    }
    for candidate in candidates[normalize_language_code(code)]:
        if Path(candidate).exists():
            return candidate
    return fallback
