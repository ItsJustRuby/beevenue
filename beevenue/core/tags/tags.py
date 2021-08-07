from typing import Iterable, List, NewType
import re

from beevenue.flask import g
from sentry_sdk import start_span
from sqlalchemy import select, delete
from sqlalchemy.orm import aliased

from ...models import MediumTag, Tag, MediumTagAbsence, TagAlias, TagImplication


VALID_TAG_REGEX_INNER = "(?P<category>[a-z]+:)?([a-zA-Z0-9.]+)"
VALID_TAG_REGEX = re.compile(f"^{VALID_TAG_REGEX_INNER}$")

ValidTagName = NewType("ValidTagName", str)


def tag_name_selector(tag: Tag) -> str:
    name: str = tag.tag
    return name


def validate(tag_names: Iterable[str]) -> List[ValidTagName]:
    """
    Filters input iterable such that it only contains valid tag names.
    """
    return [
        ValidTagName(n.strip()) for n in tag_names if VALID_TAG_REGEX.match(n)
    ]


def delete_orphans() -> None:
    with start_span(op="http", description="delete_orphans"):
        session = g.db

        tag_implications_a = aliased(TagImplication)
        tag_implications_b = aliased(TagImplication)

        subquery = (
            select(Tag.id)
            .outerjoin(MediumTag)
            .filter(MediumTag.tag_id.is_(None))
            .outerjoin(MediumTagAbsence)
            .filter(MediumTagAbsence.tag_id.is_(None))
            .outerjoin(TagAlias)
            .filter(TagAlias.tag_id.is_(None))
            .outerjoin(
                tag_implications_a, Tag.id == tag_implications_a.implied_tag_id
            )
            .filter(tag_implications_a.implied_tag_id.is_(None))
            .outerjoin(
                tag_implications_b, Tag.id == tag_implications_b.implying_tag_id
            )
            .filter(tag_implications_b.implying_tag_id.is_(None))
        )

        session.execute(
            delete(Tag)
            .filter(Tag.id.in_(subquery))
            .execution_options(synchronize_session=False)
        )
        session.commit()
