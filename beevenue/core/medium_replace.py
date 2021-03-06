from enum import Enum
from typing import Literal, Optional, TypedDict, Union

from werkzeug.datastructures import FileStorage

from beevenue.extensions import EXTENSIONS
from beevenue.flask import g
from . import thumbnails
from ..models import Medium
from .. import signals
from .file_upload import upload_precheck, upload_file, UploadFailure
from .media import delete_medium_files


class ReplacementFailureType(Enum):
    """Reason why medium could not be replaced.

    Values must extend and not overlap with UploadFailureType!
    """

    UNKNOWN_MEDIUM = 3


class _UnknownMediumResult(TypedDict):
    type: Literal[ReplacementFailureType.UNKNOWN_MEDIUM]


ReplacementFailure = Union[UploadFailure, _UnknownMediumResult]


def replace_medium(
    medium_id: int, file: FileStorage
) -> Optional[ReplacementFailure]:
    """Update file for medium with id ``medium_id``."""
    maybe_medium = g.db.get(Medium, medium_id)
    if not maybe_medium:
        return {"type": ReplacementFailureType.UNKNOWN_MEDIUM}

    details, failure = upload_precheck(file)

    if (not details) or failure:
        return failure

    old_hash = maybe_medium.hash
    old_extension = EXTENSIONS[maybe_medium.mime_type]

    mime_type, basename, extension = details

    # Upload new file
    upload_file(file, basename, extension)

    session = g.db

    # Update Medium entity with new values
    maybe_medium.mime_type = mime_type
    maybe_medium.hash = basename

    session.commit()

    # Update thumbs, tiny thumb
    thumbnails.create(maybe_medium)

    # Delete old file, thumbs
    delete_medium_files(old_hash, old_extension)

    signals.medium_file_replaced.send((old_hash, medium_id))
    return None
