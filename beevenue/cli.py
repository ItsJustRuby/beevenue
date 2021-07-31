"""CLI operations for the application. Mainly used for testing."""

import os
from typing import Iterable

import click
from flask import g

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
