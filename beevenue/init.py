from typing import Any, Optional

from flask import current_app, session
from flask_login import current_user

from .flask import BeevenueContext, BeevenueFlask, request


def _context_setter() -> None:
    """Set request.beevenue_context from request context."""

    try:
        is_sfw = session["sfwSession"]
    except Exception:
        is_sfw = True

    role = None
    if hasattr(current_user, "role"):
        role = current_user.role

    request.beevenue_context = BeevenueContext(is_sfw=is_sfw, user_role=role)


def _login_required_by_default() -> Optional[Any]:
    """Make login required by default on all endpoints.

    Can be overridden through ``does_not_require_login``.
    """

    # * endpoint is None: Can happen when /foo/ is registered,
    #   but /foo is accessed.
    # * OPTIONS queries are sent-preflight to e.g. PATCH,
    #   and do not carry session info (so we can't auth them)
    if not request.endpoint or request.method == "OPTIONS":
        return None

    view_func = current_app.view_functions[request.endpoint]

    if hasattr(view_func, "is_public"):
        return None

    if not current_user.is_authenticated:
        any_current_app: Any = current_app
        return any_current_app.login_manager.unauthorized()
    return None


def init_app(app: BeevenueFlask) -> None:
    """Register request/response lifecycle methods."""

    app.before_request(_context_setter)
    app.before_request(_login_required_by_default)
