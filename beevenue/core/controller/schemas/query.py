
from marshmallow import fields, Schema

from ....schemas import PaginationQueryParamsSchema


class SearchQueryParamsSchema(PaginationQueryParamsSchema):
    q = fields.String(required=True)


search_query_params_schema = SearchQueryParamsSchema()


class UpdateTagSchema(Schema):
    newName = fields.String(required=True)


update_tag_schema = UpdateTagSchema()


class AddTagsBatchSchema(Schema):
    tags = fields.List(fields.String, required=True)
    mediumIds = fields.List(fields.Int, required=True)


add_tags_batch_schema = AddTagsBatchSchema()
