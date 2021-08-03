from typing import Any, Optional

from flask import Request, Response, g as flask_g, request as flask_request

from .convert import try_convert_model
from .types import BeevenueFlask, BeevenueG


class BeevenueContext:
    """Customized request context."""

    def __init__(self, is_sfw: bool, user_role: Optional[str]):
        self.is_sfw = is_sfw
        self.user_role = user_role


class BeevenueResponse(Response):
    """Customized response object."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)


class BeevenueRequest(Request):
    """Customized request class."""

    beevenue_context: BeevenueContext


request: BeevenueRequest = flask_request  # type: ignore
g: BeevenueG = flask_g  # type: ignore


class BeevenueFlaskImpl(BeevenueFlask):
    """Custom implementation of Flask application"""

    request_class = BeevenueRequest
    response_class = BeevenueResponse

    def __init__(
        self, name: str, hostname: str, port: int, *args: Any, **kwargs: Any
    ) -> None:
        BeevenueFlask.__init__(self, name, *args, **kwargs)
        self.hostname = hostname
        self.port = port

    def make_response(self, rv: Any) -> Any:
        model = try_convert_model(rv)
        res: Any = super().make_response(model)
        return res
