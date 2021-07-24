from marshmallow import fields, Schema

from ..schemas import (
    PaginationQueryParamsSchema,
    requires_json_body,
    requires_query_params,
)


class _BatchSearchQueryParamsSchema(Schema):
    q = fields.String(required=True)


class _SearchQueryParamsSchema(
    _BatchSearchQueryParamsSchema, PaginationQueryParamsSchema
):
    pass


search_query_params_schema = requires_query_params(_SearchQueryParamsSchema())


batch_search_query_params_schema = requires_query_params(
    _BatchSearchQueryParamsSchema()
)


class _UpdateTagSchema(Schema):
    tag = fields.String()
    rating = fields.String()


update_tag_schema = requires_json_body(_UpdateTagSchema())


class _AddTagsBatchSchema(Schema):
    isAbsent = fields.Bool(required=True)
    tags = fields.List(fields.String, required=True)
    mediumIds = fields.List(fields.Int, required=True)


add_tags_batch_schema = requires_json_body(_AddTagsBatchSchema())
