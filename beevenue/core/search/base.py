from abc import ABCMeta, abstractmethod
from re import Match
from typing import Any, List, NamedTuple, Optional, Set

from ...document_types import TinyMediumDocument


class ParsableMixin(metaclass=ABCMeta):
    """Base class for all terms which can be parsed from a re.Match."""

    # Note: In Python 3.11, this can finally be typed as "-> Self".
    @classmethod
    @abstractmethod
    def from_match(cls, match: Match) -> Any:
        """Construct this object from the match of its regex."""


class FilteringSearchTerm(ParsableMixin, metaclass=ABCMeta):
    """Abstract base class for all search terms."""

    @classmethod
    def from_match(cls, match: Match) -> "FilteringSearchTerm":
        return cls(**match.groupdict())  # type: ignore

    @abstractmethod
    def applies_to(self, medium: TinyMediumDocument) -> bool:
        """Does this FilteringSearchTerm apply to this medium?"""

    def __eq__(self, other: object) -> bool:
        """Support hash-based equality."""
        return self.__hash__() == other.__hash__()

    def __hash__(self) -> int:
        """Support hash-based equality based on __repr__.

        This allows us to easily parse multiple equal search term strings
        (["foo", "foo", "bar"]) into a set of Search Terms (set("foo", "bar")).
        """
        return hash(self.__repr__())


class SortingSearchTerm(ParsableMixin, metaclass=ABCMeta):
    """Search term which states that the output be sorted a certain way."""

    @abstractmethod
    def sort(self, media: Set[TinyMediumDocument]) -> List[TinyMediumDocument]:
        "Returns list of specified media, but now ordered by this term."


class SearchTerms(NamedTuple):
    """Holder for all filters and sorters that could be found in the query."""

    filtering: Set[FilteringSearchTerm]
    sorting: Optional[SortingSearchTerm]

    def __bool__(self) -> bool:
        return bool(self.sorting) or any(self.filtering)
