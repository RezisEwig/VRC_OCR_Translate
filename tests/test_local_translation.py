from vrc_ocr_translate.config import TranslationConfig
from vrc_ocr_translate.local_translation import (
    TranslateGemmaTranslator,
    build_translation_prompt,
)


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"content": "출구는 이쪽입니다.<end_of_turn>"}


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse()


class FakeServer:
    base_url = "http://127.0.0.1:18765"


def test_builds_translategemma_prompt_without_duplicate_bos_token():
    prompt = build_translation_prompt("出口はこちらです。")
    assert prompt.startswith("<start_of_turn>user\n")
    assert "<bos>" not in prompt
    assert "professional Japanese to Korean" in prompt
    assert prompt.endswith("<start_of_turn>model\n")


def test_prompt_translates_mixed_japanese_and_english_as_one_text():
    prompt = build_translation_prompt("STARTを押してください")
    assert "mixed Japanese and English" in prompt
    assert "including any English embedded" in prompt


def test_caches_repeated_local_translation():
    session = FakeSession()
    translator = TranslateGemmaTranslator(
        TranslationConfig(), FakeServer(), session=session
    )

    first = translator.translate("出口はこちらです。")
    second = translator.translate("出口はこちらです。")

    assert first == "출구는 이쪽입니다."
    assert second == first
    assert len(session.calls) == 1
