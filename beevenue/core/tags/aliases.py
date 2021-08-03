from typing import Optional

from beevenue.flask import g
from sqlalchemy import select
from sqlalchemy.sql.expression import func

from .tags import delete_orphans
from ...models import Tag, TagAlias
from ... import signals


def add_alias(current_name: str, new_alias: str) -> Optional[str]:
    """Try to add ``new_alias`` as an alias to the tag ``current_name``.

    Returns error on failure, else None."""

    session = g.db

    old_tags = (
        session.execute(select(Tag).filter(Tag.tag == current_name))
        .scalars()
        .all()
    )

    if len(old_tags) != 1:
        return "Could not find tag with that name"

    new_alias = new_alias.strip()

    conflicting_aliases_count = (
        session.execute(
            select(func.count(TagAlias.id)).filter(TagAlias.alias == new_alias)
        )
    ).scalar()
    if conflicting_aliases_count > 0:
        return "This alias is already taken"

    # Ensure that there is no tag with the new_alias as actual name
    conflicting_tags_count = (
        session.execute(select(func.count(Tag.id)).filter(Tag.tag == new_alias))
    ).scalar()

    if conflicting_tags_count > 0:
        return "This alias is already taken"

    old_tag = old_tags[0]
    alias = TagAlias(old_tag.id, new_alias)
    session.add(alias)
    session.commit()
    signals.alias_added.send(
        (
            old_tag.tag,
            new_alias,
        )
    )
    return None


def remove_alias(name: str, alias: str) -> None:
    """Remove alias ``alias`` from tag ``name``.

    Always succeeds, even if tag or alias do not exist."""
    session = g.db

    old_tag_count = session.execute(
        select(func.count(Tag.id)).filter(Tag.tag == name)
    ).scalar()
    if old_tag_count != 1:
        return None

    current_aliases = (
        (session.execute(select(TagAlias).filter(TagAlias.alias == alias)))
        .scalars()
        .all()
    )

    if len(current_aliases) == 0:
        return None

    session.delete(current_aliases[0])
    session.commit()
    delete_orphans()
    signals.alias_removed.send(alias)
    return None
