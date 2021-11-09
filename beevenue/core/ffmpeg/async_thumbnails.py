import base64
from typing import Any, List, Optional, Tuple

from flask import current_app
from redis import Redis


def start_persisting(medium_id: int) -> None:
    redis = Redis(host="redis", db=2)
    redis.set(f"T_{medium_id}", "")


def finish_persisting(
    medium_id: int, thumbnails: List[Tuple[int, bytes]]
) -> None:
    expiry_seconds = current_app.config[
        "BEEVENUE_TEMPORARY_THUMBNAIL_EXPIRY_SECONDS"
    ]

    redis = Redis(host="redis", db=2)
    redis_dict: Any = {}

    idx = 0
    last_size_pixels = -1

    for size_pixels, payload in thumbnails:
        if size_pixels != last_size_pixels:
            last_size_pixels = size_pixels
            idx = 0

        key = f"T_{medium_id}_{size_pixels}_{idx}"
        redis_dict[key] = payload
        idx += 1

    redis_dict[f"T_{medium_id}"] = ",".join(list(redis_dict.keys()))

    redis.mset(redis_dict)
    for key in redis_dict:
        redis.expire(key, expiry_seconds)


def pick(medium_id: int, size_pixels: int, idx: int) -> Optional[bytes]:
    redis = Redis(host="redis", db=2)

    key = f"T_{medium_id}_{size_pixels}_{idx}"
    return redis.get(key)


def cleanup(medium_id: int) -> None:
    redis = Redis(host="redis", db=2)
    meta_key = f"T_{medium_id}"

    keys_as_string = redis.get(meta_key)
    if not keys_as_string:
        return

    keys = keys_as_string.split(b",")
    redis.delete(meta_key, *keys)


def try_load(medium_id: int) -> Optional[List[str]]:
    """Returns None if thumbnailing in progress.

    Returns filled List if complete, or empty list if not in progress."""
    size_pixels = 0

    for _, thumbnail_size_pixels in current_app.config[
        "BEEVENUE_THUMBNAIL_SIZES"
    ].items():
        size_pixels = thumbnail_size_pixels
        break

    redis = Redis(host="redis", db=2)

    status = redis.get(f"T_{medium_id}")
    if status is None:
        # No thumbnailing in progress
        return []
    if not status:
        # Thumbnailing in progress, but not complete (i.e. value not set)
        return None

    keys = _get_key_range(medium_id, size_pixels)
    loaded_thumbnails = redis.mget(keys)

    return [base64.b64encode(t).decode("utf-8") for t in loaded_thumbnails if t]


def _get_key_range(medium_id: int, size_pixels: int) -> List[str]:
    thumbnail_count = current_app.config["BEEVENUE_TEMPORARY_THUMBNAIL_COUNT"]
    return [
        f"T_{medium_id}_{size_pixels}_{idx}"
        for idx in range(0, thumbnail_count)
    ]
