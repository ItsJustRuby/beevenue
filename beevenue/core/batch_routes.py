from flask import Blueprint

from beevenue.flask import request

from .. import permissions
from .search import search
from .schemas import batch_search_query_params_schema


bp = Blueprint("batch", __name__)


@bp.route("/search/batch")
@permissions.is_owner
@batch_search_query_params_schema
def get_backup_sh():  # type: ignore
    search_term_list = request.args.get("q").split(" ")
    return search.run_unpaginated(search_term_list)
