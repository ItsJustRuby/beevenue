"""CLI operations for the application. Mainly used for testing."""

from datetime import date, timedelta
import os
from typing import Iterable

import click
from sqlalchemy import select
from beevenue.core import thumbnails
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

    @app.cli.command("data-migration")
    def _migrate_data() -> None:
        # TBD: Remove this when all media are migrated and cols are non-null
        media_to_migrate = (
            g.db.execute(
                select(Medium)
                .filter(Medium.insert_date.is_(None))
                .order_by(Medium.id)
            )
            .scalars()
            .all()
        )

        for medium in media_to_migrate:
            print(f"Adding measurements to medium {medium.id}")
            thumbnails.add_measurements(medium)

            medium.insert_date = date.today() - timedelta(days=1)
            g.db.commit()
