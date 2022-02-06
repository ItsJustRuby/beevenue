from collections import defaultdict, deque
from typing import List, Sequence, Set

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from beevenue.flask import g

from beevenue.documents import IndexedMedium
from beevenue.models import Medium, Tag, TagAlias, TagImplication
from beevenue.document_types import MediumDocument

from .data_source import (
    AbstractDataSource,
    FullLoadDataSource,
    MultiLoadDataSource,
)


def _non_innate_tags(
    data_source: AbstractDataSource, medium: Medium
) -> Set[str]:
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


def _create_indexed_medium(
    data_source: AbstractDataSource, medium: Medium
) -> IndexedMedium:
    # First, get innate tags. These will never change.
    innate_tag_names = {t.tag for t in medium.tags}

    # Follow chain of implications. Gather implied tags
    # and aliases until that queue is empty.
    extra_searchable_tags = _non_innate_tags(data_source, medium)

    searchable_tag_names = innate_tag_names | extra_searchable_tags

    absent_tag_names = {t.tag for t in medium.absent_tags}

    return IndexedMedium(
        medium.id,
        medium.hash,
        medium.mime_type,
        medium.rating,
        medium.width,
        medium.height,
        medium.filesize,
        medium.insert_date,
        medium.tiny_thumbnail,
        frozenset(innate_tag_names),
        frozenset(searchable_tag_names),
        frozenset(absent_tag_names),
    )


def multi_load(medium_ids: List[int]) -> List[MediumDocument]:
    matching_media = (
        g.db.query(Medium)
        .options(joinedload(Medium.tags), joinedload(Medium.absent_tags))
        .filter(Medium.id.in_(medium_ids))
        .all()
    )

    relevant_tag_ids = set()
    for medium in matching_media:
        relevant_tag_ids |= {t.id for t in medium.tags}

    data_source = MultiLoadDataSource(frozenset(relevant_tag_ids))

    return [_create_indexed_medium(data_source, m) for m in matching_media]


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

    data_source = FullLoadDataSource(
        implied_by_this, aliases_by_id, tag_name_by_id
    )

    media_to_cache = [_create_indexed_medium(data_source, m) for m in all_media]

    return media_to_cache
