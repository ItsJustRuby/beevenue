import re
from re import Pattern
from typing import List, Optional, Tuple, Type

from ...tags.tags import VALID_TAG_REGEX_INNER
from ..base import FilteringSearchTerm
from . import simple, complex as complex_terms

COMPARISON = r"(?P<operator>(:|=|<|>|<=|>=|!=))"
DECIMAL_COMPARISON = COMPARISON + r"(?P<number>[0-9]+(\.[0-9]+)?)"
INT_COMPARISON = COMPARISON + r"(?P<number>[0-9]+)"

COUNTING_TERM_REGEX = re.compile(r"tags" + INT_COMPARISON)
CATEGORY_TERM_REGEX = re.compile(r"(?P<category>[a-z]+)tags" + INT_COMPARISON)
RATING_TERM_REGEX = re.compile(r"rating:(u|s|e|q)")
RULE_TERM_REGEX = re.compile(r"rule:(?P<number>[0-9]+)")
EXACT_TERM_REGEX = re.compile(r"\+(" + VALID_TAG_REGEX_INNER + ")")
POSITIVE_TERM_REGEX = re.compile(VALID_TAG_REGEX_INNER)

AGE = r"(?P<period>w|weeks?|d|days?|m|months?|y|years?)"
FILESIZE = r"(?P<unit>[kKmMgG][bB]?)"

AGE_TERM_REGEX = re.compile(r"age" + INT_COMPARISON + AGE)
FILESIZE_TERM_REGEX = re.compile(r"filesize" + INT_COMPARISON + FILESIZE)
DIMENSION_TERM_REGEX = re.compile(
    r"(?P<dimension>width|height)" + INT_COMPARISON
)
ASPECT_RATIO_TERM_REGEX = re.compile(r"aspectratio" + DECIMAL_COMPARISON)

FILTERS: List[Tuple[Pattern, Type[FilteringSearchTerm]]] = [
    (COUNTING_TERM_REGEX, complex_terms.CountingSearchTerm),
    (CATEGORY_TERM_REGEX, complex_terms.CategorySearchTerm),
    (RATING_TERM_REGEX, simple.RatingSearchTerm),
    (AGE_TERM_REGEX, complex_terms.AgeSearchTerm),
    (FILESIZE_TERM_REGEX, complex_terms.FilesizeSearchTerm),
    (DIMENSION_TERM_REGEX, complex_terms.DimensionSearchTerm),
    (ASPECT_RATIO_TERM_REGEX, complex_terms.AspectRatioSearchTerm),
    (RULE_TERM_REGEX, simple.RuleSearchTerm),
    (EXACT_TERM_REGEX, simple.ExactSearchTerm),
    (POSITIVE_TERM_REGEX, simple.PositiveSearchTerm),
]


def try_parse_filter(term: str) -> Optional[FilteringSearchTerm]:
    """Try and parse the given string into a valid FilteringSearchTerm."""
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
    return term_obj  # type: ignore
