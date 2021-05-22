import os

from flask import current_app

from beevenue.extensions import EXTENSIONS


def _base_dir() -> str:
    return current_app.config.get("BEEVENUE_STORAGE", "./")


def thumbnail_directory() -> str:
    return os.path.join(_base_dir(), "thumbs")


def thumbnail_path(medium_hash: str, size: str) -> str:
    return os.path.join(_base_dir(), "thumbs", f"{medium_hash}.{size}.jpg")


def medium_directory() -> str:
    return os.path.join(_base_dir(), "media")


def medium_path(filename: str) -> str:
    return os.path.join(_base_dir(), "media", filename)


def medium_filename(medium_hash: str, mime_type: str) -> str:
    extension = EXTENSIONS[mime_type]
    return f"{medium_hash}.{extension}"
