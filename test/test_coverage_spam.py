# These tests are just here to raise coverage the last few percents.
import os
from pathlib import Path

import pytest

from beevenue.core import ffmpeg
from beevenue.core.search import complex, simple
from beevenue.core.search.pagination import Pagination
from beevenue.fast.nope import NotACache
from beevenue.models import Tag
from beevenue.permissions import _CanSeeMediumWithRatingNeed
from beevenue.documents import IndexedMedium, TinyIndexedMedium


def _assert_equally_hashed(x1, x2):
    assert not x1 == object()
    assert not x2 == object()
    assert hash(x1) == hash(x2)
    assert x1 == x2
    assert len(set([x1, x2])) == 1


def test_permission_need_internals():
    need = _CanSeeMediumWithRatingNeed("q")
    assert not (need == "something else")

    assert len(need.__repr__()) > 0


def test_indexed_medium_internals():
    medium = IndexedMedium(
        1,
        "someHash",
        "mime",
        "q",
        bytes(),
        frozenset(),
        frozenset(),
        frozenset(),
    )

    medium_with_same_id = IndexedMedium(
        1,
        "someOtherHash",
        "mime",
        "q",
        bytes(),
        frozenset(),
        frozenset(),
        frozenset(),
    )

    assert len(medium.__str__()) > 0
    assert len(medium.__repr__()) > 0
    _assert_equally_hashed(medium, medium_with_same_id)


def test_tiny_indexed_medium_internals():
    medium = TinyIndexedMedium(
        1,
        "hash1",
        "q",
        frozenset(),
        frozenset(),
        frozenset(),
    )

    medium_with_same_id = TinyIndexedMedium(
        1,
        "hash2",
        "e",
        frozenset(),
        frozenset(),
        frozenset(),
    )

    assert len(medium.__str__()) > 0
    assert len(medium.__repr__()) > 0
    _assert_equally_hashed(medium, medium_with_same_id)


def test_tag_cannot_be_created_empty(client):
    assert Tag.create("  ") is None


def test_thumbnailing_weird_mime_type_throws():
    with pytest.raises(Exception):
        ffmpeg.thumbnails("", Path("./"), "application/weird")


def test_counting_search_term_internals():
    term = complex.CountingSearchTerm("??", 3)  # invalid operator
    with pytest.raises(Exception):
        term.applies_to(None)


def test_category_search_term_internals():
    term = complex.CategorySearchTerm("c", "??", 3)  # invalid operator

    class FakeMedium:
        def __getattribute__(self, name):
            if name == "tag_names":
                return self
            return set()

    with pytest.raises(Exception):
        term.applies_to(FakeMedium())


def test_negative_search_term_internals():
    with pytest.raises(NotImplementedError):
        simple.Negative.from_match(None)


def test_pagination_internals():
    pagination = Pagination([], 1, 1, 10)
    assert len(pagination.__repr__()) > 0


def test_notacache_internals():
    not_a_cache = NotACache()
    assert not_a_cache.delete([]) == 0
