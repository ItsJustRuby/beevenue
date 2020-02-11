from flask import session, request, current_app
from flask_login import current_user

from ...db import db


class BeevenueContext(object):
    def __init__(self, is_sfw, user_role):
        self.is_sfw = is_sfw
        self.user_role = user_role

    def session(self):
        return db.session


def context_setter():
    try:
        is_sfw = session["sfwSession"]
    except Exception:
        is_sfw = True

    role = None
    if hasattr(current_user, "role"):
        role = current_user.role

    request.beevenue_context = BeevenueContext(is_sfw=is_sfw, user_role=role)


def login_required_by_default():
    # * endpoint is None: Can happen when /foo/ is registered,
    #   but /foo is accessed.
    # * OPTIONS queries are sent-preflight to e.g. PATCH,
    #   and do not carry session info (so we can't auth them)
    if not request.endpoint or request.method == "OPTIONS":
        return

    view_func = current_app.view_functions[request.endpoint]

    if hasattr(view_func, "is_public"):
        return

    if not current_user.is_authenticated:
        return current_app.login_manager.unauthorized()


def set_client_hint_headers(res):
    client_hint_fields = ["DPR", "Viewport-Width", "Width", "Downlink"]

    if "Accept-CH" not in res.headers:
        res.headers["Accept-CH"] = ", ".join(client_hint_fields)

    if "Accept-CH-Lifetime" not in res.headers:
        res.headers["Accept-CH-Lifetime"] = 86400

    for x in client_hint_fields:
        res.vary.add(x)

    # Turns out that Flask CORS sometimes just doesn't set this header? Hm.
    if "Access-Control-Allow-Credentials" not in res.headers:
        res.headers["Access-Control-Allow-Credentials"] = "true"

    if "Access-Control-Allow-Origin" not in res.headers:
        res.headers["Access-Control-Allow-Origin"] = ",".join(
            current_app.config["BEEVENUE_ALLOWED_CORS_ORIGINS"]
        )

    return res


def init_app(app):
    app.before_request(context_setter)
    app.before_request(login_required_by_default)
    app.after_request(set_client_hint_headers)
