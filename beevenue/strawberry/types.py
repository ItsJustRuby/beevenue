# pylint: disable=missing-class-docstring
from typing import List, Literal, Optional, TypedDict, Union


class AllJson(TypedDict):
    type: Literal["all"]


class FailJson(TypedDict):
    type: Literal["fail"]


class HasAllTagsAbsentOrPresentJson(TypedDict):
    type: Literal["hasAllAbsentOrPresent"]
    data: List[str]


class HasAnyRatingJson(TypedDict):
    type: Literal["hasRating"]


class HasSpecificRatingJson(TypedDict):
    type: Literal["hasRating"]
    data: Optional[str]


class HasAnyTagsInJson(TypedDict):
    type: Literal["hasAnyTagsIn"]
    data: List[str]


class HasAnyTagsLikeJson(TypedDict):
    type: Literal["hasAnyTagsLike"]
    data: List[str]


RulePartJson = Union[
    AllJson,
    FailJson,
    HasAnyRatingJson,
    HasSpecificRatingJson,
    HasAnyTagsInJson,
    HasAllTagsAbsentOrPresentJson,
    HasAnyTagsLikeJson,
]

PartsJson = Union[RulePartJson, List[RulePartJson]]

RuleJson = TypedDict("RuleJson", {"if": PartsJson, "then": PartsJson})
