from typing import List, Optional, Set


from .base import FilteringSearchTerm, SearchTerms, SortingSearchTerm
from .filtering.parse import try_parse_filter
from .sorting.parse import try_parse_sorter


def parse_search_terms(search_term_list: List[str]) -> SearchTerms:
    """Parse list of search term strings into Set of valid SearchTerms."""

    filtering: Set[FilteringSearchTerm] = set()
    sorting: Optional[SortingSearchTerm] = None

    for term in search_term_list:
        maybe_sorting = try_parse_sorter(term)
        if maybe_sorting:
            if not sorting:
                sorting = maybe_sorting
            continue

        maybe_filter = try_parse_filter(term)
        if maybe_filter:
            filtering.add(maybe_filter)
            continue

    return SearchTerms(filtering, sorting)
