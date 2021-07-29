"""Top-level access to the Flask cache."""
from beevenue.types import MediumDocument, TinyMediumDocument
from enum import Enum, unique
from logging import debug, info
from redis import Redis
import time
from typing import Any, Dict, Iterable, List, Set

from .load import full_load

from .schemas import (
    ALL_TINY_MEDIUM_DOCUMENT_SCHEMA,
    FULL_MEDIUM_DOCUMENT_SCHEMA,
    STRING_LIST_SCHEMA,
    TINY_MEDIUM_DOCUMENT_SCHEMA,
    RATING_BY_HASH_SCHEMA,
)


@unique
class CacheEntityKind(str, Enum):
    """All kind of entities that can be stored in this cache."""

    MEDIUM_DOCUMENT = "MD"
    MEDIUM_DOCUMENT_TINY = "MDT"
    MEDIUM_DOCUMENT_TINY_ALL = "MDTA"
    RATING_BY_HASH = "RBH"
    SEARCHABLE_TAGS = "ST"


SCHEMAS = {
    CacheEntityKind.MEDIUM_DOCUMENT: FULL_MEDIUM_DOCUMENT_SCHEMA,
    CacheEntityKind.MEDIUM_DOCUMENT_TINY: TINY_MEDIUM_DOCUMENT_SCHEMA,
    CacheEntityKind.MEDIUM_DOCUMENT_TINY_ALL: ALL_TINY_MEDIUM_DOCUMENT_SCHEMA,
    CacheEntityKind.RATING_BY_HASH: RATING_BY_HASH_SCHEMA,
    CacheEntityKind.SEARCHABLE_TAGS: STRING_LIST_SCHEMA,
}


def _key(kind: CacheEntityKind, entity: Any) -> str:
    return f"{kind}_{entity}"


class BeevenueCache:
    """Access to redis cache."""

    def __init__(self) -> None:
        self.redis = Redis(host="redis")

    def _set_all(
        self, target_kind: CacheEntityKind, dictionary: Dict[Any, Any]
    ) -> None:
        raw_bytes_dict = {
            _key(target_kind, key): SCHEMAS[target_kind].serialize(value)
            for (key, value) in dictionary.items()
        }

        self.redis.mset(raw_bytes_dict)

    def get(self, target_kind: CacheEntityKind, key: Any) -> Any:
        raw_bytes = self.redis.get(_key(target_kind, key))
        if raw_bytes is None:
            return None
        return SCHEMAS[target_kind].deserialize(raw_bytes)

    def get_all_tiny(self) -> List[TinyMediumDocument]:
        raw_bytes = self.redis.get("MDTA_ALL")

        result: List[TinyMediumDocument] = SCHEMAS[
            CacheEntityKind.MEDIUM_DOCUMENT_TINY_ALL
        ].deserialize(raw_bytes)
        return result

    def get_many(
        self, target_kind: CacheEntityKind, keys: List[Any]
    ) -> List[Any]:
        raw_bytes_list = self.redis.mget([_key(target_kind, k) for k in keys])
        result = [SCHEMAS[target_kind].deserialize(b) for b in raw_bytes_list]
        return result

    def set(self, target_kind: CacheEntityKind, key: str, value: Any) -> None:
        raw_bytes = SCHEMAS[target_kind].serialize(value)
        self.redis.set(_key(target_kind, key), raw_bytes)

    def get_all_searchable_tag_names(self) -> List[str]:
        result: List[str] = self.get(CacheEntityKind.SEARCHABLE_TAGS, "")
        return result

    def warmup(
        self,
        media_document_dictionary: Dict[int, MediumDocument],
        tag_names: Iterable[str],
    ) -> None:

        self.set(CacheEntityKind.SEARCHABLE_TAGS, "", tag_names)
        self._set_all(
            CacheEntityKind.MEDIUM_DOCUMENT, media_document_dictionary
        )
        self._set_all(
            CacheEntityKind.MEDIUM_DOCUMENT_TINY, media_document_dictionary
        )

        self._set_all(
            CacheEntityKind.RATING_BY_HASH,
            {
                v.medium_hash: v.rating
                for k, v in media_document_dictionary.items()
            },
        )
        self.set(
            CacheEntityKind.MEDIUM_DOCUMENT_TINY_ALL,
            "ALL",
            list(media_document_dictionary.values()),
        )

    def fill(self) -> None:
        tic = time.perf_counter()
        info("Starting warmup.")
        self.redis.flushall()
        info("Loading all media.")
        all_media = full_load()

        info("Gathering searchable tag names.")
        searchable_tag_names: Set[str] = set()
        for medium in all_media:
            searchable_tag_names |= medium.searchable_tag_names

        self.warmup(
            {item.medium_id: item for item in all_media},
            searchable_tag_names,
        )
        toc = time.perf_counter()
        debug(f"Refilling cache took {1000*(toc-tic):0.1f} ms")
