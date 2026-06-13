from vrc_ocr_translate.stability import TranslationCache


def test_cache_evicts_oldest_value():
    cache = TranslationCache(2)
    cache.put("a", "A")
    cache.put("b", "B")
    cache.put("c", "C")
    assert cache.get("a") is None
    assert cache.get("b") == "B"
