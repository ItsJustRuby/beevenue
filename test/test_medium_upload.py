from io import BytesIO
import subprocess

import pytest


def _current_newest_medium_id(client):
    res = client.get("/media?pageNumber=1&pageSize=10")
    assert res.status_code == 200
    return res.get_json()["items"][0]["id"]


def test_cannot_upload_medium_without_login(client):
    res = client.post("/medium")
    assert res.status_code == 401


def test_cannot_upload_medium_as_user(client, asUser):
    res = client.post("/medium")
    assert res.status_code == 403


def test_uploading_medium_as_admin_requires_some_files_in_request(
    client, asAdmin
):
    res = client.post("/medium")
    assert res.status_code == 400


def test_uploading_medium_as_admin_succeeds(client, asAdmin, nsfw):
    previously_newest_medium_id = _current_newest_medium_id(client)
    print(previously_newest_medium_id)

    with open("test/resources/placeholder.jpg", "rb") as f:
        contents = f.read()
    res = client.post(
        "/medium", data={"file": (BytesIO(contents), "example.foo")}
    )
    assert res.status_code == 200

    currently_newest_medium_id = _current_newest_medium_id(client)

    print(currently_newest_medium_id)
    assert currently_newest_medium_id > previously_newest_medium_id


def test_uploading_same_medium_twice_fails(client, asAdmin):
    with open("test/resources/placeholder.jpg", "rb") as f:
        contents = f.read()
    res = client.post(
        "/medium", data={"file": (BytesIO(contents), "example.foo")}
    )
    assert res.status_code == 200

    res = client.post(
        "/medium", data={"file": (BytesIO(contents), "second_example.bar")}
    )
    assert res.status_code == 400


def test_uploading_weird_mime_type_fails(client, asAdmin):
    with open("test/resources/testing.sql", "rb") as f:
        contents = f.read()
    res = client.post(
        "/medium", data={"file": (BytesIO(contents), "example.foo")}
    )
    assert res.status_code == 400


@pytest.mark.parametrize(
    "filename",
    [
        "1234 - rating_q u_overwatch A.jpg",
        "1234 - rating_q.jpg",
        "1234 - A.jpg",
    ],
)
def test_uploading_medium_with_taggy_filename_succeeds(
    client, asAdmin, filename
):
    with open("test/resources/placeholder.jpg", "rb") as f:
        contents = f.read()
    res = client.post(
        "/medium",
        data={"file": (BytesIO(contents), filename)},
    )
    assert res.status_code == 200


@pytest.mark.parametrize("filename", ["", "    "])
def test_uploading_medium_with_empty_filename_fails(client, asAdmin, filename):
    with open("test/resources/placeholder.jpg", "rb") as f:
        contents = f.read()
    res = client.post(
        "/medium",
        data={"file": (BytesIO(contents), filename)},
    )
    assert res.status_code == 200


def test_uploading_video_with_broken_ffmpeg(client, asAdmin, monkeypatch):
    def fake_run(*args, **kwargs):
        class FakeResult:
            returncode = 1

        return FakeResult()

    monkeypatch.setattr(subprocess, "run", fake_run)

    with open("test/resources/tiny_video.mp4", "rb") as f:
        contents = f.read()
    res = client.post(
        "/medium",
        data={"file": (BytesIO(contents), "example.mp4")},
    )
    assert res.status_code == 400
