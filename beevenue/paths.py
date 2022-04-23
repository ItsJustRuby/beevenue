import os

from flask import current_app

from beevenue.extensions import EXTENSIONS

BASE_DIR: str = "%DEFAULT%"
PUBLIC_BASE: str = "%DEFAULT%"


def _base_dir() -> str:
    global BASE_DIR  # pylint: disable=global-statement
    if BASE_DIR == "%DEFAULT%":
        BASE_DIR = current_app.config.get("BEEVENUE_STORAGE", "./")
    return BASE_DIR


def _public_base() -> str:
    global PUBLIC_BASE  # pylint: disable=global-statement
    if PUBLIC_BASE == "%DEFAULT%":
        PUBLIC_BASE = current_app.config.get(
            "BEEVENUE_PUBLIC_BASE", "https://example.org"
        )
    return PUBLIC_BASE


def thumbnail_directory() -> str:
    return os.path.join(_base_dir(), "thumbs")


def thumbnail_path(medium_hash: str, size: str, is_animated: bool) -> str:
    if is_animated:
        extension = "mp4"
    else:
        extension = "jpg"
    return os.path.join(
        _base_dir(), "thumbs", f"{medium_hash}.{size}.{extension}"
    )


def medium_path(filename: str) -> str:
    return os.path.join(_base_dir(), "media", filename)


def public_otp_path(secret: str) -> str:
    return os.path.join(_public_base(), "otp", secret)


def medium_filename(medium_hash: str, mime_type: str) -> str:
    extension = EXTENSIONS[mime_type]
    return f"{medium_hash}.{extension}"
