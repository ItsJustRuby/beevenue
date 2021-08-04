import base64
from typing import List, Optional

from marshmallow import fields, Schema

from beevenue import paths

from .core.search.batch_search_results import BatchSearchResults
from .models import Tag
from .document_types import MediumDocument


class _MediumDocumentSchema(Schema):
    medium_id = fields.Int(data_key="id")
    tags = fields.Method("extract_innate_tags")
    absent_tag_names = fields.Method(
        "extract_absent_tags", data_key="absentTags"
    )
    medium_hash = fields.String(data_key="hash")
    rating = fields.String()
    mime_type = fields.String(data_key="mimeType")

    def extract_innate_tags(self, obj: MediumDocument) -> List[str]:
        return sorted(
            [  # pylint: disable=unnecessary-comprehension
                t for t in obj.innate_tag_names
            ]
        )

    def extract_absent_tags(self, obj: MediumDocument) -> List[str]:
        return sorted(list(obj.absent_tag_names))


class _MediumDocumentDetailSchema(_MediumDocumentSchema):
    similar = fields.Nested(
        "_MediumDocumentDetailSchema",
        many=True,
        only=["medium_id", "medium_hash"],
    )


class _PaginationMediumSchema(_MediumDocumentSchema):
    tiny_thumbnail = fields.Method("get_thumb", data_key="tinyThumbnail")

    def get_thumb(self, obj: MediumDocument) -> Optional[str]:
        return base64.b64encode(obj.tiny_thumbnail).decode("utf-8")


class _BatchSearchResultsSchema(Schema):
    items = fields.Method("get_items")

    def get_items(self, obj: BatchSearchResults) -> List[str]:
        return [
            paths.medium_filename(x.medium_hash, x.mime_type) for x in obj.items
        ]


class _PaginationSchema(Schema):
    items = fields.Nested(
        _PaginationMediumSchema,
        many=True,
        only=["medium_id", "medium_hash", "tiny_thumbnail"],
    )
    page_count = fields.Int(data_key="pageCount")
    page_number = fields.Int(data_key="pageNumber")
    page_size = fields.Int(data_key="pageSize")


class _TagShowSchema(Schema):
    aliases = fields.Method("get_aliases")
    count = fields.Method("get_media_count")

    rating = fields.String()
    tag = fields.String()

    implied_by_this = fields.Method("get_implied_by_this")
    implying_this = fields.Method("get_implying_this")

    def get_aliases(self, obj: Tag) -> List[str]:
        return [t.alias for t in obj.aliases]

    def get_media_count(self, obj: Tag) -> int:
        return len(obj.media)

    def get_implied_by_this(self, obj: Tag) -> List[str]:
        return [t.tag for t in obj.implied_by_this]

    def get_implying_this(self, obj: Tag) -> List[str]:
        return [t.tag for t in obj.implying_this]


class _TagSummaryItemSchema(Schema):
    media_count = fields.Int(data_key="mediaCount")
    implied_by_something = fields.Bool(data_key="impliedBySomething")

    class Meta:
        """Only serialize these exact fields."""

        fields = (
            "tag",
            "media_count",
            "rating",
            "implied_by_something",
        )


class _TagSummarySchema(Schema):
    tags = fields.Nested(_TagSummaryItemSchema, many=True)


MEDIUM_DETAIL_SCHEMA = _MediumDocumentDetailSchema()
PAGINATION_SCHEMA = _PaginationSchema()
BATCH_SEARCH_RESULTS_SCHEMA = _BatchSearchResultsSchema()
TAG_SUMMARY_SCHEMA = _TagSummarySchema()
TAG_SHOW_SCHEMA = _TagShowSchema()
