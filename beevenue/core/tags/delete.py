from flask import g

from ...models import MediaTags, Tag, MediumTagAbsence, TagAlias, TagImplication


def delete_orphans() -> None:
    session = g.db

    tags_to_delete = (
        session.query(Tag)
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

    for tag in tags_to_delete:
        session.delete(tag)

    if tags_to_delete:
        session.commit()
