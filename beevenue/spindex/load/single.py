from typing import Iterable, Optional, Set, Tuple

from flask import g
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from . import AbstractDataSource, create_spindexed_medium
from ...models import Medium, Tag, TagAlias, TagImplication
from ...types import MediumDocument


class _SingleLoadDataSource(AbstractDataSource):
    def __init__(self) -> None:
        self.session = g.db

    def alias_names(self, tag_ids: Iterable[int]) -> Set[str]:
        tag_aliases = (
            self.session.execute(
                select(TagAlias.alias).filter(TagAlias.tag_id.in_(tag_ids))
            )
            .scalars()
            .all()
        )

        return set(tag_aliases)

    def implied(self, tag_ids: Iterable[int]) -> Tuple[Set[int], Set[str]]:
        implied_tag_ids = (
            self.session.execute(
                select(TagImplication.implied_tag_id).filter(
                    TagImplication.implying_tag_id.in_(tag_ids)
                )
            )
            .scalars()
            .all()
        )

        implied_tag_ids = set(implied_tag_ids)

        implied_tag_names = (
            self.session.execute(
                select(Tag.tag).filter(Tag.id.in_(implied_tag_ids))
            )
            .scalars()
            .all()
        )

        implied_tag_names = set(implied_tag_names)

        return implied_tag_ids, implied_tag_names


def single_load(medium_id: int) -> Optional[MediumDocument]:
    matching_medium = (
        g.db.query(Medium)
        .filter_by(id=medium_id)
        .options(joinedload(Medium.tags), joinedload(Medium.absent_tags))
        .first()
    )

    return create_spindexed_medium(_SingleLoadDataSource(), matching_medium)
