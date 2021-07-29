from typing import Any, Dict, Iterable, List, Optional
from logging import debug

from ..cache import cache
from ..cache.cache import CacheEntityKind
from ..types import MediumDocument, TinyMediumDocument


class Spindex:
    """Per-request cache around Redis cache that saves on round trips."""

    def __init__(self) -> None:
        self.all_searchable_tag_names: Optional[List[str]] = None
        self.full_documents: Dict[int, MediumDocument] = {}

    def get_tiny(self, medium_id: int) -> TinyMediumDocument:
        tiny: TinyMediumDocument = cache.get(
            CacheEntityKind.MEDIUM_DOCUMENT_TINY, medium_id
        )
        return tiny

    def get_medium(self, medium_id: int) -> Optional[MediumDocument]:
        in_memory = self.full_documents.get(medium_id)
        if in_memory:
            debug(f"Load Single from memory: {medium_id}")
            return in_memory

        from_cache: Optional[MediumDocument] = cache.get(
            CacheEntityKind.MEDIUM_DOCUMENT, medium_id
        )
        if from_cache:
            debug(f"Load Single from Cache: {medium_id}")
            self.full_documents[medium_id] = from_cache
            return from_cache

        return None

    def get_many_tiny(self, ids: List[int]) -> Iterable[TinyMediumDocument]:
        from_cache: Iterable[TinyMediumDocument] = cache.get_many(
            CacheEntityKind.MEDIUM_DOCUMENT_TINY, ids
        )
        return from_cache

    def get_many(self, ids: List[int]) -> Iterable[MediumDocument]:
        from_cache: List[MediumDocument] = cache.get_many(
            CacheEntityKind.MEDIUM_DOCUMENT, ids
        )

        i = 0
        for medium_id in ids:
            self.full_documents[medium_id] = from_cache[i]
            i += 1

        return from_cache

    # Note: This is the nuclear option. It's good enough for now! :)
    def reindex_medium(self, *_: Any) -> None:
        cache.fill()

    def rename_tag(self, *_: Any) -> None:
        cache.fill()

    def add_alias(self, *_: Any) -> None:
        cache.fill()

    def remove_alias(self, *_: Any) -> None:
        cache.fill()

    def add_implication(self, *_: Any) -> None:
        cache.fill()

    def remove(self, *_: Any) -> None:
        cache.fill()

    def remove_implication(self, *_: Any) -> None:
        cache.fill()

    def get_all_searchable_tag_names(self) -> Iterable[str]:
        if self.all_searchable_tag_names is None:
            cached = cache.get_all_searchable_tag_names()
            self.all_searchable_tag_names = cached
            debug("Get searchable tag names from cache")
        else:
            debug("Get searchable tag names from memory")

        result: List[str] = self.all_searchable_tag_names
        return result

    # These happen at most once per request,
    # so it's not necessary to cache in-memory
    def get_rating_by_hash(self, medium_hash: str) -> Optional[str]:
        result: Optional[str] = cache.get(
            CacheEntityKind.RATING_BY_HASH, medium_hash
        )
        return result

    def get_all_tiny(self) -> Iterable[TinyMediumDocument]:
        return cache.get_all_tiny()
