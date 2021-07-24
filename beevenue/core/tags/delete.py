from flask import g

from ...models import MediaTags, Tag, MediumTagAbsence, TagAlias, TagImplication


def delete_orphans() -> None:
    session = g.db

    tag_ids = (
        session.query(Tag.id)
        .outerjoin(MediaTags)
        .filter(MediaTags.c.tag_id.is_(None))
        .outerjoin(MediumTagAbsence)
        .filter(MediumTagAbsence.tag_id.is_(None))
        .outerjoin(TagAlias)
        .filter(TagAlias.tag_id.is_(None))
        .outerjoin(TagImplication, Tag.id == TagImplication.c.implied_tag_id)
        .filter(TagImplication.c.implied_tag_id.is_(None))
        .all()
    )

    tag_ids = {t[0] for t in tag_ids}

    if tag_ids:
        session.query(Tag).filter(Tag.id.in_(tag_ids)).delete(
            synchronize_session=False
        )
        session.commit()
