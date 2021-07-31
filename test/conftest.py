import json
import logging
import os
import re
import shutil
import sqlite3
import tempfile

import pytest

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


def _run_testing_sql(temp_path):
    """Fill database at given path with initial data."""
    with open(_resource("testing.sql"), "rb") as f:
        TESTING_SQL = f.read().decode("utf-8")

    escaped_temp_path = temp_path.replace("\\", "\\\\")
    conn = sqlite3.connect(escaped_temp_path)
    conn.executescript(TESTING_SQL)
    conn.commit()
    conn.close()


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

    temp_fd, temp_path = tempfile.mkstemp(suffix=".db")
    temp_nice_path = os.path.abspath(temp_path)

    connection_string = f"sqlite:///{temp_nice_path}"

    def extra_config(application):
        """Set specific testing-only flags on the testee."""
        application.config["SQLALCHEMY_DATABASE_URI"] = connection_string

    def fill_db(db):
        """Create schema and fill the SQL database with initial data."""
        global SQLITE_PROTOTYPE

        if not RAN_ONCE:
            db.create_all()

            with open(temp_path, "rb") as f:
                SQLITE_PROTOTYPE = f.read()
        else:
            print("Overwriting DB with prototype")
            with open(temp_nice_path, "wb") as target:
                target.seek(0)
                target.write(SQLITE_PROTOTYPE)
                target.truncate()

        _run_testing_sql(temp_nice_path)

    app = get_application(extra_config, fill_db)

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

    def sql_debug(raw_query_text):
        escaped_temp_path = temp_path.replace("\\", "\\\\")
        conn = sqlite3.connect(escaped_temp_path)
        for row in conn.execute(raw_query_text):
            print(row)
        conn.close()

    c.sql_debug = sql_debug

    # Example code to run some arbitrary SQL query - e.g. to set
    # currently hardcoded constants like "what's the Id of the video medium"
    # dynamically:
    #
    # escaped_temp_path = temp_nice_path.replace("\\", "\\\\")
    # conn = sqlite3.connect(escaped_temp_path)
    # cur = conn.cursor()
    # cur.execute("SELECT * FROM medium")
    # rows = cur.fetchall()
    # c._rows = rows

    # conn.close()

    yield c

    with open(_resource("testing_rules.json"), "w") as rules_file:
        rules_file.write(rules_file_contents)

    os.close(temp_fd)
    os.unlink(temp_path)

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
