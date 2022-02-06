import re
from re import Pattern
from typing import List, Optional, Tuple, Type


from ..base import SortingSearchTerm
from .simple import (
    AgeSortingSearchTerm,
    DimensionSortingSearchTerm,
    FilesizeSortingSearchTerm,
    IdSortingSearchTerm,
    RotationSortingSearchTerm,
)


def _sorter(regex_str: str) -> Pattern:
    return re.compile(
        r"(sort|order):" + regex_str + r"(_(?P<direction>desc|asc))?"
    )


DIMENSION_SORT_REGEX = _sorter(r"(?P<dimension>width|height)")
ROTATION_SORT_REGEX = _sorter(r"(?P<rotation>portrait|landscape)")
FILESIZE_SORT_REGEX = _sorter(r"filesize")
AGE_SORT_REGEX = _sorter(r"age")
ID_SORT_REGEX = _sorter(r"id")

SORTERS: List[Tuple[Pattern, Type[SortingSearchTerm]]] = [
    (DIMENSION_SORT_REGEX, DimensionSortingSearchTerm),
    (ROTATION_SORT_REGEX, RotationSortingSearchTerm),
    (FILESIZE_SORT_REGEX, FilesizeSortingSearchTerm),
    (AGE_SORT_REGEX, AgeSortingSearchTerm),
    (ID_SORT_REGEX, IdSortingSearchTerm),
]


def try_parse_sorter(term: str) -> Optional[SortingSearchTerm]:
    match = None
    matching_class = None
    for (regex, klass) in SORTERS:
        match = regex.match(term)
        matching_class = klass
        if match:
            break

    # (This double check is a bit superfluous, but calms the type checker)
    if not match or not matching_class:
        return None

    return matching_class.from_match(match)  # type: ignore
