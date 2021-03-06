from enum import Enum
from hashlib import md5
from io import BytesIO
import re
from typing import Literal, Optional, Tuple, TypedDict, Union, Any

from sqlalchemy import select
import magic

from beevenue import paths, signals
from beevenue.extensions import EXTENSIONS
from beevenue.flask import g
from beevenue.io import HelperBytesIO

from ..models import Medium
from .medium_update import update_rating, update_tags
from . import thumbnails

Uploadable = Union[HelperBytesIO, Any]

TAGGY_FILENAME_REGEX = re.compile(r"^\d+ - (?P<tags>.*)\.([a-zA-Z0-9]+)$")

RATING_TAG_REGEX = re.compile(r"rating:(?P<rating>u|q|s|e)")

Readable = Union[HelperBytesIO, BytesIO]


def _md5sum(stream: Readable) -> str:
    """Return string representation of specified byte stream."""

    calc = md5()
    while True:
        buf = stream.read(1024 * 1024 * 64)
        if not buf:
            break
        calc.update(buf)

    return calc.hexdigest()


def _maybe_add_tags(medium: Medium, file: Uploadable) -> None:
    filename = file.filename
    if not filename:
        return

    match = TAGGY_FILENAME_REGEX.match(filename)
    if not match:
        print("Filename not taggy:", filename)
        return

    joined_tags = match.group("tags").replace("_", ":")
    tags = joined_tags.split(" ")
    ratings = []
    for chunk in tags:
        match = RATING_TAG_REGEX.match(chunk)
        if match:
            ratings.append(
                (
                    chunk,
                    match,
                )
            )

    rating = None
    if ratings:
        rating = ratings[0][1].group("rating")
        for (chunk, match) in ratings:
            tags.remove(chunk)

    update_tags(medium, set(tags))
    if rating:
        update_rating(medium, rating)


class UploadFailureType(Enum):
    """Reason enum why the upload could not be performed.

    When extending this, keep its values non-overlapping with
    ReplacementFailureType!"""

    SUCCESS = 0
    CONFLICTING_MEDIUM = 1
    UNKNOWN_MIME_TYPE = 2
    COULD_NOT_THUMBNAIL = 4


class _ConflictingMediumResult(TypedDict):
    type: Literal[UploadFailureType.CONFLICTING_MEDIUM]
    medium_id: int


class _UnknownMimeTypeResult(TypedDict):
    type: Literal[UploadFailureType.UNKNOWN_MIME_TYPE]
    mime_type: str


class _CouldNotThumbnailResult(TypedDict):
    type: Literal[UploadFailureType.COULD_NOT_THUMBNAIL]
    message: str


UploadFailure = Union[
    _UnknownMimeTypeResult, _ConflictingMediumResult, _CouldNotThumbnailResult
]

UploadDetails = Tuple[str, str, str]


def upload_precheck(
    file: Uploadable,
) -> Tuple[Optional[UploadDetails], Optional[UploadFailure]]:
    basename = _md5sum(file)

    conflicting_medium_id = (
        g.db.execute(select(Medium.id).filter(Medium.hash == basename))
        .scalars()
        .first()
    )
    if conflicting_medium_id:
        return (
            None,
            {
                "type": UploadFailureType.CONFLICTING_MEDIUM,
                "medium_id": conflicting_medium_id,
            },
        )

    file.seek(0)

    mime_type: str = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)
    extension = EXTENSIONS.get(mime_type)

    if not extension:
        return (
            None,
            {
                "type": UploadFailureType.UNKNOWN_MIME_TYPE,
                "mime_type": mime_type,
            },
        )

    return (mime_type, basename, extension), None


def upload_file(file: Uploadable, basename: str, extension: str) -> None:
    path = paths.medium_path(f"{basename}.{extension}")
    file.save(path)


def create_medium_from_upload(
    file: Uploadable,
) -> Tuple[Optional[int], Optional[UploadFailure]]:
    details, failure = upload_precheck(file)

    if (not details) or failure:
        return None, failure

    mime_type, basename, extension = details

    session = g.db
    medium = Medium(mime_type=mime_type, medium_hash=basename)
    session.add(medium)

    upload_file(file, basename, extension)

    status, error = thumbnails.create(medium)
    if status != 200:
        return None, {
            "type": UploadFailureType.COULD_NOT_THUMBNAIL,
            "message": error,
        }

    _maybe_add_tags(medium, file)

    session.commit()
    signals.medium_added.send(medium)
    return medium.id, None
