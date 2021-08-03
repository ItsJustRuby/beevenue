from typing import List, FrozenSet

from .document_types import MediumDocument, TinyMediumDocument


class IndexedMedium(
    MediumDocument
):  # pylint: disable=too-many-instance-attributes
    """In-memory representation of a medium."""

    __slots__: List[str] = []

    def __init__(
        self,
        medium_id: int,
        medium_hash: str,
        mime_type: str,
        rating: str,
        tiny_thumbnail: bytes,
        innate_tag_names: FrozenSet[str],
        searchable_tag_names: FrozenSet[str],
        absent_tag_names: FrozenSet[str],
    ) -> None:
        self.medium_id = medium_id
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
        if not isinstance(other, IndexedMedium):
            return NotImplemented
        return self.medium_id == other.medium_id

    def __str__(self) -> str:
        return f"<IndexedMedium {self.medium_id}>"

    def __repr__(self) -> str:
        return self.__str__()


class TinyIndexedMedium(TinyMediumDocument):
    """Slimmer in-memory representation of a medium."""

    @staticmethod
    def from_full(full: MediumDocument) -> "TinyIndexedMedium":
        return TinyIndexedMedium(
            full.medium_id,
            full.medium_hash,
            full.rating,
            full.innate_tag_names,
            full.searchable_tag_names,
            full.absent_tag_names,
        )

    def __init__(
        self,
        medium_id: int,
        medium_hash: str,
        rating: str,
        innate_tag_names: FrozenSet[str],
        searchable_tag_names: FrozenSet[str],
        absent_tag_names: FrozenSet[str],
    ) -> None:
        self.medium_id = medium_id
        self.medium_hash = medium_hash
        self.rating = rating
        self.innate_tag_names = innate_tag_names
        self.searchable_tag_names = searchable_tag_names
        self.absent_tag_names = absent_tag_names

    def __hash__(self) -> int:
        return self.medium_id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TinyIndexedMedium):
            return NotImplemented
        return self.medium_id == other.medium_id

    def __str__(self) -> str:
        return f"<TinyIndexedMedium {self.medium_id}>"

    def __repr__(self) -> str:
        return self.__str__()
