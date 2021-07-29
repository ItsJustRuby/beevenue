from typing import List, FrozenSet

from .types import MediumDocument, TinyMediumDocument


class SpindexedMedium(
    MediumDocument
):  # pylint: disable=too-many-instance-attributes
    """In-memory representation of a medium."""

    __slots__: List[str] = []

    def __init__(
        self,
        medium_id: int,
        aspect_ratio: str,
        medium_hash: str,
        mime_type: str,
        rating: str,
        tiny_thumbnail: bytes,
        innate_tag_names: FrozenSet[str],
        searchable_tag_names: FrozenSet[str],
        absent_tag_names: FrozenSet[str],
    ) -> None:
        self.medium_id = medium_id
        self.aspect_ratio = aspect_ratio
        self.medium_hash = medium_hash
        self.mime_type = mime_type
        self.rating = rating
        self.tiny_thumbnail = tiny_thumbnail
        self.innate_tag_names = innate_tag_names
        self.searchable_tag_names = searchable_tag_names
        self.absent_tag_names = absent_tag_names

    def __hash__(self) -> int:
        return self.medium_id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SpindexedMedium):
            return NotImplemented
        return self.medium_id == other.medium_id

    def __str__(self) -> str:
        return f"<SpindexedMedium {self.medium_id}>"

    def __repr__(self) -> str:
        return self.__str__()


class TinySpindexedMedium(TinyMediumDocument):
    """Slimmer in-memory representation of a medium."""

    def __init__(
        self,
        medium_id: int,
        rating: str,
        innate_tag_names: FrozenSet[str],
        searchable_tag_names: FrozenSet[str],
        absent_tag_names: FrozenSet[str],
    ) -> None:
        self.medium_id = medium_id
        self.rating = rating
        self.innate_tag_names = innate_tag_names
        self.searchable_tag_names = searchable_tag_names
        self.absent_tag_names = absent_tag_names

    def __hash__(self) -> int:
        return self.medium_id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TinySpindexedMedium):
            return NotImplemented
        return self.medium_id == other.medium_id

    def __str__(self) -> str:
        return f"<TinySpindexedMedium {self.medium_id}>"

    def __repr__(self) -> str:
        return self.__str__()
