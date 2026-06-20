from vrc_ocr_translate.stability import TranslationCache


def test_cache_evicts_oldest_value():
    cache = TranslationCache(2)
    cache.put("a", "A")
    cache.put("b", "B")
    cache.put("c", "C")
    assert cache.get("a") is None
    assert cache.get("b") == "B"


def test_cache_can_be_cleared_when_target_language_changes():
    cache = TranslationCache(2)
    cache.put("ko\0hello", "안녕")
    cache.clear()
    assert cache.get("ko\0hello") is None
