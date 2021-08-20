import pytest


def test_otp_fails_for_invalid_medium_id(client, asAdmin):
    res = client.get("/medium/1354531/otp?target=irrelevant")
    assert res.status_code == 400


@pytest.mark.parametrize(
    "secret", ["not-a-uuid", "64bffb71bd0c4308b1b0ddbd3f776992"]
)
def test_otp_fails_for_invalid_secret(client, asAdmin, secret):
    res = client.get(f"/otp/{secret}")
    assert res.status_code == 400


def test_otp_succeeds_for_valid_medium_id(client, asAdmin):
    # target intentionally left blank
    res = client.get("/medium/1/otp?target=")
    assert (res.status_code // 100) == 3
    new_location = res.headers["Location"].removeprefix(
        "https://www.example.org"
    )
    print(new_location)

    res = client.get(new_location)
    assert res.status_code == 200

    res = client.get(new_location)
    assert res.status_code == 400

    res = client.get("/medium/1/otp?target=")
    assert (res.status_code // 100) == 3
    other_new_location = res.headers["Location"].removeprefix(
        "https://www.example.org"
    )
    assert other_new_location != new_location
