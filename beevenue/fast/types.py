from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Any, Dict, Generic, List, Optional, TypeVar


class Cache:
    """Used for type hinting."""


@unique
class CacheEntityKind(str, Enum):
    """All kind of entities that can be stored in this cache."""

    MEDIUM_DOCUMENT = "MD"
    MEDIUM_DOCUMENT_TINY = "MDT"
    MEDIUM_DOCUMENT_TINY_ALL = "MDTA"
    RATING_BY_HASH = "RBH"
    SEARCHABLE_TAGS = "ST"


@dataclass(unsafe_hash=True)
class Query:
    """Key to access a SubCache with. A string with typing, basically."""

    kind: CacheEntityKind
    key: Any
    hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.hash = f"{self.kind}_{self.key}"


class SubCacheModificationContext(AbstractContextManager):
    """Context manager allowing modifying a value in a cache via GET+SET."""

    def __init__(self, cache: "SubCache", query: Query):
        self.cache = cache
        self.query = query
        self.value = cache.get(query)

    def __enter__(self) -> "SubCacheModificationContext":
        return self

    def __exit__(self, *_: Any, **__: Any) -> None:
        if self.value:
            self.cache.set(self.query, self.value)


class SubCache(ABC):
    """Cache that can be used as one layer in a stack of multiple caches."""

    def modify(self, query: Query) -> SubCacheModificationContext:
        return SubCacheModificationContext(self, query)

    @abstractmethod
    def delete(self, *queries: Query) -> int:
        """Remove these things from the cache (if they are in there).

        Returns how many were deleted.
        """

    @abstractmethod
    def get(self, query: Query) -> Any:
        """Try and get a cached entity without loading on cache miss."""

    @abstractmethod
    def set(self, query: Query, value: Any) -> None:
        """Fill cache with entity."""

    @abstractmethod
    def get_many(self, queries: List[Query]) -> Dict[Query, Any]:
        """Try and get these cached entities without loading on cache miss."""

    @abstractmethod
    def set_many(self, values: Dict[Query, Any]) -> None:
        """Fill cache with these entities."""


TAgg = TypeVar("TAgg")


class Command(Generic[TAgg]):
    """Command to execute on each cache. Might get and/or set!"""

    def run(self, cache: SubCache, agg: Optional[TAgg]) -> Optional[TAgg]:
        if not agg:
            return self.start()
        return self.next(cache, agg)

    @abstractmethod
    def start(self) -> TAgg:
        """Start running this command, building some initial data in 'agg'."""

    @abstractmethod
    def next(self, cache: SubCache, agg: TAgg) -> TAgg:
        """Continue running this command, aggregating data in 'agg'."""
