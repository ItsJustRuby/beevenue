from beevenue.types import MediumDocument, TinyMediumDocument
from typing import Any, List, Optional

from .application import ApplicationWideCache
from .commands import REFILL
from .nope import NotACache
from .current import CurrentRequestCache
from .types import Cache, CacheEntityKind, Command, SubCache
from .queries import run_many_query, run_single_query


class Fast(Cache):
    """A lasagna of caches. Falls through on miss and refills the layers."""

    def __init__(self) -> None:
        self.caches: List[SubCache] = [
            CurrentRequestCache(),
            ApplicationWideCache(),
            NotACache(),
        ]

    def _delegate_single(
        self, kind: CacheEntityKind, key: Optional[Any]
    ) -> Any:
        return run_single_query(self.caches, kind, key)

    def _delegate_many(
        self, kind: CacheEntityKind, keys: List[Any]
    ) -> List[Any]:

        return run_many_query(self.caches, kind, keys)

    def fill(self) -> None:
        self.run(REFILL)

    def get_rating_by_hash(self, for_hash: str) -> str:
        result: str = self._delegate_single(
            CacheEntityKind.RATING_BY_HASH, for_hash
        )
        return result

    def get_all_searchable_tag_names(self) -> List[str]:
        result: List[str] = self._delegate_single(
            CacheEntityKind.SEARCHABLE_TAGS, "ALL"
        )
        return result

    def get_many(self, ids: List[int]) -> List[Any]:
        result: List[Any] = self._delegate_many(
            CacheEntityKind.MEDIUM_DOCUMENT, ids
        )
        return result

    def get_medium(self, medium_id: int) -> MediumDocument:
        result: MediumDocument = self._delegate_single(
            CacheEntityKind.MEDIUM_DOCUMENT, medium_id
        )
        return result

    def get_many_tiny(self, ids: List[int]) -> List[TinyMediumDocument]:
        result: List[TinyMediumDocument] = self._delegate_many(
            CacheEntityKind.MEDIUM_DOCUMENT_TINY, ids
        )
        return result

    def get_tiny(self, medium_id: int) -> TinyMediumDocument:
        result: TinyMediumDocument = self._delegate_single(
            CacheEntityKind.MEDIUM_DOCUMENT_TINY, medium_id
        )
        return result

    def get_all_tiny(self) -> List[TinyMediumDocument]:
        result: List[TinyMediumDocument] = self._delegate_single(
            CacheEntityKind.MEDIUM_DOCUMENT_TINY_ALL, "ALL"
        )
        return result

    def run(self, *commands: Command) -> None:
        for command in commands:
            agg = None
            for cache in reversed(self.caches):
                agg = command.run(cache, agg)
