from typing import Any

from flask import appcontext_pushed

from beevenue.flask import g

from ..types import BeevenueFlask
from .fast import Fast
from .fast_signals import setup_signals


def init_app(app: BeevenueFlask) -> None:
    _set_fast()

    # Only used for testing
    # (Otherwise, this would run once per worker thread!)
    if app.config.get("BEEVENUE_DO_WARMUP", False):  # pragma: no cover
        g.fast.fill()

    setup_signals()

    appcontext_pushed.connect(_set_fast)

    teardown: Any = _close_fast
    app.teardown_appcontext(teardown)


def _set_fast(*_: Any, **__: Any) -> None:
    g.fast = Fast()


def _close_fast(_: Any) -> None:
    """Discards caches on appcontext destruction."""
    g.pop("fast", None)
