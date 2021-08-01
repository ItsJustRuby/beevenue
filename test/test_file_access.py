def test_cannot_access_files_without_logging_in(client):
    res = client.get("/files/hash1.jpg")
    assert res.status_code == 401


def test_can_access_files(client, asAdmin):
    res = client.get("/files/hash1.jpg")
    assert res.status_code == 200


def test_can_access_files_as_user(client, asUser):
    res = client.get("/files/hash1.jpg")
    assert res.status_code == 200


def test_accessing_nonexistant_file_does_not_crash(client, asAdmin):
    res = client.get("/files/12345678.jpg")
    assert res.status_code < 500


def test_cannot_access_thumbs_without_logging_in(client):
    res = client.get("/thumbs/hash1.jpg")
    assert res.status_code == 401


def test_accessing_thumbs_for_nonexistant_medium_does_not_crash(
    client, asAdmin
):
    res = client.get("/thumbs/ffffffff.jpg")
    assert res.status_code < 500


def test_can_access_thumb(client, asAdmin):
    res = client.get("/thumbs/hash1.jpg")
    assert res.status_code == 200
