from typing import Any, Dict, Iterable, Optional

from .types import Query, SubCache


class CurrentRequestCache(SubCache):
    """Per-request cache around Redis cache that saves on round trips."""

    def __init__(self) -> None:
        self.cache: Dict[str, Any] = {}

    def delete(self, *queries: Query) -> int:
        result = 0
        for query in queries:
            popped = self.cache.pop(query.hash, None)
            result += int(bool(popped))

        return result

    def get(self, query: Query) -> Optional[Any]:
        result = self.cache.get(query.hash, None)
        return result

    def get_many(self, queries: Iterable[Query]) -> Dict[Query, Any]:
        subresults = {query: self.get(query) for query in queries}

        result = {
            query: subresult
            for query, subresult in subresults.items()
            if subresult
        }

        return result

    def set(self, query: Query, value: Any) -> None:
        self.cache[query.hash] = value

    def set_many(self, values: Dict[Query, Any]) -> None:
        self.cache.update({q.hash: v for q, v in values.items()})
