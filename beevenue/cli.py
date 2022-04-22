"""CLI operations for the application. Mainly used for testing."""

from datetime import date, timedelta
import os
from typing import Iterable

import click
from sqlalchemy import select
from beevenue.core import media, thumbnails
from beevenue.core.thumbnails import generate_animated
from beevenue.flask import g
from beevenue.models import Medium

from .core.file_upload import create_medium_from_upload
from .flask import BeevenueFlask
from .io import HelperBytesIO


def init_cli(app: BeevenueFlask) -> None:
    """Initialize CLI component of the application."""

    @app.cli.command("warmup")
    def _warmup() -> None:
        g.fast.fill()

    @app.cli.command("import")
    @click.argument("file_paths", nargs=-1, type=click.Path(exists=True))
    def _import(file_paths: Iterable[str]) -> None:
        """Import all the specified files. Skip invalid files."""

        for path in file_paths:
            print(f"Importing {path}...")
            with open(path, "rb") as current_file:
                file_bytes = current_file.read()
            stream = HelperBytesIO(file_bytes)
            stream.filename = os.path.basename(path)

            print("Uploading...")
            medium_id, failure = create_medium_from_upload(stream)
            if failure or not medium_id:
                print(f"Could not upload file {path}: {failure}")
                continue

            print(f"Successfully imported {path} (Medium {medium_id})")

    @app.cli.command("animate")
    @click.argument("medium_id", nargs=1, type=click.INT)
    def _animate(medium_id: int) -> None:
        res = generate_animated(medium_id)
        print(res)
        print("DONE")
