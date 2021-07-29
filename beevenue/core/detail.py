from typing import List

from ..types import TinyMediumDocument


class MediumDetail(  # pylint: disable=too-many-instance-attributes
    TinyMediumDocument
):
    """Viewmodel extending MediumDocument.

    Holds info about "similar" media as well."""

    __slots__ = ["similar"]

    similar: List[TinyMediumDocument]

    def __init__(
        self, medium: TinyMediumDocument, similar: List[TinyMediumDocument]
    ):
        self.medium_id = medium.medium_id
        self.aspect_ratio = medium.aspect_ratio
        self.medium_hash = medium.medium_hash
        self.mime_type = medium.mime_type
        self.rating = medium.rating
        self.innate_tag_names = medium.innate_tag_names
        self.searchable_tag_names = medium.searchable_tag_names
        self.absent_tag_names = medium.absent_tag_names

        self.similar = similar
