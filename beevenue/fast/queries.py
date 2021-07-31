from typing import Any, Dict, Generic, Iterable, List, TypeVar
from .types import CacheEntityKind, SubCache, Query


TQueryable = TypeVar("TQueryable")
TCached = TypeVar("TCached")


class Helper(Generic[TQueryable, TCached]):
    """Helper class for arbitrary cache queries"""

    def get(self, cache: SubCache, queriable: TQueryable) -> Any:
        """Specific getter to call on cache."""

    def set(self, cache: SubCache, queriable: TQueryable, value: Any) -> None:
        """Specific setter to call on cache."""

    def transform(self, cache_hit: Any) -> TCached:
        """How to post-process a cache hit."""

    def miss(self) -> TCached:
        """What to return on a cache miss."""


class SingleQueryHelper(Helper[Query, Any]):
    """Helper class for unary queries"""

    def get(self, cache: SubCache, queriable: Query) -> Any:
        return cache.get(queriable)

    def set(self, cache: SubCache, queriable: Query, value: Any) -> None:
        return cache.set(queriable, value)

    def transform(self, cache_hit: Any) -> Any:
        return cache_hit

    def miss(self) -> Any:
        return None


class ManyQueryHelper(Helper[List[Query], List[Any]]):
    """Helper class for N-ary queries"""

    def get(self, cache: SubCache, queriable: List[Query]) -> Dict[Query, Any]:
        return cache.get_many(queriable)

    def set(
        self, cache: SubCache, _: List[Query], value: Dict[Query, Any]
    ) -> None:
        return cache.set_many(value)

    def transform(self, cache_hit: Dict[Query, Any]) -> List[Any]:
        return list(cache_hit.values())

    def miss(self) -> List[Any]:
        return []


_SINGLE_QUERY_HELPER = SingleQueryHelper()
_MANY_QUERY_HELPER = ManyQueryHelper()


def _run(
    caches: Iterable[SubCache],
    queriable: TQueryable,
    helper: Helper[TQueryable, TCached],
) -> TCached:

    caches_to_fill = []

    for cache in caches:
        cache_hit = helper.get(cache, queriable)
        if not cache_hit:
            caches_to_fill.append(cache)
        else:
            break

    if cache_hit is None:
        # This may legit happen (e.g. for rating-by-hash) and is fine.
        return helper.miss()

    for cache in reversed(caches_to_fill):
        helper.set(cache, queriable, cache_hit)

    result = helper.transform(cache_hit)
    return result


def run_single_query(
    caches: Iterable[SubCache], kind: CacheEntityKind, key: Any
) -> Any:

    return _run(caches, Query(kind, key), _SINGLE_QUERY_HELPER)


def run_many_query(
    caches: Iterable[SubCache], kind: CacheEntityKind, keys: Iterable[Any]
) -> List[Any]:

    return _run(caches, [Query(kind, key) for key in keys], _MANY_QUERY_HELPER)
