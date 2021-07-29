from collections import defaultdict, deque
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from flask import g

from beevenue.documents import SpindexedMedium
from beevenue.models import Medium, Tag, TagAlias, TagImplication
from beevenue.types import MediumDocument


class _DataSource:
    def __init__(
        self,
        implied_by_this: Dict[int, Set[int]],
        aliases_by_id: Dict[int, Set[str]],
        tag_name_by_id: Dict[int, str],
    ):
        self.implied_by_this = implied_by_this
        self.aliases_by_id = aliases_by_id
        self.tag_name_by_id = tag_name_by_id

    def alias_names(self, tag_ids: Iterable[int]) -> Set[str]:
        result = set()
        for tag_id in tag_ids:
            result |= self.aliases_by_id[tag_id]
        return result

    def implied(self, tag_ids: Iterable[int]) -> Tuple[Set[int], Set[str]]:
        implied_ids = set()
        for tag_id in tag_ids:
            implied_ids |= self.implied_by_this[tag_id]

        implied_names = {self.tag_name_by_id[i] for i in implied_ids}

        return implied_ids, implied_names


def _non_innate_tags(data_source: _DataSource, medium: Medium) -> Set[str]:
    extra: Set[str] = set()

    queue: deque = deque()
    initial_tag_ids = {t.id for t in medium.tags}
    queue.append(initial_tag_ids)

    while queue:
        tag_ids: List[int] = queue.pop()
        if not tag_ids:
            continue

        extra |= data_source.alias_names(tag_ids)

        implied_tag_ids, implied_tag_names = data_source.implied(tag_ids)
        extra |= implied_tag_names

        queue.append(implied_tag_ids)

    return extra


def _create_spindexed_medium(
    data_source: _DataSource, medium: Medium
) -> SpindexedMedium:
    # First, get innate tags. These will never change.
    innate_tag_names = {t.tag for t in medium.tags}

    # Follow chain of implications. Gather implied tags
    # and aliases until that queue is empty.
    extra_searchable_tags = _non_innate_tags(data_source, medium)

    searchable_tag_names = innate_tag_names | extra_searchable_tags

    absent_tag_names = {t.tag for t in medium.absent_tags}

    return SpindexedMedium(
        medium.id,
        str(medium.aspect_ratio),
        medium.hash,
        medium.mime_type,
        medium.rating,
        medium.tiny_thumbnail,
        frozenset(innate_tag_names),
        frozenset(searchable_tag_names),
        frozenset(absent_tag_names),
    )


def full_load() -> Sequence[MediumDocument]:
    session = g.db

    all_media = (
        session.query(Medium)
        .options(joinedload(Medium.tags), joinedload(Medium.absent_tags))
        .all()
    )

    all_implications = session.execute(select(TagImplication)).scalars().all()
    all_tags = session.execute(select(Tag)).scalars().all()

    tag_name_by_id = {t.id: t.tag for t in all_tags}

    # if Id=3 implies Id=5, implied_by_this[3] == set([5])
    implied_by_this = defaultdict(set)

    for i in all_implications:
        implied_by_this[i.implying_tag_id].add(i.implied_tag_id)

    all_aliases = session.execute(select(TagAlias)).scalars().all()

    aliases_by_id = defaultdict(set)
    for alias in all_aliases:
        aliases_by_id[alias.tag_id].add(alias.alias)

    data_source = _DataSource(implied_by_this, aliases_by_id, tag_name_by_id)

    media_to_cache = [
        _create_spindexed_medium(data_source, m) for m in all_media
    ]

    return media_to_cache
