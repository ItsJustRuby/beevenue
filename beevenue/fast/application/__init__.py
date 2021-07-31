"""Top-level access to the Flask cache."""
from redis import Redis
from typing import Any, Dict, List, Optional

from ..types import Query, SubCache

from .schemas import SCHEMAS


class ApplicationWideCache(SubCache):
    """Access to redis cache."""

    def __init__(self) -> None:
        self.redis = Redis(host="redis")

    def delete(self, *queries: Query) -> int:
        deleted_count: int = self.redis.delete(*[q.hash for q in queries])
        return deleted_count

    def get(self, query: Query) -> Optional[Any]:
        raw_bytes = self.redis.get(query.hash)
        if raw_bytes is None:
            return None
        result = SCHEMAS[query.kind].deserialize(raw_bytes)
        return result

    def set(self, query: Query, value: Any) -> None:
        raw_bytes = SCHEMAS[query.kind].serialize(value)
        self.redis.set(query.hash, raw_bytes)

    def get_many(self, queries: List[Query]) -> Dict[Query, Any]:
        if len(queries) == 0:
            return {}

        raw_bytes_list = self.redis.mget([q.hash for q in queries])

        result = {}
        for query, raw_bytes in zip(queries, raw_bytes_list):
            result[query] = SCHEMAS[queries[0].kind].deserialize(raw_bytes)

        return result

    def set_many(self, values: Dict[Query, Any]) -> None:
        raw_bytes_dict = {
            query.hash: SCHEMAS[query.kind].serialize(value)
            for (query, value) in values.items()
        }

        self.redis.mset(raw_bytes_dict)
