from flask import Blueprint
from flask.json import jsonify

from beevenue.flask import g
from .. import permissions

bp = Blueprint("stats", __name__)


@bp.route("/stats", methods=["GET"])
@permissions.is_owner
def stats():  # type: ignore
    statistics = {k: 0 for k in ["s", "q", "e", "u"]}
    for medium in g.fast.get_all_tiny():
        statistics[medium.rating] += 1
    return jsonify(statistics)
