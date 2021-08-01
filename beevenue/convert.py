from typing import Any

from flask import jsonify
from sentry_sdk import start_span

from .core.detail import MediumDetail
from .core.search.batch_search_results import BatchSearchResults
from .core.search.pagination import Pagination
from .core.tags.tag_summary import TagSummary
from .models import Tag
from .viewmodels import (
    batch_search_results_schema,
    medium_detail_schema,
    pagination_schema,
    tag_show_schema,
    tag_summary_schema,
)

SCHEMAS = {
    MediumDetail: medium_detail_schema,
    Tag: tag_show_schema,
    Pagination: pagination_schema,
    TagSummary: tag_summary_schema,
    BatchSearchResults: batch_search_results_schema,
}


def try_convert_model(model: Any) -> Any:
    """Use custom schemas to serialize models (or the default on fallback).

    This allows us to simply return models from our flask endpoints and
    convert them to JSON in this one central location, instead of in every
    endpoint separately."""

    with start_span(op="http", description="try_convert_model"):
        schema = SCHEMAS.get(type(model), None)
        if not schema:
            return model
        return jsonify(schema.dump(model))
