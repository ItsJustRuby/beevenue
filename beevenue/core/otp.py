from typing import Optional
from uuid import uuid4, UUID
from redis import Redis

from flask import current_app

from beevenue import paths
from beevenue.flask import g


def request(medium_id: int) -> Optional[str]:
    redis = Redis(host="redis", db=1)

    tiny = g.fast.get_medium(medium_id)
    if not tiny:
        return None
    full_path = paths.medium_filename(tiny.medium_hash, tiny.mime_type)

    some_secret = uuid4().hex

    redis.set(
        some_secret,
        full_path,
        current_app.config.get("BEEVENUE_OTP_EXPIRY_SECONDS", 30),
    )
    return some_secret


def resolve_and_destroy(secret: str) -> Optional[str]:
    try:
        UUID(secret)
    except ValueError:
        return None

    redis = Redis(host="redis", db=1)
    stored_bytes = redis.get(secret)

    if stored_bytes:
        redis.delete(secret)
        full_path = stored_bytes.decode("utf-8")
        return full_path

    return None
