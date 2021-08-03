from typing import Any

from flask.app import Flask
from flask.ctx import _AppCtxGlobals
from sqlalchemy.orm.scoping import scoped_session

from .fast.types import Cache


class BeevenueG(_AppCtxGlobals):
    """Type hint for flask.g."""

    db: scoped_session
    fast: Cache


class BeevenueFlask(Flask):
    """Typing hint for main application object."""

    hostname: str
    port: int

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        Flask.__init__(self, name, *args, **kwargs)
