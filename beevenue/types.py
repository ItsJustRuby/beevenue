from abc import ABC
from typing import Any, FrozenSet

from flask.app import Flask


class BeevenueFlask(Flask):
    """Typing hint for main application object."""

    hostname: str
    port: int

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        Flask.__init__(self, name, *args, **kwargs)


class MediumDocument(ABC):
    """Flattened, full in-memory representation of a medium."""

    __slots__ = [
        "medium_id",
        "aspect_ratio",
        "medium_hash",
        "mime_type",
        "rating",
        "tiny_thumbnail",
        "innate_tag_names",
        "searchable_tag_names",
        "absent_tag_names",
    ]

    medium_id: int
    aspect_ratio: str
    medium_hash: str
    mime_type: str
    rating: str
    tiny_thumbnail: bytes
    innate_tag_names: FrozenSet[str]
    searchable_tag_names: FrozenSet[str]
    absent_tag_names: FrozenSet[str]


class TinyMediumDocument(ABC):
    """Flattened, low-footprint in-memory representation of a medium."""

    __slots__ = [
        "medium_id",
        "aspect_ratio",
        "medium_hash",
        "mime_type",
        "rating",
        "innate_tag_names",
        "searchable_tag_names",
        "absent_tag_names",
    ]

    medium_id: int
    aspect_ratio: str
    medium_hash: str
    mime_type: str
    rating: str
    innate_tag_names: FrozenSet[str]
    searchable_tag_names: FrozenSet[str]
    absent_tag_names: FrozenSet[str]
