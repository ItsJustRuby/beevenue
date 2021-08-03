from typing import FrozenSet, List, NamedTuple

from ..document_types import MediumDocument, TinyMediumDocument


class MediumDetail(NamedTuple):
    """Viewmodel for Medium which holds info about "similar" media as well."""

    medium_id: int
    medium_hash: str
    mime_type: str
    rating: str
    innate_tag_names: FrozenSet[str]
    searchable_tag_names: FrozenSet[str]
    absent_tag_names: FrozenSet[str]

    similar: List[TinyMediumDocument]


def create_medium_detail(
    medium: MediumDocument, similar: List[TinyMediumDocument]
) -> MediumDetail:
    return MediumDetail(
        medium_id=medium.medium_id,
        medium_hash=medium.medium_hash,
        mime_type=medium.mime_type,
        rating=medium.rating,
        innate_tag_names=medium.innate_tag_names,
        searchable_tag_names=medium.searchable_tag_names,
        absent_tag_names=medium.absent_tag_names,
        similar=similar,
    )
