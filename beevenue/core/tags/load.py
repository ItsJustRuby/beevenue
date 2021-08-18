from typing import List, Optional, Set, Tuple

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from beevenue.flask import g

from ...models import Medium, Tag
from .tags import ValidTagName


def get(name: str) -> Optional[Tag]:
    session = g.db
    all_tags: List[Tag] = (
        session.query(Tag)
        .filter_by(tag=name)
        .options(
            joinedload(Tag.media),
            joinedload(Tag.aliases),
            joinedload(Tag.implied_by_this),
            joinedload(Tag.implying_this),
        )
        .all()
    )

    if len(all_tags) != 1:
        return None

    return all_tags[0]


def load(
    trimmed_tag_names: List[ValidTagName], medium_ids: Set[int]
) -> Optional[Tuple[Set[Tag], Set[Medium]]]:
    if not medium_ids:
        return None

    all_media = (
        Medium.query.filter(Medium.id.in_(medium_ids))
        .options(joinedload(Medium.tags), joinedload(Medium.absent_tags))
        .all()
    )

    # User submitted only ids for nonexistant media
    if not all_media:
        return None

    all_tags = (
        g.db.execute(select(Tag).filter(Tag.tag.in_(trimmed_tag_names)))
        .scalars()
        .all()
    )

    return all_tags, all_media
