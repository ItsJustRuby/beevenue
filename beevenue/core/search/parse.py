import re
from re import Pattern
from typing import List, Optional, Set, Tuple, Type

from ..tags.tags import VALID_TAG_REGEX_INNER
from .base import SearchTerm
from . import simple, complex as complex_terms

COMPARISON = r"(?P<operator>(:|=|<|>|<=|>=|!=))(?P<number>[0-9]+)"

COUNTING_TERM_REGEX = re.compile(r"tags" + COMPARISON)
CATEGORY_TERM_REGEX = re.compile(r"(?P<category>[a-z]+)tags" + COMPARISON)
RATING_TERM_REGEX = re.compile(r"rating:(u|s|e|q)")
RULE_TERM_REGEX = re.compile(r"rule:(?P<number>[0-9]+)")
EXACT_TERM_REGEX = re.compile(r"\+(" + VALID_TAG_REGEX_INNER + ")")
POSITIVE_TERM_REGEX = re.compile(VALID_TAG_REGEX_INNER)


FILTERS: List[Tuple[Pattern, Type[SearchTerm]]] = [
    (COUNTING_TERM_REGEX, complex_terms.CountingSearchTerm),
    (CATEGORY_TERM_REGEX, complex_terms.CategorySearchTerm),
    (RATING_TERM_REGEX, simple.RatingSearchTerm),
    (RULE_TERM_REGEX, simple.RuleSearchTerm),
    (EXACT_TERM_REGEX, simple.ExactSearchTerm),
    (POSITIVE_TERM_REGEX, simple.PositiveSearchTerm),
]


def _try_parse(term: str) -> Optional[SearchTerm]:
    """Try and parse the given search term string into a valid SearchTerm."""
    if len(term) < 1:
        return None

    do_negate = False
    if term[0] == "-":
        do_negate = True
        term = term[1:]

    match = None
    matching_class = None
    for (regex, klass) in FILTERS:
        match = regex.match(term)
        matching_class = klass
        if match:
            break

    # (This double check is a bit superfluous, but calms the type checker)
    if not match or not matching_class:
        return None

    term_obj = matching_class.from_match(match)
    if do_negate:
        term_obj = simple.Negative(term_obj)
    return term_obj


def parse_search_terms(search_term_list: List[str]) -> Set[SearchTerm]:
    """Parse list of search term strings into Set of valid SearchTerms."""

    result = set()

    for term in search_term_list:
        maybe_term = _try_parse(term)
        if maybe_term:
            result.add(maybe_term)

    return result
