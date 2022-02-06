from abc import ABC
from datetime import date
from typing import FrozenSet


class TinyMediumDocument(ABC):
    """Flattened, low-footprint in-memory representation of a medium."""

    __slots__ = [
        "medium_id",
        "medium_hash",
        "rating",
        "width",
        "height",
        "filesize",
        "insert_date",
        "innate_tag_names",
        "searchable_tag_names",
        "absent_tag_names",
    ]

    medium_id: int
    medium_hash: str
    rating: str
    width: int
    height: int
    filesize: int
    insert_date: date
    innate_tag_names: FrozenSet[str]
    searchable_tag_names: FrozenSet[str]
    absent_tag_names: FrozenSet[str]


class MediumDocument(TinyMediumDocument):
    """Flattened, full in-memory representation of a medium."""

    __slots__ = [
        "medium_id",
        "medium_hash",
        "mime_type",
        "rating",
        "width",
        "height",
        "filesize",
        "insert_date",
        "tiny_thumbnail",
        "innate_tag_names",
        "searchable_tag_names",
        "absent_tag_names",
    ]

    medium_id: int
    medium_hash: str
    mime_type: str
    rating: str
    width: int
    height: int
    filesize: int
    insert_date: date
    tiny_thumbnail: bytes
    innate_tag_names: FrozenSet[str]
    searchable_tag_names: FrozenSet[str]
    absent_tag_names: FrozenSet[str]
