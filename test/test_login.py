def test_login_missing_user_failure(client):
    res = client.post(
        "/login", json={"username": "klashki", "password": "passenger"}
    )
    assert res.status_code == 401


def test_login_incorrect_password_failure(client):
    res = client.post(
        "/login", json={"username": "user", "password": "incorrectPassword"}
    )
    assert res.status_code == 401


def test_login_allows_options_first(client):
    client.options("/login")


def test_double_login_does_not_modify_session(client):
    res = client.post("/login", json={"username": "user", "password": "user"})
    assert res.status_code == 200
    assert res.get_json()["sfwSession"] == True

    res = client.patch("/sfw", json={"sfwSession": False})
    assert res.status_code == 200

    # Now, SFW should be False
    res = client.get("/login")
    assert res.status_code == 200
    assert res.get_json()["sfwSession"] == False

    res = client.post("/login", json={"username": "user", "password": "user"})
    assert res.status_code == 200

    # SFW should *still* be False, not modified.
    res = client.get("/login")
    assert res.status_code == 200
    assert res.get_json()["sfwSession"] == False


def test_get_logged_in_as_user(client, asUser):
    res = client.get("/login")
    assert res.status_code == 200


def test_if_logged_in_as_user_with_faulty_session_nothing_crashes(
    client, asUser
):
    with client.session_transaction() as session:
        del session["role"]

    res = client.get("/login")
    assert res.status_code == 200


def test_get_logged_in_anonymously(client):
    res = client.get("/login")
    assert res.status_code == 200
