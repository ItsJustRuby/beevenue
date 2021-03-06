from math import ceil
from pathlib import Path

from PIL import Image
from flask import current_app

from ..interface import SuccessThumbnailingResult, Measurements


def _constrain_aspect_ratio(img: Image) -> Image:
    """Constrain an image to an aspect ratio bigger than the minimum.

    This makes it so overly tall pictures don't distort the grid in which they
    are displayed (especially noticeable for multi-panel comics with aspect
    ratio of >2).
    """

    min_aspect_ratio = current_app.config["BEEVENUE_MINIMUM_ASPECT_RATIO"]
    aspect_ratio = img.width / img.height

    if aspect_ratio < min_aspect_ratio:
        maximum_height = round((1 / min_aspect_ratio) * img.width)
        img = img.crop((0, 0, img.width, maximum_height))

    return img


def _get_thumbnail(
    img: Image, width: int, height: int, aspect_ratio: float, min_axis: int
) -> Image:

    if width > height:
        min_height = min_axis
        min_width = int(ceil(aspect_ratio * min_height))
    else:
        min_width = min_axis
        min_height = int(ceil(min_width / aspect_ratio))

    thumbnail = img.copy()
    thumbnail.thumbnail((min_width, min_height))

    thumbnail = _constrain_aspect_ratio(thumbnail)

    if thumbnail.mode != "RGB":
        thumbnail = thumbnail.convert("RGB")

    return thumbnail


def measure(in_path: str) -> Measurements:
    filesize = Path(in_path).stat().st_size
    with Image.open(in_path) as img:
        width, height = img.size
    return Measurements(width=width, height=height, filesize=filesize)


def image_thumbnails(
    in_path: str, extensionless_out_path: Path
) -> SuccessThumbnailingResult:
    """Generate thumbnails for given image and save them to disk."""
    with Image.open(in_path) as img:
        width, height = img.size
        aspect_ratio = float(width) / height

        for thumbnail_size, thumbnail_size_pixels in current_app.config[
            "BEEVENUE_THUMBNAIL_SIZES"
        ].items():
            min_axis = thumbnail_size_pixels
            out_path = extensionless_out_path.with_suffix(
                f".{thumbnail_size}.jpg"
            )

            thumbnail = _get_thumbnail(
                img, width, height, aspect_ratio, min_axis
            )

            thumbnail.save(
                out_path, quality=80, progressive=True, optimize=True
            )

        return SuccessThumbnailingResult()
