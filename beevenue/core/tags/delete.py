from flask import g
from sentry_sdk import start_span
from sqlalchemy import select, delete

from ...models import MediumTag, Tag, MediumTagAbsence, TagAlias, TagImplication


def delete_orphans() -> None:
    with start_span(op="http", description="delete_orphans"):
        session = g.db

        subquery = (
            select(Tag.id)
            .outerjoin(MediumTag)
            .filter(MediumTag.tag_id.is_(None))
            .outerjoin(MediumTagAbsence)
            .filter(MediumTagAbsence.tag_id.is_(None))
            .outerjoin(TagAlias)
            .filter(TagAlias.tag_id.is_(None))
            .outerjoin(TagImplication, Tag.id == TagImplication.implied_tag_id)
            .filter(TagImplication.implied_tag_id.is_(None))
        )

        session.execute(
            delete(Tag)
            .filter(Tag.id.in_(subquery))
            .execution_options(synchronize_session=False)
        )
        session.commit()
