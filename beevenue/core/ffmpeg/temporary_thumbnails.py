from contextlib import AbstractContextManager
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from typing import Any, Generator

from flask import current_app

from .measure import get_length_in_ms


class _PickableThumbsContextManager(AbstractContextManager):
    """Disposable handle on a list of temporary thumbnails.

    Allows iteration over the contained files as Paths.
    On exiting this context, the contained temporary directory is disposed."""

    def __init__(self, inner: TemporaryDirectory):
        self.inner = inner

    def __iter__(self) -> Generator[Path, None, None]:
        for thumb_file_name in os.listdir(self.inner.name):
            yield Path(self.inner.name, thumb_file_name)

    def __exit__(self, exc: Any, value: Any, tb: Any) -> None:
        self.inner.__exit__(exc, value, tb)


def temporary_thumbnails(
    in_path: str, scale: int
) -> _PickableThumbsContextManager:
    """Generate some thumbnails and return a disposable handle to them."""

    thumbnail_count = current_app.config["BEEVENUE_TEMPORARY_THUMBNAIL_COUNT"]

    length_in_ms = get_length_in_ms(in_path)

    temp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
    out_pattern = Path(temp_dir.name, "out_%03d.jpg")

    cmd = [
        "ffmpeg",
        "-i",
        f"{in_path}",
        "-vf",
        f"fps={((thumbnail_count-1)*1000)}/{length_in_ms},scale={scale}:-1",
        f"{out_pattern}",
    ]

    subprocess.run(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
    )

    return _PickableThumbsContextManager(temp_dir)
