from abc import ABC, abstractmethod
from beevenue.types import TinyMediumDocument
import re
from typing import FrozenSet, Generator, Optional

from flask import g

from . import violations
from .violations import Violation


class RulePart(ABC):
    """Abstract base class for all rule parts (both iffs and thens)."""


class Iff(RulePart):
    """Abstract base class for all Iff rule parts."""

    @abstractmethod
    def applies_to(self, medium: TinyMediumDocument) -> bool:
        """Does this part of the rule apply to this medium?"""

    @abstractmethod
    def pprint_if(self) -> str:
        """Formats this part as an 'if' clause."""


class Then(RulePart):
    """Abstract base class for all Then rule parts."""

    @abstractmethod
    def violations_for(
        self, medium: TinyMediumDocument
    ) -> Generator[Violation, None, None]:
        """Yield all ways in which the medium violates this."""

    @abstractmethod
    def pprint_then(self) -> str:
        """Formats this part as an 'then' clause."""


class TagsRulePart(RulePart):
    """Abstract base class for rule parts that checks for presence of tags."""

    def __init__(self) -> None:
        self.tag_names: Optional[FrozenSet[str]] = None

    def _load_tag_names(self) -> None:
        """Preload the tag names (e.g. based on regexes) into self.tag_names."""

    @property
    @abstractmethod
    def _tags_as_str(self) -> str:
        """Pretty-printed version of self.tag_names for user display."""

    def _ensure_tag_names_loaded(self) -> None:
        if self.tag_names is not None:
            return

        self._load_tag_names()


class IffAndThen(Iff, Then):
    """Only for type hinting"""


class HasAnyTagsIffAndThen(TagsRulePart, IffAndThen):
    """Helper class for all rule parts that refer to lists of tags."""

    def __init__(self) -> None:
        TagsRulePart.__init__(self)

    def applies_to(self, medium: TinyMediumDocument) -> bool:
        self._ensure_tag_names_loaded()
        return bool((self.tag_names or frozenset()) & medium.innate_tag_names)

    def violations_for(
        self, medium: TinyMediumDocument
    ) -> Generator[Violation, None, None]:
        self._ensure_tag_names_loaded()
        if not self.tag_names:
            return

        if len(self.tag_names & medium.searchable_tag_names) > 0:
            return

        if len(self.tag_names) > 5:
            yield violations.Nontrivial()
        else:
            yield violations.ShouldHaveTagIn(self.tag_names)


class HasAnyTagsLike(HasAnyTagsIffAndThen):
    """Rule part that checks if medium has any tags matching some regexes."""

    def __init__(self, *regexes: str) -> None:
        HasAnyTagsIffAndThen.__init__(self)
        if not regexes:
            raise Exception("You must configure at least one LIKE expression")

        self.regexes = regexes

    def _load_tag_names(self) -> None:
        tag_names = set()

        all_tag_names = set(g.fast.get_all_searchable_tag_names())

        for regex in self.regexes:
            compiled_regex = re.compile(f"^{regex}$")
            for tag_name in all_tag_names:
                if compiled_regex.match(tag_name):
                    tag_names.add(tag_name)

        self.tag_names = frozenset(tag_names)

    @property
    def _tags_as_str(self) -> str:
        return ", ".join(self.regexes)

    def pprint_if(self) -> str:
        return f"Any medium with a tag like '{self._tags_as_str}'"

    def pprint_then(self) -> str:
        return f"should have a tag like '{self._tags_as_str}'."


class HasAnyTagsIn(HasAnyTagsIffAndThen):
    """Rule part that checks if a medium has any tags in a specified set."""

    def __init__(self, *tag_names: str) -> None:
        HasAnyTagsIffAndThen.__init__(self)
        if not tag_names:
            raise Exception("You must configure at least one name")
        self.tag_names: FrozenSet[str] = frozenset(tag_names)

    @property
    def _tags_as_str(self) -> str:
        return ", ".join(self.tag_names)

    def pprint_if(self) -> str:
        return f"Any medium with a tag in '{self._tags_as_str}'"

    def pprint_then(self) -> str:
        return f"should have a tag in '{self._tags_as_str}'."


class HasRating(Iff, Then):
    """Flexible rule part that checks for the presence of a (specific) rating.

    I.e. HasRating() checks that a medium has any rating other than "unrated",
    but HasRating("s") checks that a medium has the rating "s".
    """

    def __init__(self, rating: Optional[str] = None):
        self.rating: Optional[str] = rating

    def applies_to(self, medium: TinyMediumDocument) -> bool:
        if self.rating:
            has_correct_rating: bool = medium.rating == self.rating
            return has_correct_rating

        has_any_rating: bool = medium.rating != "u"
        return has_any_rating

    def violations_for(
        self, medium: TinyMediumDocument
    ) -> Generator[Violation, None, None]:
        if (
            self.rating and medium.rating != self.rating
        ) or medium.rating == "u":
            yield violations.Nontrivial()

    @property
    def _rating_str(self) -> str:
        if self.rating:
            return f"a rating of '{self.rating}'"
        return "a known rating"

    def pprint_then(self) -> str:
        return f"should have {self._rating_str}."

    def pprint_if(self) -> str:
        return f"Any medium with {self._rating_str}"
