from urllib import parse

import pytest


def _when_searching(c, query):
    q = parse.urlencode({"q": query})
    print(q)
    return c.get(f"/search/batch?{q}")


def test_batch_search_fails_as_nonadmin(client, asUser):
    q = parse.urlencode({"q": "test"})
    print(q)
    res = _when_searching(client, q)
    assert res.status_code == 403


def test_batch_search_succeeds(client, asAdmin):
    res = _when_searching(client, "rating:s")
    assert res.status_code == 200
    assert "items" in res.get_json()


def test_batch_search_does_not_crash_on_whitespace_query(client, asAdmin):
    res = _when_searching(client, "   ")
    assert res.status_code == 200
    assert "items" in res.get_json()
