from typing import Any

from flask import jsonify
from sentry_sdk import start_span

from .core.detail import MediumDetail
from .core.search.batch_search_results import BatchSearchResults
from .core.search.pagination import Pagination
from .core.tags.tag_summary import TagSummary
from .models import Tag
from .strawberry.viewmodels import VIOLATIONS_SCHEMA, ViolationsViewModel
from .viewmodels import (
    BATCH_SEARCH_RESULTS_SCHEMA,
    MEDIUM_DETAIL_SCHEMA,
    PAGINATION_SCHEMA,
    TAG_SHOW_SCHEMA,
    TAG_SUMMARY_SCHEMA,
)

SCHEMAS = {
    MediumDetail: MEDIUM_DETAIL_SCHEMA,
    Tag: TAG_SHOW_SCHEMA,
    Pagination: PAGINATION_SCHEMA,
    TagSummary: TAG_SUMMARY_SCHEMA,
    BatchSearchResults: BATCH_SEARCH_RESULTS_SCHEMA,
    ViolationsViewModel: VIOLATIONS_SCHEMA,
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
