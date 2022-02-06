from pathlib import Path
import re

from flask import current_app

from beevenue import paths
from beevenue.flask import g
from ..interface import Measurements, ThumbnailingResult
from .image import image_thumbnails, measure as measure_image
from .temporary_thumbnails import temporary_thumbnails
from .video import video_thumbnails, measure as measure_video
from . import async_thumbnails


def measure(in_path: str, mime_type: str) -> Measurements:
    if re.match("image/", mime_type):
        return measure_image(in_path)
    if re.match("video/", mime_type):
        return measure_video(in_path)

    raise Exception(f"Cannot measure file with mime_type {mime_type}")


def thumbnails(
    in_path: str, extensionless_out_path: Path, mime_type: str
) -> ThumbnailingResult:
    """Generate and persist thumbnails of the file at ``in_path``."""

    if re.match("image/", mime_type):
        return image_thumbnails(in_path, extensionless_out_path)
    if re.match("video/", mime_type):
        return video_thumbnails(in_path, extensionless_out_path)

    raise Exception(f"Cannot create thumbnails for mime_type {mime_type}")


def _set_thumbnail(
    medium_hash: str, thumbnail_size: str, raw_bytes: bytes
) -> None:
    out_path = Path(paths.thumbnail_path(medium_hash, thumbnail_size))

    with open(out_path, "wb") as out_file:
        out_file.write(raw_bytes)


def generate_picks_task(medium_id: int, in_path: str) -> None:
    """Generate some preview-sized thumbnails in-memory.

    The files are temporarily persisted (in redis)."""

    async_thumbnails.start_persisting(medium_id)

    all_thumbs = []

    for _, thumbnail_size_pixels in current_app.config[
        "BEEVENUE_THUMBNAIL_SIZES"
    ].items():
        with temporary_thumbnails(
            in_path, thumbnail_size_pixels
        ) as temporary_thumbs:
            for thumb_file_name in temporary_thumbs:
                with open(thumb_file_name, "rb") as thumb_file:
                    these_bytes = thumb_file.read()
                    all_thumbs.append(
                        (
                            thumbnail_size_pixels,
                            these_bytes,
                        )
                    )

    async_thumbnails.finish_persisting(medium_id, all_thumbs)


def generate_picks(medium_id: int, in_path: str) -> None:
    current_app.generate_picks_task.delay(medium_id, in_path)  # type: ignore


def pick(medium_id: int, index: int, medium_hash: str) -> None:
    """Pick ``index`` as the new thumbnail.

    Afterwards expires all temporary thumbnails for that medium."""

    for thumbnail_size, thumbnail_size_pixels in current_app.config[
        "BEEVENUE_THUMBNAIL_SIZES"
    ].items():
        thumb = async_thumbnails.pick(medium_id, thumbnail_size_pixels, index)
        if thumb:
            _set_thumbnail(medium_hash, thumbnail_size, thumb)

    async_thumbnails.cleanup(medium_id)
