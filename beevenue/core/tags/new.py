from typing import Iterable, Optional, Set, Tuple

from sqlalchemy.orm import joinedload
from beevenue.flask import g

from ...models import Tag, Medium, TagAlias
from ... import signals
from .tags import ValidTagName, validate
from .load import load


def _add_all(
    is_absent: bool,
    trimmed_tag_names: Iterable[ValidTagName],
    tags: Set[Tag],
    media: Set[Medium],
) -> int:
    tags_by_name = {t.tag: t for t in tags}

    if is_absent:
        tags_selector = lambda m: m.absent_tags
    else:
        tags_selector = lambda m: m.tags

    added_count = 0
    for tag_name in trimmed_tag_names:
        if tag_name not in tags_by_name:
            # User might have entered a valid, but non-existant tag
            continue

        tag = tags_by_name[tag_name]
        for medium in media:
            target = tags_selector(medium)
            if tag not in target:
                target.append(tag)
                added_count += 1

    g.db.commit()

    # In this method, we have either added present or absent tags
    # to these media, never created them. So overall, this simple signal
    # is the most efficient and still safe to use.
    signals.media_updated.send(media)
    return added_count


def add_batch(
    is_absent: bool, tag_names: Iterable[str], medium_ids: Set[int]
) -> Optional[int]:

    trimmed_tag_names = validate(tag_names)

    loaded = load(trimmed_tag_names, medium_ids)

    if not loaded:
        return None

    added_count = _add_all(is_absent, trimmed_tag_names, *loaded)
    return added_count


def create(name: ValidTagName) -> Tuple[bool, Tag]:
    """Return tuple of (needs_to_be_inserted, matching_tag)."""

    # Don't create tag if there is another tag that has 'name' as an alias
    maybe_conflict = (
        g.db.query(TagAlias)
        .options(joinedload(TagAlias.tag))
        .filter_by(alias=name)
        .first()
    )
    if maybe_conflict:
        return False, maybe_conflict.tag

    return True, Tag.create(name)  # type: ignore
