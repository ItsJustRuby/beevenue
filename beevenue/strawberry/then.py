from typing import FrozenSet

from beevenue.types import TinyMediumDocument
from .common import TagsRulePart, Then


class HasAllTagsAbsentOrPresent(TagsRulePart, Then):
    """Validate if medium has been tagged enough.

    This allows checking if for a medium, all of the specified tags are
    either present or absent. This excludes the scenario of "unknown",
    which usually means "this medium needs more tagging".
    """

    def __init__(self, *tag_names: str) -> None:
        TagsRulePart.__init__(self)
        self.tag_names: FrozenSet[str] = frozenset(tag_names)

    def _filter_predicate(self, medium: TinyMediumDocument) -> bool:
        result: bool = self.tag_names <= (
            medium.searchable_tag_names | medium.absent_tag_names
        )
        return result

    @property
    def _tags_as_str(self) -> str:
        return ", ".join(self.tag_names)

    def pprint_then(self) -> str:
        return (
            f"should have all the tags in '{self._tags_as_str}' marked"
            " as either present or absent."
        )


class Fail(Then):
    """Fail every medium.

    This allows you to construct rules of the form "No media to which this Iff
    applies should exist at all."""

    def applies_to(self, _: TinyMediumDocument) -> bool:
        return False

    def pprint_then(self) -> str:
        return "should not exist."
