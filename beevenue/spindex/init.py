from typing import Any

from flask import g

from ..flask import BeevenueFlask
from .signal_handlers import setup_signals
from .spindex import Spindex


def init_app(app: BeevenueFlask) -> None:
    _set_spindex()
    app.before_request(_set_spindex)

    teardown: Any = _close_spindex
    app.teardown_appcontext(teardown)

    setup_signals()


def _set_spindex() -> None:
    g.spindex = Spindex()


def _close_spindex(_: Any) -> None:
    """Discards last db session on appcontext destruction."""
    g.pop("spindex", None)
