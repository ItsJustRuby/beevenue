from typing import Tuple, Union, Optional

from sqlalchemy import select, update as sql_update
from sqlalchemy.orm import joinedload
from flask import g

from ... import signals
from ...models import Tag, MediumTag


def _rename(old_tag: Tag, new_name: str) -> Tuple[str, Optional[Tag]]:
    new_name = new_name.strip()

    if not new_name:
        return "You must specify a new name", None

    old_name = old_tag.tag
    old_id = old_tag.id

    new_tags = (
        g.db.execute(select(Tag).filter(Tag.tag == new_name)).scalars().all()
    )

    if len(new_tags) < 1:
        # New tag doesn't exist yet. We can simply rename "old_tag".
        old_tag.tag = new_name
        signals.tag_renamed.send(
            (
                old_name,
                new_name,
            )
        )
        return "Successfully renamed tag", old_tag

    new_tag = new_tags[0]

    # if new_tag does exist, UPDATE all medium tags
    # to reference new_tag instead of old_tag and remove old_tag
    g.db.delete(old_tag)
    g.db.execute(
        sql_update(MediumTag)
        .where(MediumTag.tag_id == old_id)
        .values(tag_id=new_tag.id)
    )

    signals.tag_renamed.send(
        (
            old_name,
            new_name,
        )
    )
    return "Successfully renamed tag", new_tag


def update(tag_name: str, new_model: dict) -> Tuple[bool, Union[str, Tag]]:
    session = g.db
    tag = (
        session.query(Tag)
        .filter(Tag.tag == tag_name)
        .options(
            joinedload(Tag.media),
            joinedload(Tag.aliases),
            joinedload(Tag.implied_by_this),
            joinedload(Tag.implying_this),
        )
        .first()
    )

    if not tag:
        return False, "Could not find tag with that name"

    new_tag = None
    tag_id_to_load = tag.id

    if "tag" in new_model:
        msg, new_tag = _rename(tag, new_model["tag"])
        if not new_tag:
            return False, msg

    if "rating" in new_model:
        rating = new_model["rating"]
        if rating not in ("s", "q", "e"):
            return False, "Please specify a valid rating"

        tag.rating = rating

    session.commit()

    # Reload tag to build full viewmodel
    # (since commit() resets the previously loaded entity)
    if new_tag:
        tag_id_to_load = new_tag.id

    tag = (
        session.query(Tag)
        .filter(Tag.id == tag_id_to_load)
        .options(
            joinedload(Tag.media),
            joinedload(Tag.aliases),
            joinedload(Tag.implied_by_this),
            joinedload(Tag.implying_this),
        )
        .first()
    )

    return True, tag
