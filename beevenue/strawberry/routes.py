import random
from typing import Dict, List, Optional, Tuple

from flask import Blueprint, current_app, g, jsonify
from flask.json import dumps
from sentry_sdk import start_span

from beevenue.flask import request
from beevenue.types import TinyMediumDocument

from .. import permissions
from .json import decode_rules_json, decode_rules_list
from .rule import Rule

bp = Blueprint("strawberry", __name__)


def _persist(rules_list: List[Rule]) -> None:
    res = dumps(rules_list, indent=4, separators=(",", ": "))
    rules_file_path = current_app.config["BEEVENUE_RULES_FILE"]
    with open(rules_file_path, "w") as rules_file:
        rules_file.write(res)


def _pretty_print(rule_breaks: Dict[int, List[Rule]]) -> Dict[int, List[str]]:
    json_helper = {}
    for medium_id, broken_rules in rule_breaks.items():
        json_helper[medium_id] = [r.pprint() for r in broken_rules]

    return json_helper


def _current_rules() -> List[Rule]:
    with start_span(op="http", description="Loading current rules"):
        rules_file_path = current_app.config["BEEVENUE_RULES_FILE"]
        with open(rules_file_path, "r") as rules_file:
            rules_file_json = rules_file.read()

        rules_file_json = rules_file_json or "[]"

        return decode_rules_json(rules_file_json)


def _random_rule_violation() -> Optional[Tuple[int, Rule]]:
    all_media = g.fast.get_all_tiny()

    sorted_ratings = ["s", "q", "e", "u"]
    semirandom_sorting_index = {
        m.medium_id: sorted_ratings.index(m.rating) + random.uniform(-0.4, 0.4)
        for m in all_media
    }

    def shuffler(medium: TinyMediumDocument) -> float:
        return semirandom_sorting_index[medium.medium_id]

    all_media.sort(key=shuffler)

    rules = _current_rules()
    random.shuffle(rules)

    for medium in all_media:
        for rule in rules:
            if rule.is_violated_by(medium):
                return (medium.medium_id, rule)

    return None


@bp.route("/rules")
@bp.route("/rules/rules.json")
@permissions.is_owner
def get_rules_as_json():  # type: ignore
    return jsonify(_current_rules()), 200


@bp.route("/rules/<int:rule_index>", methods=["DELETE"])
@permissions.is_owner
def remove_rule(rule_index: int):  # type: ignore
    current_rules = _current_rules()
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
    medium = g.fast.get_tiny(medium_id)
    broken_rules = [r for r in _current_rules() if r.is_violated_by(medium)]
    return _pretty_print({medium_id: broken_rules})


@bp.route("/tags/missing/any", methods=["GET", "OPTION"])
@permissions.is_owner
def get_missing_tags_any():  # type: ignore
    maybe_violation = _random_rule_violation()
    if not maybe_violation:
        return _pretty_print({})

    medium_id, rule = maybe_violation
    return _pretty_print({medium_id: [rule]})
