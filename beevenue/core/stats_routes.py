from collections import defaultdict

from flask import Blueprint
from flask.json import jsonify

from beevenue.flask import g
from .. import permissions

bp = Blueprint("stats", __name__)


@bp.route("/stats", methods=["GET"])
@permissions.is_owner
def stats():  # type: ignore
    all_media = g.fast.get_all_tiny()

    rating_statistics = {k: 0 for k in ["s", "q", "e", "u"]}
    tag_histogram = defaultdict(int)
    absent_tag_histogram = defaultdict(int)

    for medium in all_media:
        rating_statistics[medium.rating] += 1
        tag_histogram[len(medium.innate_tag_names)] += 1
        absent_tag_histogram[len(medium.absent_tag_names)] += 1

    return jsonify(
        {
            "tagHistogram": tag_histogram,
            "absentTagHistogram": absent_tag_histogram,
            "byRating": rating_statistics,
        }
    )
