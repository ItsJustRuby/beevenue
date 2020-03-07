from flask import request

from ....spindex.spindex import SPINDEX

from .terms import get_search_terms
from .terms.simple import RatingSearchTerm, Negative


class Pagination(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def empty(cls):
        return cls(items=[], pageCount=0, pageNumber=1, pageSize=1)


def find_all():
    return _run([])


def run(search_term_list):
    search_terms = get_search_terms(search_term_list)

    if not search_terms:
        return Pagination.empty()

    return _run(search_terms)


def _run(search_terms):
    context = request.beevenue_context
    medium_ids = _search(context, search_terms)

    if not medium_ids:
        return Pagination.empty()

    medium_ids = list(medium_ids)
    medium_ids.sort(reverse=True)
    pagination = _paginate(medium_ids)
    media = SPINDEX.get_media(pagination.items)

    pagination.items = media
    return pagination


def _censor(context, search_terms):
    search_terms = set(search_terms)

    if context.is_sfw:
        search_terms.add(RatingSearchTerm("s"))
    if context.user_role != "admin":
        search_terms.add(Negative(RatingSearchTerm("e")))
        search_terms.add(Negative(RatingSearchTerm("u")))

    return search_terms


def _search(context, search_terms):
    search_terms = _censor(context, search_terms)

    all_media = SPINDEX.all()
    result = set()

    for m in all_media:
        for search_term in search_terms:
            if not search_term.applies_to(m):
                break
        else:
            result.add(m.id)

    return result


def _paginate(ids):
    pageNumber = int(request.args.get("pageNumber"))
    pageSize = int(request.args.get("pageSize"))

    if pageSize < 1:
        return []

    if pageNumber < 1:
        skip = 0
    else:
        skip = (pageNumber - 1) * pageSize

    pageCount = len(ids) // pageSize
    if (len(ids) % pageSize) != 0:
        pageCount += 1

    return Pagination(
        items=ids[skip : skip + pageSize],
        pageCount=pageCount,
        pageNumber=pageNumber,
        pageSize=pageSize,
    )
