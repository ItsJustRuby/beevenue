def test_cannot_update_medium_without_logging_in(client):
    res = client.patch("/medium/3/metadata")
    assert res.status_code == 401


def test_cannot_update_medium_as_user(client, asUser):
    res = client.patch("/medium/3/metadata")
    assert res.status_code == 403


def test_can_update_medium_as_admin(client, asAdmin):
    res = client.patch(
        "/medium/3/metadata",
        json={
            "rating": "q",
            "tags": [" some_new_tag   ", "A", "mango"],
            "absentTags": [],
        },
    )
    assert res.status_code == 200


def test_can_update_really_tricky_medium(client, asAdmin):
    old_medium = client.get("/medium/15").get_json()
    print(old_medium)
    old_medium["tags"] = []
    print(old_medium)

    res = client.patch("/medium/15/metadata", json=old_medium)
    assert res.status_code == 200
    print(res.get_json())


def test_cant_update_medium_to_unknown_rating(client, asAdmin, nsfw):
    res = client.get("/medium/3")
    current_rating = res.get_json()["rating"]

    res = client.patch(
        "/medium/3/metadata",
        json={"rating": "u", "tags": ["A"], "absentTags": []},
    )
    assert res.status_code == 200

    res = client.get("/medium/3")
    assert res.status_code == 200
    json_result = res.get_json()
    assert json_result["rating"] == current_rating


def test_cant_update_medium_to_same_rating(client, asAdmin, nsfw):
    res = client.patch(
        "/medium/3/metadata",
        json={"rating": "e", "tags": ["A"], "absentTags": []},
    )
    assert res.status_code == 200


def test_cant_update_missing_medium(client, asAdmin, nsfw):
    res = client.patch(
        "/medium/233/metadata",
        json={"rating": "e", "tags": ["A"], "absentTags": []},
    )
    assert res.status_code == 400


def test_specifiying_empty_tags_means_remove_all(client, asAdmin, nsfw):
    res = client.patch(
        "/medium/2/metadata", json={"rating": "q", "tags": [], "absentTags": []}
    )
    assert res.status_code == 200
    res = client.get("/medium/2")
    assert res.status_code == 200
    json_result = res.get_json()
    assert len(json_result["tags"]) == 0


def test_can_update_medium_with_duplicate_tags(client, asAdmin):
    res = client.patch(
        "/medium/3/metadata",
        json={
            "rating": "q",
            "tags": ["new_tag", "new_tag", "c:pete"],
            "absentTags": [],
        },
    )
    assert res.status_code == 200


def test_can_update_medium_without_changes(client, asAdmin, nsfw):
    res = client.get("/medium/5")
    old_model = res.get_json()

    res = client.patch(
        "/medium/5/metadata",
        json=old_model,
    )
    assert res.status_code == 200


def test_can_update_absent_tags(client, asAdmin):
    res = client.get("/medium/13")
    old_model = res.get_json()

    res = client.patch(
        "/medium/13/metadata",
        json={
            "rating": old_model["rating"],
            "tags": old_model["tags"],
            "absentTags": ["B"],
        },
    )
    assert res.status_code == 200


def test_cant_have_same_tag_present_and_absent(client, asAdmin):
    res = client.get("/medium/13")
    old_model = res.get_json()

    res = client.patch(
        "/medium/13/metadata",
        json={
            "rating": old_model["rating"],
            "tags": ["B"],
            "absentTags": ["B"],
        },
    )
    assert res.status_code == 200


def test_cant_have_tag_present_and_implied_tag_absent(client, asAdmin):
    res = client.patch(
        "/medium/13/metadata",
        json={
            "rating": "s",
            "tags": ["c:tinkerbell"],
            "absentTags": ["u:peter.pan"],
        },
    )

    res = client.get("/medium/13")
    new_model = res.get_json()
    assert "u:peter.pan" not in new_model["absentTags"]
