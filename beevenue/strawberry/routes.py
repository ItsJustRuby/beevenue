from typing import List

from flask import Blueprint, current_app, make_response
from flask.json import dumps, jsonify

from beevenue.flask import request
from beevenue import notifications

from .. import permissions
from .get import get_rules, get_violations, random_rule_violation, summary
from .json import decode_rules_list
from .rule import Rule

bp = Blueprint("strawberry", __name__)


def _persist(rules_list: List[Rule]) -> None:
    res = dumps(rules_list, indent=4, separators=(",", ": "))
    rules_file_path = current_app.config["BEEVENUE_RULES_FILE"]
    with open(rules_file_path, "w") as rules_file:
        rules_file.write(res)


@bp.route("/rules/rules.json")
@permissions.is_owner
def get_rules_as_json():  # type: ignore
    rules_json = dumps(get_rules(), indent=4, separators=(",", ": "))
    res = make_response(
        (
            rules_json,
            200,
        )
    )
    res.headers["Content-Disposition"] = "attachment"
    res.headers["Content-Type"] = "application/json"
    return res


@bp.route("/rules/summary")
@permissions.is_owner
def rule_summary():  # type: ignore
    return jsonify(summary())


@bp.route("/rules/<int:rule_index>", methods=["DELETE"])
@permissions.is_owner
def remove_rule(rule_index: int):  # type: ignore
    current_rules = get_rules()
    if rule_index < 0 or rule_index > (len(current_rules) - 1):
        return "", 400

    del current_rules[rule_index]
    _persist(current_rules)
    return "", 200


@bp.route("/rules", methods=["POST"])
@permissions.is_owner
def upload_rules():  # type: ignore
    try:
        maybe_rules = decode_rules_list(request.json)
    except Exception:
        return "", 400

    _persist(maybe_rules)
    return "", 200


@bp.route("/rules/validation", methods=["POST"])
@permissions.is_owner
def validate_rules():  # type: ignore
    try:
        maybe_rules = decode_rules_list(request.json)
        return {"ok": True, "data": len(maybe_rules)}, 200
    except Exception as exception:
        return {"ok": False, "data": str(exception)}, 200


@bp.route("/tags/missing/<int:medium_id>", methods=["GET", "OPTION"])
@permissions.get_medium
def get_missing_tags_for_post(medium_id: int):  # type: ignore
    return get_violations(medium_id)


@bp.route("/tags/missing/any", methods=["GET", "OPTION"])
@permissions.is_owner
def get_missing_tags_any():  # type: ignore
    violating_medium_id, notification = random_rule_violation()

    if not violating_medium_id and not notification:
        # No violations left
        return {}

    if notification:
        return notifications.simple_warning(notification)

    return {"id": violating_medium_id}
