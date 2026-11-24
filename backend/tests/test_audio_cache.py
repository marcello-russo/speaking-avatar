import pytest
from app.services.audio_cache import AudioCache


def test_cache_hit():
    cache = AudioCache(max_l1=5)
    chunks = [{"data": b"audio1", "dur": 0.5}]
    cache.put("ciao come stai", chunks)
    assert cache.get("ciao come stai") == chunks


def test_cache_miss():
    cache = AudioCache(max_l1=5)
    assert cache.get("non esistente") is None


def test_cache_lru_eviction():
    cache = AudioCache(max_l1=3)
    for i in range(5):
        cache.put(f"frase_{i}", [{"data": bytes([i]), "dur": 0.1}])
    assert cache.get("frase_0") is None
    assert cache.get("frase_1") is None
    assert cache.get("frase_2") is not None
    assert cache.get("frase_3") is not None
    assert cache.get("frase_4") is not None


def test_normalize_key():
    cache = AudioCache()
    k1 = cache.normalize("Ciao! Come stai?")
    k2 = cache.normalize("ciao!  come  stai?")
    assert k1 == k2
