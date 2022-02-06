from beevenue.core.search.base import FilteringSearchTerm
from beevenue.core.search.filtering.simple import PositiveSearchTerm


def test_terms_are_compared_by_value():
    def term():
        return PositiveSearchTerm("foo")

    x = term()
    y = term()

    are_equal = x == y
    assert are_equal
    assert hash(x) == hash(y)
