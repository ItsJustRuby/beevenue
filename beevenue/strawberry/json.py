import json
from typing import Any, List, Sequence, Union

from .common import (
    HasAnyTagsIn,
    HasAnyTagsLike,
    HasRating,
    IffAndThen,
    RulePart,
)
from .iff import All, Iff
from .rule import Rule
from .then import Fail, Then, HasAllTagsAbsentOrPresent
from . import types


def _decode_common(
    obj: types.RulePartJson,
) -> IffAndThen:
    if obj["type"] == "hasRating":
        return HasRating(obj.get("data", None))  # type: ignore

    if obj["type"] == "hasAnyTagsIn":
        return HasAnyTagsIn(*obj["data"])

    if obj["type"] == "hasAnyTagsLike":
        return HasAnyTagsLike(*obj["data"])

    raise Exception(f'Unknown rule part type "{obj["type"]}"')


def _decode_iffs(obj: types.PartsJson) -> List[Iff]:
    if not isinstance(obj, list):
        obj = [obj]
    return [_decode_iff(i) for i in obj]


def _decode_iff(obj: types.RulePartJson) -> Iff:
    if obj["type"] == "all":
        return All()
    return _decode_common(obj)


def _decode_then(obj: types.RulePartJson) -> Then:
    if obj["type"] == "fail":
        return Fail()
    if obj["type"] == "hasAllAbsentOrPresent":
        return HasAllTagsAbsentOrPresent(*obj["data"])
    return _decode_common(obj)


def _decode_thens(thens_obj: types.PartsJson) -> List[Then]:
    if not isinstance(thens_obj, list):
        thens_obj = [thens_obj]
    return [_decode_then(t) for t in thens_obj]


def _decode_rule(obj: types.RuleJson) -> Rule:
    iffs = _decode_iffs(obj["if"])
    thens = _decode_thens(obj["then"])

    return Rule(iffs, thens)


def decode_rules_json(json_text: str) -> List[Rule]:
    """Decode given JSON text into list of Rules."""
    return decode_rules_list(json.loads(json_text))


def decode_rules_list(json_list: List[types.RuleJson]) -> List[Rule]:
    """Decode given list of dictionaries into list of Rules."""
    return [_decode_rule(rule) for rule in json_list]


class RulePartEncoder(json.JSONEncoder):
    """JSON Encoder for `RulePart`."""

    def default(  # pylint: disable=too-many-return-statements
        self, o: RulePart
    ) -> types.RulePartJson:
        if isinstance(o, All):
            all_json: types.AllJson = {"type": "all"}
            return all_json
        if isinstance(o, Fail):
            fail: types.FailJson = {"type": "fail"}
            return fail
        if isinstance(o, HasRating):
            if o.rating:
                specific_rating_json: types.HasSpecificRatingJson = {
                    "type": "hasRating",
                    "data": o.rating,
                }
                return specific_rating_json

            any_rating_json: types.HasAnyRatingJson = {"type": "hasRating"}
            return any_rating_json
        if isinstance(o, HasAllTagsAbsentOrPresent):
            json_obj: types.HasAllTagsAbsentOrPresentJson = {
                "type": "hasAllAbsentOrPresent",
                "data": list(o.tag_names),
            }
            return json_obj
        if isinstance(o, HasAnyTagsIn):
            has_any_tags_in_json: types.HasAnyTagsInJson = {
                "type": "hasAnyTagsIn",
                "data": list(o.tag_names),
            }
            return has_any_tags_in_json
        if isinstance(o, HasAnyTagsLike):
            has_any_tags_like_json: types.HasAnyTagsLikeJson = {
                "type": "hasAnyTagsLike",
                "data": list(o.regexes),
            }
            return has_any_tags_like_json
        raise Exception(f"Cannot encode rule part with type {type(o)}")


class RuleEncoder(json.JSONEncoder):
    """JSON Encoder for `Rule`."""

    def _list_or_singleton(
        self, enc: RulePartEncoder, things: Sequence[RulePart]
    ) -> Union[types.RulePartJson, List[types.RulePartJson]]:
        if len(things) == 1:
            return enc.default(things[0])
        return [enc.default(t) for t in things]

    def default(self, o: Any) -> types.RuleJson:
        if isinstance(o, Rule):
            enc = RulePartEncoder()
            return {
                "if": self._list_or_singleton(enc, o.iffs),
                "then": self._list_or_singleton(enc, o.thens),
            }
        raise Exception(f"Cannot encode rule with type {type(o)}")
