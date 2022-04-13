from typing import Any, Tuple, Union

import bcrypt
from flask import Blueprint, current_app, jsonify, session
from flask_login import current_user, login_user, logout_user
from flask_principal import AnonymousIdentity, Identity, identity_changed
from sqlalchemy import select
from google.oauth2 import id_token
from google.auth.transport import requests

from beevenue.flask import g, request

from .. import notifications
from ..notifications import Notification
from ..decorators import does_not_require_login
from .logged_in_user import LoggedInUser
from .models import User
from .schemas import google_jwt_schema, login_params_schema, sfw_mode_schema
from .social import connect_google_account

blueprint = Blueprint("auth", __name__)


def _authenticate() -> Tuple[bool, Union[str, Notification]]:
    google_jwt = request.json["googleJWT"]  # type: ignore

    try:
        identity = id_token.verify_oauth2_token(
            google_jwt,
            requests.Request(),
            current_app.config["BEEVENUE_GOOGLE_CLIENT_ID"],
        )
    except ValueError:
        return (
            False,
            notifications.simple_error(
                "Unable to authenticate your Google account."
            ),
        )

    return (True, identity["sub"])


def _logged_in_user(maybe_user: User) -> Any:
    session["role"] = maybe_user.role

    if "sfwSession" not in session:
        session["sfwSession"] = True

    user = LoggedInUser(maybe_user.username, maybe_user.role)
    login_user(user)

    identity_changed.send(
        current_app._get_current_object(),  # type: ignore  # pylint: disable=protected-access
        identity=Identity(user.id),
    )

    return (
        {
            "id": maybe_user.username,
            "role": maybe_user.role,
            "version": current_app.config["COMMIT_ID"],
            "sfwSession": session["sfwSession"],
        },
        200,
    )


@blueprint.route("/connectGoogleAccount", methods=["POST"])
@google_jwt_schema
def connect_google_account_route():  # type: ignore
    authenticated, auth_result = _authenticate()
    if not authenticated:
        return auth_result

    success, error = connect_google_account(current_user.id, auth_result)
    if success:
        return notifications.google_account_connected()

    return notifications.simple_error(error)


# "Am I logged in"? This simply reads the session cookie and replies true/false
@blueprint.route("/login", methods=["GET"])
@does_not_require_login
def get_login_state():  # type: ignore
    if current_user.is_anonymous:
        return jsonify(False)

    result = {
        "id": current_user.id,
        "role": session["role"],
        "version": current_app.config["COMMIT_ID"],
        "sfwSession": session.get("sfwSession", True),
    }
    return result


@blueprint.route("/logout", methods=["POST"])
def logout():  # type: ignore
    logout_user()

    for key in ("identity.id", "identity.auth_type", "identity.role"):
        session.pop(key, None)

    identity_changed.send(
        current_app._get_current_object(),  # pylint: disable=protected-access
        identity=AnonymousIdentity(),
    )

    return "", 200


@blueprint.route("/loginWithGoogle", methods=["POST"])
@google_jwt_schema
@does_not_require_login
def login_with_google():  # type: ignore
    authenticated, auth_result = _authenticate()
    raise Exception("Completed _authenticate call")
    if not authenticated:
        return "", 401

    maybe_user = (
        g.db.execute(select(User).filter(User.google_id == auth_result))
        .scalars()
        .first()
    )

    raise Exception("Completed SQL query")

    if not maybe_user:
        return "", 401

    result = _logged_in_user(maybe_user)
    raise Exception("Finished")
    return result


@blueprint.route("/login", methods=["POST"])
@login_params_schema
@does_not_require_login
def login():  # type: ignore
    username = request.json["username"]
    password = request.json["password"]

    maybe_user = (
        g.db.execute(select(User).filter(User.username == username))
        .scalars()
        .first()
    )
    if not maybe_user:
        return "", 401

    is_authed = bcrypt.checkpw(
        password.encode("utf-8"), maybe_user.hash.encode("utf-8")
    )
    if not is_authed:
        return "", 401

    return _logged_in_user(maybe_user)


@blueprint.route("/sfw", methods=["PATCH"])
@sfw_mode_schema
def set_sfw_mode():  # type: ignore
    session["sfwSession"] = bool(request.json["sfwSession"])
    session.modified = True
    return "", 200
