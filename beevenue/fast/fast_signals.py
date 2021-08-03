from typing import Any, List, Tuple

from beevenue.flask import g

from beevenue import signals
from beevenue.models import Medium

from . import commands


def _nuke(*_: Any, **__: Any) -> None:
    g.fast.run(commands.REFILL)


def _medium_file_replaced(msg: Tuple[str, int]) -> None:
    old_hash, medium_id = msg
    g.fast.run(
        commands.RefreshMediumCommand(
            [
                (
                    medium_id,
                    old_hash,
                )
            ]
        )
    )


def _delete_medium(msg: Tuple[int, str]) -> None:
    medium_id, medium_hash = msg
    g.fast.run(commands.DeleteMediumCommand(medium_id, medium_hash))


def _add_media(media: List[Medium]) -> None:
    params = [
        (
            m.id,
            m.hash,
        )
        for m in media
    ]
    g.fast.run(commands.RefreshMediumCommand(params))


def _add_medium(medium: Medium) -> None:
    g.fast.run(
        commands.RefreshMediumCommand(
            [
                (
                    medium.id,
                    medium.hash,
                )
            ]
        )
    )


def _refresh_metadata(medium: Medium) -> None:
    g.fast.run(
        commands.RefreshMediumCommand(
            [
                (
                    medium.id,
                    medium.hash,
                )
            ]
        ),
        commands.REFRESH_SEARCHABLE_TAGS,
    )


def setup_signals() -> None:
    # These actions happen so rarely, it's fine to just completely
    # reload the cache.
    signals.tag_renamed.connect(_nuke)

    signals.alias_added.connect(_nuke)
    signals.alias_removed.connect(_nuke)

    signals.implication_added.connect(_nuke)
    signals.implication_removed.connect(_nuke)

    # These are specific, but easy to update (only affect exactly
    # media documents)
    signals.medium_file_replaced.connect(_medium_file_replaced)
    signals.medium_added.connect(_add_medium)
    signals.medium_deleted.connect(_delete_medium)
    signals.media_updated.connect(_add_media)

    # This requires the most finesse, so it uses multiple successive commands.
    signals.medium_metadata_changed.connect(_refresh_metadata)
