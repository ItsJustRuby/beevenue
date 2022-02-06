from abc import ABCMeta, abstractmethod
from re import Match
from typing import Any, Callable, List, Literal, Set

from beevenue.document_types import TinyMediumDocument
from ..base import SortingSearchTerm

SortingLambda = Callable[[TinyMediumDocument], Any]


class ReversibleSortingSearchTerm(SortingSearchTerm, metaclass=ABCMeta):
    """Base class for all sorting terms which support both desc and asc."""

    def __init__(self, is_descending: bool, *_: Any, **__: Any) -> None:
        self.is_descending = is_descending

    @classmethod
    def from_match(cls, match: Match) -> "ReversibleSortingSearchTerm":
        is_descending = True

        is_descending_lookup = {"asc": False, "desc": True}

        groups = match.groupdict()
        if groups["direction"]:
            is_descending = is_descending_lookup[groups["direction"]]
        groups.pop("direction")

        return cls(is_descending, **groups)  # type: ignore

    def sort(self, media: Set[TinyMediumDocument]) -> List[TinyMediumDocument]:
        return sorted(media, key=self.sorter, reverse=self.is_descending)

    @property
    @abstractmethod
    def sorter(self) -> SortingLambda:
        """Specifies which part of TinyMediumDocument to sort by."""


class IdSortingSearchTerm(ReversibleSortingSearchTerm):
    """Sorts media by their ID numbers."""

    @property
    def sorter(self) -> SortingLambda:
        def _sorter(medium: TinyMediumDocument) -> int:
            return medium.medium_id

        return _sorter


class FilesizeSortingSearchTerm(ReversibleSortingSearchTerm):
    """Sorts media by their filesize."""

    @property
    def sorter(self) -> SortingLambda:
        def _sorter(medium: TinyMediumDocument) -> Any:
            return medium.filesize

        return _sorter


class AgeSortingSearchTerm(ReversibleSortingSearchTerm):
    """Sorts media by their age (oldest first)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.is_descending = not self.is_descending

    @property
    def sorter(self) -> SortingLambda:
        def _sorter(medium: TinyMediumDocument) -> Any:
            return medium.medium_id

        return _sorter


class RotationSortingSearchTerm(ReversibleSortingSearchTerm):
    """Sorts media by their long axis."""

    rotation: Literal["portrait", "landscape"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.rotation = kwargs["rotation"]

    @property
    def sorter(self) -> SortingLambda:
        def _sorter(medium: TinyMediumDocument) -> Any:
            if self.rotation == "portrait":
                return medium.height / medium.width
            return medium.width / medium.height

        return _sorter


class DimensionSortingSearchTerm(ReversibleSortingSearchTerm):
    """Sorts media by their width or height."""

    dimension: Literal["width", "height"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.dimension = kwargs["dimension"]

    @property
    def sorter(self) -> SortingLambda:
        def _sorter(medium: TinyMediumDocument) -> Any:
            if self.dimension == "width":
                return medium.width
            return medium.height

        return _sorter
