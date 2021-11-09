from io import BytesIO
import os
import re
from typing import Optional, Tuple
from pathlib import Path

from PIL import Image
from flask import current_app, g

from beevenue import paths
from beevenue.extensions import EXTENSIONS

from . import ffmpeg
from ..models import Medium
from .interface import ThumbnailingResult


def _thumbnailable_video(
    medium_id: int,
) -> Tuple[int, Optional[Tuple[str, Medium]]]:
    session = g.db
    medium = session.get(Medium, medium_id)

    if not medium:
        return 404, None

    if not re.match("video/", medium.mime_type):
        return 400, None

    extension = EXTENSIONS[medium.mime_type]
    origin_path = paths.medium_path(f"{medium.hash}.{extension}")
    return 200, (origin_path, medium)


def generate_picks(medium_id: int) -> int:
    status_code, details = _thumbnailable_video(medium_id)

    if status_code != 200 or (details is None):
        return status_code

    origin_path, _ = details
    ffmpeg.generate_picks(medium_id, origin_path)
    return 200


def pick(medium_id: int, thumb_index: int) -> int:
    status_code, details = _thumbnailable_video(medium_id)

    if status_code != 200 or (details is None):
        return status_code

    _, medium = details
    ffmpeg.pick(medium_id, thumb_index, medium.hash)
    _generate_tiny(medium)
    return 200


def create(medium: Medium) -> Tuple[int, str]:
    session = g.db

    thumbnailing_result = _create(medium.mime_type, medium.hash)

    if thumbnailing_result.error:
        return 400, thumbnailing_result.error

    medium.aspect_ratio = thumbnailing_result.aspect_ratio
    session.commit()
    _generate_tiny(medium)
    return 200, ""


def _create(mime_type: str, medium_hash: str) -> ThumbnailingResult:
    extensionless_thumb_path = Path(
        os.path.join(paths.thumbnail_directory(), medium_hash)
    )

    extension = EXTENSIONS[mime_type]

    origin_path = paths.medium_path((f"{medium_hash}.{extension}"))
    return ffmpeg.thumbnails(origin_path, extensionless_thumb_path, mime_type)


def _generate_tiny(medium: Medium) -> None:
    size, _ = list(current_app.config["BEEVENUE_THUMBNAIL_SIZES"].items())[0]
    tiny_thumb_res = current_app.config["BEEVENUE_TINY_THUMBNAIL_SIZE"]

    out_path = paths.thumbnail_path(medium_hash=medium.hash, size=size)

    with Image.open(out_path, "r") as img:
        thumbnail = img.copy()
        thumbnail.thumbnail((tiny_thumb_res, tiny_thumb_res))

        with BytesIO() as out_bytes_io:
            thumbnail.save(
                out_bytes_io, format="JPEG", optimize=True, quality=75
            )
            out_bytes = out_bytes_io.getvalue()

    medium.tiny_thumbnail = out_bytes
    g.db.commit()
