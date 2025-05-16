import pytest
from .cache import LRUCache


def test_lru_set_and_get():
    cache = LRUCache(capacity=2)
    cache.set("a", 1)
    assert cache.get("a") == 1


def test_lru_eviction():
    cache = LRUCache(capacity=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)  # should evict "a"
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_lru_update_existing():
    cache = LRUCache(capacity=2)
    cache.set("a", 1)
    cache.set("a", 2)
    assert cache.get("a") == 2


def test_lru_ordering():
    cache = LRUCache(capacity=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.get("a")  # simulate access to "a"
    cache.set("c", 3)  # should evict "b"
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3
