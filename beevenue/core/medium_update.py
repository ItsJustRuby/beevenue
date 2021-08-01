from typing import Iterable, List, Optional, Set, Tuple

from flask import g
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload

from beevenue.flask import request

from . import tags
from ..types import MediumDocument
from ..models import MediumTag, Medium, Tag, MediumTagAbsence
from .. import signals
from .detail import MediumDetail, create_medium_detail
from .media import similar_media
from .tags import ValidTagName, delete_orphans
from .tags.new import create


def update_rating(medium: Medium, new_rating: str) -> bool:
    if new_rating not in (medium.rating, "u"):
        medium.rating = new_rating
        return True
    return False


def _distinguish(
    new_tags: List[ValidTagName],
) -> Tuple[Set[ValidTagName], Set[int]]:
    # Lookup ids for all input tags
    if len(new_tags) == 0:
        existing_tags = []
    else:
        existing_tags = (
            g.db.execute(select(Tag).filter(Tag.tag.in_(new_tags)))
            .scalars()
            .all()
        )

    existing_tag_id_by_name = {}
    for tag in existing_tags:
        existing_tag_id_by_name[tag.tag] = tag.id

    existing_tag_names = existing_tag_id_by_name.keys()

    # foreach tag not found in database, create tag
    unknown_tag_names = set(new_tags) - set(existing_tag_names)

    return unknown_tag_names, set(existing_tag_id_by_name.values())


def _autocreate(unknown_tag_names: Set[ValidTagName]) -> List[Tag]:
    new_tags = []
    need_to_commit = False

    session = g.db

    for unknown_tag_name in unknown_tag_names:
        needs_to_be_inserted, matching_tag = create(unknown_tag_name)

        if needs_to_be_inserted:
            session.add(matching_tag)
            need_to_commit = True
        new_tags.append(matching_tag)

    # We need this to get the ids to insert into MediumTag later!
    if need_to_commit:
        session.commit()

    return new_tags


def _ensure(
    medium: Medium, existing_tag_ids: Set[int], new_tags: Iterable[Tag]
) -> None:
    session = g.db

    target_tag_ids = existing_tag_ids | {t.id for t in new_tags}

    # ensure that medium_tags contains exactly that set
    session.execute(
        delete(MediumTag)
        .filter(MediumTag.medium_id == medium.id)
        .execution_options(synchronize_session=False)
    )

    for tag_id in target_tag_ids:
        media_tag = MediumTag()
        media_tag.medium_id = medium.id
        media_tag.tag_id = tag_id
        session.add(media_tag)

    session.commit()


def _ensure_absent(medium: Medium, new_absent_tag_ids: Set[int]) -> None:
    session = g.db

    session.execute(
        delete(MediumTagAbsence)
        .filter(MediumTagAbsence.medium_id == medium.id)
        .execution_options(synchronize_session=False)
    )
    session.commit()

    for tag_id in new_absent_tag_ids:
        absence = MediumTagAbsence()
        absence.medium_id = medium.id
        absence.tag_id = tag_id
        session.add(absence)

    session.commit()


def update_tags(medium: Medium, new_tags: Set[str]) -> bool:
    validated_tags = tags.validate(new_tags)

    unknown_tag_names, existing_tag_ids = _distinguish(validated_tags)
    created_tags = _autocreate(unknown_tag_names)
    _ensure(medium, existing_tag_ids, created_tags)

    delete_orphans()
    return True


def update_absent_tags(medium: Medium, new_absent_tags: Set[str]) -> bool:
    validated_absent_tags = tags.validate(new_absent_tags)
    _, existing_tag_ids = _distinguish(validated_absent_tags)

    _ensure_absent(medium, existing_tag_ids)
    return True


def _reject_direct_overlap(
    new_tags: Set[str], new_absent_tags: Set[str]
) -> bool:
    # A medium can't have the same (non-implied) tag both present and absent.
    # If we receive such a request, we just don't apply that change.
    return bool(new_tags & new_absent_tags)


def _reject_implication_overlap(
    medium: Medium, new_absent_tags: Set[str]
) -> bool:
    # Figure out if we want to mark a tag as both absent and implied. Reject.

    medium = (
        g.db.query(Medium)
        .filter(Medium.id == medium.id)
        .options(joinedload(Medium.tags).joinedload(Tag.implied_by_this))
    ).first()

    searchable_tag_names = set()
    for tag in medium.tags:
        searchable_tag_names.add(tag.tag)
        searchable_tag_names |= {t.tag for t in tag.implied_by_this}

    return bool(new_absent_tags & searchable_tag_names)


def _update_tags_and_absents(
    medium: Medium, new_tags: Set[str], new_absent_tags: Set[str]
) -> None:
    new_tag_set = set(new_tags)
    new_absent_tag_set = set(new_absent_tags)

    if _reject_direct_overlap(new_tag_set, new_absent_tag_set):
        return

    update_tags(medium, new_tag_set)

    if _reject_implication_overlap(medium, new_absent_tag_set):
        return

    update_absent_tags(medium, new_absent_tag_set)


def update_medium(
    medium_id: int,
    new_rating: str,
    new_tags: List[str],
    new_absent_tags: List[str],
) -> Optional[MediumDetail]:

    maybe_medium = g.db.get(Medium, medium_id)
    if not maybe_medium:
        return None

    update_rating(maybe_medium, new_rating)
    _update_tags_and_absents(maybe_medium, set(new_tags), set(new_absent_tags))

    signals.medium_metadata_changed.send(maybe_medium)

    result: MediumDocument = g.fast.get_medium(maybe_medium.id)  # type: ignore

    return create_medium_detail(
        result, similar_media(request.beevenue_context, result)
    )
