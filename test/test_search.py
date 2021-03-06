from urllib import parse

import pytest


def _when_searching(c, query, page_number=1, page_size=10):
    q = parse.urlencode(
        {"q": query, "pageNumber": page_number, "pageSize": page_size}
    )
    print(q)
    return c.get(f"/search?{q}")


@pytest.mark.parametrize("pageNumber", [0, -1])
@pytest.mark.parametrize("pageSize", [0, -10])
def test_cannot_crash_search_with_weird_int_pagination(
    client, asUser, pageNumber, pageSize
):
    q = parse.urlencode(
        {"q": "test", "pageNumber": pageNumber, "pageSize": pageSize}
    )
    print(q)
    res = client.get(f"/search?{q}")
    assert res.status_code != 500


def test_cannot_crash_search_with_invalid_pagination(client, asUser):
    q = parse.urlencode({"q": "test", "pageNumber": "foo", "pageSize": "bar"})
    print(q)
    res = client.get(f"/search?{q}")
    assert res.status_code != 500


def test_returns_last_page_if_requested_page_number_too_high(client, asUser):
    res = _when_searching(client, "A", page_number=69, page_size=10)
    assert res.status_code == 200
    assert res.get_json()["pageNumber"] != 69
    assert res.get_json()["pageNumber"] == res.get_json()["pageCount"]


def test_search_succeeds_on_unparseable_term(client, asUser):
    res = _when_searching(client, "__foo__?")
    assert res.status_code == 200
    assert "items" in res.get_json()
    assert res.get_json()["items"] == []


def test_search_succeeds_on_whitespace_term(client, asUser):
    res = _when_searching(client, "   ")
    assert res.status_code == 200
    assert "items" in res.get_json()
    assert res.get_json()["items"] == []


def test_search_without_login(client):
    res = client.get("/search")
    assert res.status_code == 401


def test_no_results_has_valid_schema(client, asAdmin):
    res = _when_searching(client, "asdgjhkasgdgas")
    assert res.status_code == 200
    assert "items" in res.get_json()
    assert res.get_json()["items"] == []


def test_search_coverage_spam_exact_page_size(client, asAdmin, nsfw):
    total_medium_count = 16

    res = _when_searching(
        client,
        "-tagThatNoMediumHasSoAllOfThemAreFound",
        page_size=total_medium_count,
    )
    assert res.status_code == 200
    result = res.get_json()
    assert len(result["items"]) >= 1


def test_search_with_only_negative_terms_succeeds(client, asUser):
    res = _when_searching(client, "-C")
    assert res.status_code == 200
    result = res.get_json()
    assert len(result["items"]) >= 1


def test_valid_search_with_weird_params_succeeds(client, asUser):
    res = _when_searching(client, "+C", page_size=0, page_number=0)
    assert res.status_code == 200


def test_search_with_only_exact_terms_succeeds(client, asUser):
    res = _when_searching(client, "+C")
    assert res.status_code == 200
    result = res.get_json()
    assert len(result["items"]) >= 1


rule_terms = ["rule:0", "rule:9999"]


@pytest.mark.parametrize("q", rule_terms)
def test_search_with_rule_term_succeeds(client, asUser, q):
    res = _when_searching(client, q)
    result = res.get_json()
    print(result)
    assert res.status_code == 200


identical_group_search_terms = ["utags:1", "utags=1"]
identical_counting_search_terms = ["tags:2", "tags=2"]


@pytest.mark.parametrize("q", identical_group_search_terms)
def test_search_with_category_term_succeeds(client, asUser, q):
    res = _when_searching(client, q)
    assert res.status_code == 200
    result = res.get_json()
    print(result)
    assert len(result["items"]) == 2


@pytest.mark.parametrize("q", identical_counting_search_terms)
def test_search_colon_is_treated_the_same_as_equals(client, asUser, q):
    res = _when_searching(client, q)
    assert res.status_code == 200
    result = res.get_json()
    print(result)
    assert len(result["items"]) == 1


def test_search_with_combined_terms_succeeds(client, asUser):
    res = _when_searching(client, "c:tinkerbell tags>1")
    assert res.status_code == 200
    result = res.get_json()
    print(result)
    assert len(result["items"]) == 1


def test_search_with_alias_term_succeeds(client, asUser):
    res = _when_searching(client, "c:pete c:tinkerbell")
    assert res.status_code == 200
    result = res.get_json()
    print(result)
    assert len(result["items"]) == 1


def test_search_with_rating_term_succeeds(client, asAdmin, nsfw):
    res = _when_searching(client, "rating:s", page_size=20)
    assert res.status_code == 200
    result = res.get_json()
    print(result)
    assert len(result["items"]) == 14


def test_search_with_counting_term_succeeds(client, asAdmin, nsfw):
    res = _when_searching(client, "tags<2")
    assert res.status_code == 200
    result = res.get_json()
    print(result)
    assert len(result["items"]) == 10


def test_search_with_counting_term2_succeeds(client, asAdmin, nsfw):
    res = _when_searching(client, "tags<=1")
    assert res.status_code == 200
    result = res.get_json()
    print(result)
    assert len(result["items"]) == 10


def test_search_with_counting_term3_succeeds(client, asAdmin, nsfw):
    res = _when_searching(client, "tags>2")
    assert res.status_code == 200
    result = res.get_json()
    print(result)
    assert len(result["items"]) == 2


def test_search_with_counting_term4_succeeds(client, asAdmin, nsfw):
    res = _when_searching(client, "tags!=0")
    assert res.status_code == 200
    result = res.get_json()
    print(result)
    assert len(result["items"]) >= 3


@pytest.mark.parametrize(
    "filterAndExpectedCount",
    [
        ("width>400", 14),
        ("width<400", 0),
        ("height>200", 14),
        ("height<200", 0),
        ("filesize>5M", 0),
        ("filesize>2gb", 0),
        ("filesize=1234", 0),
        ("filesize<2m", 14),
        ("age>2w", 0),
        ("age>2y", 0),
        ("age>2m", 0),
        ("age>10d", 0),
        ("age<4d", 14),
        ("aspectratio>1", 14),
        ("aspectratio<1", 0),
    ],
)
def test_search_spammy_filter_tests(client, asUser, filterAndExpectedCount):
    _filter, expectedCount = filterAndExpectedCount
    res = _when_searching(client, _filter, page_size=20)
    assert res.status_code == 200
    result = res.get_json()
    print(result)

    assert len(result["items"]) == expectedCount
