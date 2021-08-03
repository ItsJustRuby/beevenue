from abc import ABC
from typing import FrozenSet


class TinyMediumDocument(ABC):
    """Flattened, low-footprint in-memory representation of a medium."""

    __slots__ = [
        "medium_id",
        "medium_hash",
        "rating",
        "innate_tag_names",
        "searchable_tag_names",
        "absent_tag_names",
    ]

    medium_id: int
    medium_hash: str
    rating: str
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
        "tiny_thumbnail",
        "innate_tag_names",
        "searchable_tag_names",
        "absent_tag_names",
    ]

    medium_id: int
    medium_hash: str
    mime_type: str
    rating: str
    tiny_thumbnail: bytes
    innate_tag_names: FrozenSet[str]
    searchable_tag_names: FrozenSet[str]
    absent_tag_names: FrozenSet[str]
