from .cache import cache


def warmup() -> None:
    cache.clear()
    cache.fill()
