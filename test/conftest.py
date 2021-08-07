import json
import logging
import os
import re
import shutil
from flask_sqlalchemy import SQLAlchemy

import pytest
from sqlalchemy.sql.expression import text

from beevenue.beevenue import get_application


def _resource(fname):
    return os.path.join(
        os.path.join(os.path.dirname(__file__), "resources"), fname
    )


def _file(folder, fname):
    return os.path.join(os.path.dirname(__file__), folder, fname)


def _thumbs_file(fname):
    return _file("thumbs", fname)


def _medium_file(fname):
    return _file("media", fname)


def _run_testing_sql(db: SQLAlchemy):
    """Fill database at given path with initial data."""
    with open(_resource("testing.sql"), "rb") as f:
        TESTING_SQL = f.read().decode("utf-8")

    session = db.create_scoped_session()
    session.execute(text(TESTING_SQL))
    session.commit()


def _ensure_folder(fname):
    """Ensure the specified folder exists and is empty."""

    folder = os.path.join(os.path.dirname(__file__), fname)
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.mkdir(folder)


def _add_simple_images(fname, hash_prefixes):
    res = _resource(fname)

    for hash_prefix in hash_prefixes:
        shutil.copy(res, _medium_file(f"{hash_prefix}.jpg"))
        shutil.copy(res, _thumbs_file(f"{hash_prefix}.s.jpg"))
        shutil.copy(res, _thumbs_file(f"{hash_prefix}.l.jpg"))


RAN_ONCE = False
SQLITE_PROTOTYPE = None


def _client():
    """Set up the testing client."""
    global RAN_ONCE

    def fill_db(app, db):
        """Create schema and fill the SQL database with initial data."""

        session = db.create_scoped_session()

        session.connection().connection.set_isolation_level(0)
        session.execute(
            text(
                """
                DROP SCHEMA public CASCADE;
                CREATE SCHEMA public;
                GRANT ALL ON SCHEMA public TO testing;
                """
            )
        )
        session.commit()
        session.connection().connection.set_isolation_level(1)

        db.create_all()
        _run_testing_sql(db)
        app.testing_db = db

    app = get_application(fill_db)

    if not RAN_ONCE:
        _ensure_folder("media")
        _ensure_folder("thumbs")
        _add_simple_images(
            "placeholder.jpg", ["hash1", "hash2", "hash3", "hash4", "hash5"]
        )

    # Some tests ruin this file by overwriting it. So we restore it when we're done.
    with open(_resource("testing_rules.json"), "r") as rules_file:
        rules_file_contents = rules_file.read()

    c = app.test_client()
    c.app_under_test = app

    yield c

    with open(_resource("testing_rules.json"), "w") as rules_file:
        rules_file.write(rules_file_contents)

    RAN_ONCE = True


@pytest.fixture
def client(caplog):
    """Return the current testing client."""
    caplog.set_level(logging.DEBUG)
    for c in _client():
        yield c


@pytest.fixture
def nsfw(client):
    """Ensure that the current session is not tagged as 'sfw'."""
    res = client.patch("/sfw", json={"sfwSession": False})
    assert res.status_code == 200


@pytest.fixture
def asAdmin(client):
    """Ensure that we are logged in as the 'admin' role."""
    res = client.post("/login", json={"username": "admin", "password": "admin"})
    assert res.status_code == 200


@pytest.fixture
def withVideo(client):
    """Ensure that some uploaded video is available."""
    runner = client.app_under_test.test_cli_runner()
    result = runner.invoke(args=["import", _resource("tiny_video.mp4")])
    if result.exception:
        raise result.exception
    print(result.__dict__)
    stdout = result.stdout_bytes.decode("utf-8")
    match = re.search(r"\(Medium (?P<medium_id>.+)\)", stdout)
    if not match:
        raise Exception("Could not determine Medium id after upload")
    medium_id_str = match.group("medium_id")
    medium_id = int(medium_id_str)
    yield {"medium_id": medium_id}


@pytest.fixture
def asUser(client):
    """Ensure that we are logged in as the 'user' role."""
    res = client.post("/login", json={"username": "user", "password": "user"})
    assert res.status_code == 200


@pytest.fixture
def withTrivialRules(client):
    """Ensure that the 'trivial' ruleset is active."""
    withRules(client, "test/resources/testing_rules_trivial.json")


@pytest.fixture
def withSimpleRules(client):
    """Ensure that the 'rating' ruleset is active."""
    withRules(client, "test/resources/testing_rules_simple.json")


def withRules(client, path):
    """Ensure that a specific ruleset is active."""
    with open(path, "r") as f:
        contents = f.read()

    res = client.post("/rules", json=json.loads(contents))
    assert res.status_code == 200
