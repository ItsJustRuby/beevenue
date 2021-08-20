from base64 import b64encode

from pathlib import Path

from flask import Blueprint, redirect
from flask.helpers import make_response

from beevenue import paths
from beevenue.decorators import does_not_require_login
from beevenue.flask import g, request, BeevenueResponse

from .. import notifications, permissions
from . import thumbnails, otp
from .search import search
from ..models import Medium
from .schemas import search_query_params_schema

bp = Blueprint("routes", __name__)


@bp.route("/search")
@search_query_params_schema
def search_endpoint():  # type: ignore
    search_term_list = request.args.get("q").split(" ")
    return search.run(search_term_list)


@bp.route("/thumbnail/<int:medium_id>", methods=["PATCH"])
@permissions.is_owner
def create_thumbnail(medium_id: int):  # type: ignore
    medium = g.db.get(Medium, medium_id)
    if not medium:
        return notifications.no_such_medium(medium_id), 404

    status_code, message = thumbnails.create(medium)

    return message, status_code


@bp.route(
    "/medium/<int:medium_id>/thumbnail/picks/<int:thumbnail_count>",
    methods=["GET"],
)
@permissions.is_owner
def show_thumbnail_picks(medium_id: int, thumbnail_count: int):  # type: ignore
    status_code, list_of_bytes = thumbnails.generate_picks(
        medium_id, thumbnail_count
    )

    if status_code != 200 or (list_of_bytes is None):
        return "", status_code

    # Idea: We could also use a zip file.
    base64_strings = []

    for byte in list_of_bytes:
        base64_strings.append(b64encode(byte).decode("utf-8"))

    return {"thumbs": base64_strings}


@bp.route(
    "/medium/<int:medium_id>/thumbnail/pick/"
    "<int:thumb_index>/<int:thumbnail_count>",
    methods=["PATCH"],
)
@permissions.is_owner
def pick_thumbnail(  # type: ignore
    medium_id: int, thumb_index: int, thumbnail_count: int
):
    status_code = thumbnails.pick(medium_id, thumb_index, thumbnail_count)

    return notifications.new_thumbnail(), status_code


def _sendfile_response(nginx_path: Path) -> BeevenueResponse:
    # Default Content-Type is text/html, and nginx will simply forward that.
    # For media files and thumbs, that will be incorrect.
    # If we set "", nginx will determine the Content-Type from the actual file.
    res = make_response(("", 200, {"Content-Type": ""}))

    res.headers["X-Accel-Redirect"] = str(nginx_path)
    return res  # type: ignore


@bp.route("/thumbs/<string:full_path>")
@permissions.get_medium_file
def get_thumb(full_path: str):  # type: ignore
    return _sendfile_response(Path("/", "beevenue_thumbs", full_path))


@bp.route("/files/<string:full_path>")
@permissions.get_medium_file
def get_file(full_path: str):  # type: ignore
    return _sendfile_response(Path("/", "media", full_path))


@bp.route("/medium/<int:medium_id>/otp", methods=["GET"])
@permissions.get_medium
def request_otp(medium_id):  # type: ignore
    secret = otp.request(medium_id)
    if not secret:
        return "", 400

    secret_path = paths.public_otp_path(secret)
    target = request.args.get("target", "")
    return redirect(f"{target}{secret_path}")


@bp.route("/otp/<string:secret>")
@does_not_require_login
def get_otp(secret: str):  # type: ignore
    full_path = otp.resolve_and_destroy(secret)
    if full_path:
        return _sendfile_response(Path("/", "media", full_path))
    return "", 400
