from logging import debug, info
from typing import (
    Dict,
    FrozenSet,
    List,
    NamedTuple,
    Sequence,
    Set,
    Tuple,
)
import time

from sqlalchemy.sql.expression import select

from beevenue.documents import TinyIndexedMedium
from beevenue.flask import g
from beevenue.models import Tag, TagAlias
from beevenue.document_types import MediumDocument, TinyMediumDocument

from .types import CacheEntityKind, Command, Query, SubCache
from .load import full_load, multi_load


class RefillCommandAggregator(NamedTuple):
    """Aggregator class for RefillCommand."""

    media: Dict[int, MediumDocument]
    searchable_tag_names: FrozenSet[str]


class RefillCommand(Command[RefillCommandAggregator]):
    """Completely refill the caches from SQL."""

    def start(self) -> RefillCommandAggregator:
        # We are the bottom layer, prev is always None.
        tic = time.perf_counter()
        info("Starting warmup.")
        info("Loading all media.")
        all_media = full_load()

        info("Gathering searchable tag names.")
        searchable_tag_names: Set[str] = set()
        for medium in all_media:
            searchable_tag_names |= medium.searchable_tag_names

        agg = RefillCommandAggregator(
            {item.medium_id: item for item in all_media},
            frozenset(searchable_tag_names),
        )

        toc = time.perf_counter()
        debug(f"Refilling cache took {1000*(toc-tic):0.1f} ms")

        return agg

    def next(
        self, cache: SubCache, agg: RefillCommandAggregator
    ) -> RefillCommandAggregator:

        cache.set(
            Query(CacheEntityKind.SEARCHABLE_TAGS, "ALL"),
            agg.searchable_tag_names,
        )
        cache.set_many(
            {
                Query(CacheEntityKind.MEDIUM_DOCUMENT, k): v
                for k, v in agg.media.items()
            }
        )
        cache.set_many(
            {
                Query(CacheEntityKind.MEDIUM_DOCUMENT_TINY, k): v
                for k, v in agg.media.items()
            }
        )
        cache.set_many(
            {
                Query(CacheEntityKind.RATING_BY_HASH, v.medium_hash): v.rating
                for k, v in agg.media.items()
            }
        )
        cache.set(
            Query(CacheEntityKind.MEDIUM_DOCUMENT_TINY_ALL, "ALL"),
            list(agg.media.values()),
        )

        return agg


REFILL = RefillCommand()


class RefreshMediumAggregator(NamedTuple):
    """Aggregator class for RefreshMediumCommand."""

    old_hashes: List[str]
    fulls: List[MediumDocument]
    tinies: Sequence[TinyMediumDocument]


class RefreshMediumCommand(Command[RefreshMediumAggregator]):
    """Completely reload these media from SQL."""

    def __init__(self, tuples: List[Tuple[int, str]]) -> None:
        self.tuples = tuples

    def start(self) -> RefreshMediumAggregator:
        old_hashes = []
        fulls = []
        tinies: List[TinyIndexedMedium] = []

        loaded_media = multi_load([t[0] for t in self.tuples])
        loaded_media_dict = {m.medium_id: m for m in loaded_media}

        for medium_id, old_hash in self.tuples:
            # We are responsible for loading the medium in document form.
            refreshed = loaded_media_dict[medium_id]

            old_hashes.append(old_hash)
            fulls.append(refreshed)
            tinies.append(TinyIndexedMedium.from_full(refreshed))

        agg = RefreshMediumAggregator(
            old_hashes=old_hashes,
            fulls=fulls,
            tinies=tinies,
        )

        return agg

    def next(
        self, cache: SubCache, agg: RefreshMediumAggregator
    ) -> RefreshMediumAggregator:
        to_delete = []
        to_set = {}

        for old_hash, full, tiny in zip(agg.old_hashes, agg.fulls, agg.tinies):
            # We need to UPDATE our cache.
            to_delete.append(Query(CacheEntityKind.RATING_BY_HASH, old_hash))

            to_set.update(
                {
                    Query(
                        CacheEntityKind.MEDIUM_DOCUMENT, full.medium_id
                    ): full,
                    Query(
                        CacheEntityKind.MEDIUM_DOCUMENT_TINY, full.medium_id
                    ): tiny,
                    Query(
                        CacheEntityKind.RATING_BY_HASH, full.medium_hash
                    ): full.rating,
                }
            )

        cache.delete(*to_delete)
        cache.set_many(to_set)

        with cache.modify(
            Query(CacheEntityKind.MEDIUM_DOCUMENT_TINY_ALL, "ALL")
        ) as modify:
            if not modify.value:
                # This cache doesn't care about these documents
                return agg

            new_tinies = []

            refreshed_by_id = {r.medium_id: r for r in agg.tinies}

            for tiny in modify.value:
                new_tinies.append(refreshed_by_id.pop(tiny.medium_id, tiny))

            modify.value = new_tinies + list(refreshed_by_id.values())

        return agg


class EmptyAggregator:
    """Aggregator class holding nothing."""


class DeleteMediumCommand(Command[EmptyAggregator]):
    """Completely delete this medium from cache."""

    def __init__(self, medium_id: int, medium_hash: str) -> None:
        self.medium_id = medium_id
        self.medium_hash = medium_hash

    def start(self) -> EmptyAggregator:
        # We are not a cache, so we don't need to delete anything
        return EmptyAggregator()

    def next(self, cache: SubCache, agg: EmptyAggregator) -> EmptyAggregator:

        with cache.modify(
            Query(CacheEntityKind.MEDIUM_DOCUMENT_TINY_ALL, "ALL")
        ) as modify:
            if not modify.value:
                # This cache doesn't care about these documents
                return agg

            modify.value = [
                t for t in modify.value if t.medium_id != self.medium_id
            ]

        cache.delete(
            Query(CacheEntityKind.MEDIUM_DOCUMENT_TINY, self.medium_id),
            Query(CacheEntityKind.MEDIUM_DOCUMENT, self.medium_id),
            Query(CacheEntityKind.RATING_BY_HASH, self.medium_hash),
        )

        return agg


class RefreshSearchableTagsAggregator(NamedTuple):
    """Aggregator class for RefreshSearchableTagsCommand."""

    searchable_tags: FrozenSet[str]


class RefreshSearchableTagsCommand(Command[RefreshSearchableTagsAggregator]):
    """Completely refresh CacheEntityKind.SEARCHABLE_TAGS from SQL."""

    def start(self) -> RefreshSearchableTagsAggregator:
        all_searchable = (
            g.db.execute(select(Tag.tag).union_all(select(TagAlias.alias)))
            .scalars()
            .all()
        )

        return RefreshSearchableTagsAggregator(frozenset(all_searchable))

    def next(
        self, cache: SubCache, agg: RefreshSearchableTagsAggregator
    ) -> RefreshSearchableTagsAggregator:
        cache.set(
            Query(CacheEntityKind.SEARCHABLE_TAGS, "ALL"),
            list(agg.searchable_tags),
        )
        return agg


REFRESH_SEARCHABLE_TAGS = RefreshSearchableTagsCommand()
