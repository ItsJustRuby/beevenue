from typing import Any
from ..flask import BeevenueFlask

from .routes import bp
from .json import RuleEncoder


def init_app(app: BeevenueFlask) -> None:
    app.register_blueprint(bp)
    json_encoder: Any = RuleEncoder
    app.json_encoder = json_encoder
