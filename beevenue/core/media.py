from io import BytesIO
import json
import os
from typing import List, Optional, Tuple
import zipfile

from flask import current_app
from sqlalchemy import select, delete as sql_delete
from sqlalchemy.orm import joinedload

from beevenue import paths, signals
from beevenue.core.tags.tags import delete_orphans
from beevenue.extensions import EXTENSIONS
from beevenue.flask import g, BeevenueContext

from ..models import Medium, MediumTag, MediumTagAbsence
from .detail import MediumDetail, create_medium_detail
from .similar import similar_media
from .ffmpeg import async_thumbnails


def _try_and_remove(file: str) -> None:
    try:
        os.remove(file)
    except Exception:
        pass


def _get_metadata_bytes(medium: Medium) -> bytes:
    metadata = {
        "rating": medium.rating,
        "tags": [t.tag for t in medium.tags],
        "absent_tags": [t.tag for t in medium.absent_tags],
    }
    metadata_text = json.dumps(metadata)
    return metadata_text.encode("utf-8")


def get(
    context: BeevenueContext, medium_id: int
) -> Tuple[int, Optional[MediumDetail]]:
    maybe_medium = g.fast.get_medium(medium_id)

    if not maybe_medium:
        return 404, None

    if context.is_sfw and maybe_medium.rating != "s":
        return 400, None

    detail = create_medium_detail(
        maybe_medium,
        similar_media(context, maybe_medium),
        async_thumbnails.try_load(maybe_medium.medium_id),
    )
    return 200, detail


def get_all_ids() -> List[int]:
    """Get ids of *all* media."""

    ids: List[int] = (
        g.db.execute(select(Medium.id).order_by(Medium.id)).scalars().all()
    )
    return ids


def delete(medium_id: int) -> bool:
    """Delete medium. Return True on success, False otherwise."""

    maybe_medium = g.db.get(Medium, medium_id)

    if not maybe_medium:
        return False

    _delete(maybe_medium)

    return True


def _delete(medium: Medium) -> None:
    current_hash = medium.hash
    extension = EXTENSIONS[medium.mime_type]

    session = g.db
    medium_id = medium.id

    session.execute(
        sql_delete(MediumTag)
        .filter(MediumTag.medium_id == medium_id)
        .execution_options(synchronize_session=False)
    )
    session.execute(
        sql_delete(MediumTagAbsence)
        .filter(MediumTagAbsence.medium_id == medium_id)
        .execution_options(synchronize_session=False)
    )
    session.execute(
        sql_delete(Medium)
        .filter(Medium.id == medium_id)
        .execution_options(synchronize_session=False)
    )
    session.commit()

    delete_orphans()
    delete_medium_files(current_hash, extension)
    signals.medium_deleted.send(
        (
            medium_id,
            current_hash,
        )
    )


def delete_medium_files(medium_hash: str, extension: str) -> None:
    """Ensure medium files and thumbnails are deleted, ignoring failure."""

    _try_and_remove(paths.medium_path(f"{medium_hash}.{extension}"))

    for thumbnail_size in current_app.config["BEEVENUE_THUMBNAIL_SIZES"].keys():
        for is_animated in [False, True]:
            path = paths.thumbnail_path(
                medium_hash, thumbnail_size, is_animated=is_animated
            )
            _try_and_remove(path)


def get_zip(medium_id: int) -> Tuple[int, Optional[BytesIO]]:
    """Get zip file containing file and metadata for specific medium."""

    medium = (
        Medium.query.filter_by(id=medium_id)
        .options(joinedload(Medium.tags), joinedload(Medium.absent_tags))
        .first()
    )

    if not medium:
        return 404, None

    result_bytes = BytesIO()
    with zipfile.ZipFile(result_bytes, mode="w") as zip_file:
        # Add metadata
        metadata_bytes = _get_metadata_bytes(medium)
        zip_file.writestr(f"{medium.id}.metadata.json", metadata_bytes)

        # Add data
        extension = EXTENSIONS[medium.mime_type]
        with current_app.open_resource(
            paths.medium_path(f"{medium.hash}.{extension}"), "rb"
        ) as res:
            zip_file.writestr(f"{medium.id}.{extension}", res.read())

    result_bytes.seek(0)
    return 200, result_bytes
