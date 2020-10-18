from flask import Blueprint, jsonify

from .. import permissions
from .init import full_load
from .spindex import SPINDEX

bp = Blueprint("spindex", __name__)


@bp.route("/spindex/status")
@permissions.is_owner
def status():  # type: ignore
    output = []
    for medium in SPINDEX.all():
        output.append(
            {"id": medium.id, "rating": medium.rating, "hash": medium.hash}
        )

    return jsonify(output), 200


@bp.route("/spindex/reindex", methods=["POST"])
@permissions.is_owner
def reindex():  # type: ignore
    full_load()
    return f"Full load finished. Loaded {len(SPINDEX.all())} entries.", 200
