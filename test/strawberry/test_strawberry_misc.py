import pytest


def test_get_missing_any(client, asAdmin):
    r = client.get("/tags/missing/any")
    assert r.status_code == 200


def test_get_missing_any_nsfw(client, asAdmin, nsfw):
    r = client.get("/tags/missing/any")
    assert r.status_code == 200


def test_get_missing_any_nsfw_trivial(client, asAdmin, nsfw, withTrivialRules):
    r = client.get("/tags/missing/any")
    assert r.status_code == 200


@pytest.mark.parametrize("id", [1, 2, 3, 4, 5, 14])
def test_get_missing_specific(client, asAdmin, id):
    r = client.get(f"/tags/missing/{id}")
    assert r.status_code == 200


@pytest.mark.parametrize("id", [1, 2, 3, 4, 5])
def test_trivial_rules_always_succeed(client, asAdmin, withTrivialRules, id):
    r = client.get(f"/tags/missing/{id}")
    assert r.status_code == 200
    assert r.get_json()["violations"] == []


def test_trivial_rules_return_zero_violations(
    client, asAdmin, withTrivialRules
):
    r = client.get("/tags/missing/any")
    assert r.status_code == 200
    assert r.get_json() == {}


def test_high_rating_rules_return_non_safe_violations(
    client, asAdmin, withSimpleRules
):
    r = client.get("/tags/missing/any")
    assert r.status_code == 200
