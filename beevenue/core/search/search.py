from logging import warning
from typing import List, Set

from beevenue.flask import g

from beevenue.flask import request

from ...document_types import MediumDocument, TinyMediumDocument

from .batch_search_results import BatchSearchResults
from .pagination import Pagination
from .parse import parse_search_terms
from .base import SearchTerms
from .filtering.simple import Negative, RatingSearchTerm
from .sorting.simple import IdSortingSearchTerm


def find_all() -> Pagination[MediumDocument]:
    return _run_paginated(parse_search_terms([]))


def run_unpaginated(search_term_list: List[str]) -> BatchSearchResults:
    search_terms = parse_search_terms(search_term_list)

    if not search_terms:
        return BatchSearchResults.empty()

    return _run_unpaginated(search_terms)


def run(search_term_list: List[str]) -> Pagination[MediumDocument]:
    search_terms = parse_search_terms(search_term_list)

    if not search_terms:
        return Pagination.empty()

    return _run_paginated(search_terms)


def _run_unpaginated(search_terms: SearchTerms) -> BatchSearchResults:
    medium_ids = _search(search_terms)
    return BatchSearchResults(list(g.fast.get_many(list(medium_ids))))


def _run_paginated(search_terms: SearchTerms) -> Pagination[MediumDocument]:
    sorted_medium_ids = _search(search_terms)

    if not sorted_medium_ids:
        return Pagination.empty()

    pagination = _paginate(sorted_medium_ids)
    return pagination  # type: ignore


def _censor(search_terms: SearchTerms) -> SearchTerms:
    context = request.beevenue_context

    if context.is_sfw:
        search_terms.filtering.add(RatingSearchTerm("s"))
    if context.user_role != "admin":
        search_terms.filtering.add(Negative(RatingSearchTerm("e")))
        search_terms.filtering.add(Negative(RatingSearchTerm("u")))

    return search_terms


def _search(search_terms: SearchTerms) -> List[int]:
    search_terms = _censor(search_terms)

    all_media = g.fast.get_all_tiny()
    search_results: Set[TinyMediumDocument] = set()

    for medium in all_media:
        for search_term in search_terms.filtering:
            if not search_term.applies_to(medium):
                break
        else:
            search_results.add(medium)

    sorter = search_terms.sorting or IdSortingSearchTerm(is_descending=True)
    sorted_results = sorter.sort(search_results)
    return [m.medium_id for m in sorted_results]


def _paginate(ids: List[int]) -> Pagination[int]:
    page_number_arg: str = request.args.get(  # type: ignore
        "pageNumber", type=str
    )
    page_size_arg: str = request.args.get("pageSize", type=str)  # type: ignore

    page_number = int(page_number_arg)
    page_size = int(page_size_arg)

    page_number = max(page_number, 1)
    page_size = max(min(page_size, 100), 10)

    page_count = len(ids) // page_size
    if (len(ids) % page_size) != 0:
        page_count += 1

    # Be nice. If the client skips too far ahead,
    # they get the last page instead.
    page_number = min(page_number, page_count)
    skip = (page_number - 1) * page_size
    paginated_ids = ids[skip : skip + page_size]

    return Pagination(
        items=g.fast.get_many(paginated_ids),
        page_count=page_count,
        page_number=page_number,
        page_size=page_size,
    )
