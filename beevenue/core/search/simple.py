from abc import ABC
from beevenue.strawberry.rule import Rule
from beevenue.strawberry.get import get_rules
from re import Match
from typing import NoReturn, Optional

from ...document_types import TinyMediumDocument
from .base import SearchTerm


class BasicSearchTerm(ABC, SearchTerm):
    """Abstract helper class that saves a single term."""

    def __init__(self, term: str):
        self.term = term


class PositiveSearchTerm(BasicSearchTerm):
    """Search term like "foo" which filters by searchable tag name.

    Searchable tag names include implied tag names and tag name aliases."""

    def __repr__(self) -> str:
        return f"{self.term}"

    def applies_to(self, medium: TinyMediumDocument) -> bool:
        return self.term in medium.searchable_tag_names

    @classmethod
    def from_match(cls, match: Match) -> "PositiveSearchTerm":
        return PositiveSearchTerm(match.group(0))


class ExactSearchTerm(BasicSearchTerm):
    """Search term like "+foo" which filters by exact tag name.

    This sets it apart from "foo", because it does *not* search implications
    and aliases. This allows searches like "bluegreen +blue" to find files
    which are tagged as both blue and bluegreen (if bluegreen implies blue).
    """

    def __repr__(self) -> str:
        return f"+{self.term}"

    def applies_to(self, medium: TinyMediumDocument) -> bool:
        return self.term in medium.innate_tag_names

    @classmethod
    def from_match(cls, match: Match) -> "ExactSearchTerm":
        return ExactSearchTerm(match.group(1))


class RatingSearchTerm(SearchTerm):
    """Search term like "rating:s"."""

    def __init__(self, rating: str):
        self.rating = rating

    @classmethod
    def from_match(cls, match: Match) -> "RatingSearchTerm":
        return RatingSearchTerm(match.group(1))

    def __repr__(self) -> str:
        return f"rating:{self.rating}"

    def applies_to(self, medium: TinyMediumDocument) -> bool:
        return medium.rating == self.rating


class RuleSearchTerm(SearchTerm):
    """Search term like "rule:0". Returns violating media."""

    def __init__(self, rule_index: int):
        self.rule_index = rule_index
        self.rule: Optional[Rule] = None

        all_rules = get_rules()

        if rule_index < len(all_rules):
            self.rule = all_rules[rule_index]

    @classmethod
    def from_match(cls, match: Match) -> "RuleSearchTerm":
        rule_index = int(match.group(1))
        return RuleSearchTerm(rule_index)

    def __repr__(self) -> str:
        return f"rule:{self.rule_index}"

    def applies_to(self, medium: TinyMediumDocument) -> bool:
        if self.rule is None:
            return False
        return self.rule.is_violated_by(medium)


class Negative(SearchTerm):
    """Meta search term which negates the wrapped inner SearchTerm."""

    def __init__(self, inner_term: SearchTerm):
        self.inner_term = inner_term

    @classmethod
    def from_match(cls, match: Match) -> NoReturn:
        raise NotImplementedError("Unsupported for this SearchTerm")

    def __repr__(self) -> str:
        return f"!{self.inner_term.__repr__()}"

    def applies_to(self, medium: TinyMediumDocument) -> bool:
        return not self.inner_term.applies_to(medium)
