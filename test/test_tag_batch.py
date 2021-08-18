import pytest


def test_tag_batch_update(client, asAdmin):
    res = client.post(
        "/tags/batch",
        json={
            "isAbsent": False,
            "tags": ["C", "tobecensored"],
            "mediumIds": [1],
        },
    )
    assert res.status_code == 200

    res = client.get("/medium/1")
    assert res.status_code == 200
    tags = res.get_json()["tags"]
    assert "C" in tags
    assert "tobecensored" in tags


def test_tag_batch_rating_change(client, asAdmin, nsfw):
    res = client.post(
        "/tags/batch",
        json={
            "isAbsent": False,
            "tags": ["rating:e"],
            "mediumIds": [1],
        },
    )
    assert res.status_code == 200

    res = client.get("/medium/1")
    assert res.status_code == 200
    assert res.get_json()["rating"] == "e"


@pytest.mark.parametrize("rating", ["ent", "squeal", "fridge"])
def test_tag_batch_rating_change_does_nothing_for_weird_rating(
    client, rating, asAdmin, nsfw
):
    res = client.post(
        "/tags/batch",
        json={
            "isAbsent": False,
            "tags": [f"rating:{rating}"],
            "mediumIds": [1],
        },
    )
    assert res.status_code == 200

    res = client.get("/medium/1")
    assert res.status_code == 200
    assert res.get_json()["rating"] == "s"


def test_tag_batch_rating_change_and_tag_add_at_once(client, asAdmin, nsfw):
    res = client.post(
        "/tags/batch",
        json={
            "isAbsent": False,
            "tags": ["rating:e", "C"],
            "mediumIds": [1],
        },
    )
    assert res.status_code == 200

    res = client.get("/medium/1")
    assert res.status_code == 200
    assert res.get_json()["rating"] == "e"
    assert "C" in res.get_json()["tags"]


def test_tag_batch_rating_change_with_multiple_ratings_invalid(
    client, asAdmin, nsfw
):
    res = client.post(
        "/tags/batch",
        json={
            "isAbsent": False,
            "tags": ["rating:e", "rating:q"],
            "mediumIds": [1],
        },
    )
    assert res.status_code == 200

    res = client.get("/medium/1")
    assert res.status_code == 200
    assert res.get_json()["rating"] == "s"


def test_tag_batch_absent_update(client, asAdmin):
    res = client.post(
        "/tags/batch",
        json={
            "isAbsent": True,
            "tags": ["tobecensoredtoo"],
            "mediumIds": [1, 2, 3],
        },
    )
    assert res.status_code == 200

    res = client.get("/medium/1")
    assert res.status_code == 200
    absent_tags = res.get_json()["absentTags"]
    assert "tobecensoredtoo" in absent_tags


def test_tag_cannot_add_tags_to_zero_media(client, asAdmin):
    res = client.post(
        "/tags/batch", json={"isAbsent": False, "tags": ["C"], "mediumIds": []}
    )
    assert res.status_code == 200


def test_double_adding_tag_to_medium_does_not_fail(client, asAdmin):
    res = client.get("/medium/1")
    assert res.status_code == 200
    assert "A" in res.get_json()["tags"]

    res = client.post(
        "/tags/batch", json={"isAbsent": False, "tags": ["A"], "mediumIds": [1]}
    )
    assert res.status_code == 200

    res = client.get("/medium/1")
    assert res.status_code == 200
    assert "A" in res.get_json()["tags"]


def test_tag_cannot_add_tags_to_missing_media(client, asAdmin):
    res = client.post(
        "/tags/batch",
        json={"isAbsent": False, "tags": ["C"], "mediumIds": [55343]},
    )
    assert res.status_code == 200


def test_tag_cannot_add_zero_tags_to_medium(client, asAdmin):
    res = client.post(
        "/tags/batch", json={"isAbsent": False, "tags": [], "mediumIds": [1]}
    )
    assert res.status_code == 200


def test_tag_cannot_add_only_new_tags_to_medium(client, asAdmin):
    res = client.post(
        "/tags/batch",
        json={"isAbsent": False, "tags": ["klonoa"], "mediumIds": [1]},
    )
    assert res.status_code == 200

    res = client.get("/medium/1")
    assert res.status_code == 200
    assert "klonoa" not in res.get_json()["tags"]


def test_tag_cannot_add_some_new_tags_to_medium(client, asAdmin):
    res = client.post(
        "/tags/batch",
        json={"isAbsent": False, "tags": ["klonoa", "C"], "mediumIds": [1]},
    )
    assert res.status_code == 200

    res = client.get("/medium/1")
    assert res.status_code == 200
    assert "klonoa" not in res.get_json()["tags"]
