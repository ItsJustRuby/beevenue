from sqlalchemy.sql import func
from sqlalchemy.orm import load_only

from ....models import Medium, Tag, MediaTags, TagAlias, TagImplication

from .terms import get_search_terms


def _tag_to_id(session, search_terms):
    # In a separate query, create a map of tagname => tagid
    # (or => none if searched tag sucks)
    all_tag_names = set()
    all_tag_names |= set([t.term for t in search_terms.positive])
    all_tag_names |= set([t.term for t in search_terms.negative])

    if all_tag_names:
        found_tags = session.query(Tag).filter(
            Tag.tag.in_(all_tag_names)).all()
    else:
        found_tags = []

    tag_to_id = {}
    for found_tag in found_tags:
        tag_to_id[found_tag.tag] = found_tag.id

    return tag_to_id


def _tag_ids_per_category(session, search_terms):
    # Lookup category => tag_ids_in_category dict
    category_names = set([t.category for t in search_terms.category])

    tag_ids_per_category = {}

    for category_name in category_names:
        tags_in_this_category = \
            session.query(Tag)\
            .filter(Tag.tag.like(f'{category_name}:%'))\
            .all()

        tag_ids_in_this_category = [t.id for t in tags_in_this_category]
        tag_ids_per_category[category_name] = set(tag_ids_in_this_category)

    return tag_ids_per_category


def _having_expr(category_term):
    if category_term.operator in (':', '='):
        return func.count(MediaTags.c.tag_id) == category_term.number
    if category_term.operator == '<':
        return func.count(MediaTags.c.tag_id) < category_term.number
    if category_term.operator == '>':
        return func.count(MediaTags.c.tag_id) > category_term.number
    if category_term.operator == '<=':
        return func.count(MediaTags.c.tag_id) <= category_term.number
    if category_term.operator == '>=':
        return func.count(MediaTags.c.tag_id) >= category_term.number
    if category_term.operator == '!=':
        return func.count(MediaTags.c.tag_id) != category_term.number
    raise Exception(f"Unknown operator in {category_term}")


# Pass "is_and"=True to AND together conditions.
# Otherwise, they will be ORed together.
def _find_medium_tags(session, tag_to_id, terms, is_and):

    # User supplied no search terms: show nothing
    if not terms:
        return []

    ids = set()
    for t in terms:
        maybe_id = tag_to_id.get(t.term, None)
        if maybe_id:
            ids.add(maybe_id)

    # TODO Write unit test
    if ids:
        implications = session.query(TagImplication)\
            .filter(TagImplication.c.implied_tag_id.in_(ids))\
            .all()

        implying_tag_ids = [i.implying_tag_id for i in implications]
        ids |= set(implying_tag_ids)

    # User supplied terms, but none were valid
    if not ids:
        return []

    q = session\
        .query(MediaTags.c.medium_id)\
        .filter(MediaTags.c.tag_id.in_(ids))\
        .group_by(MediaTags.c.medium_id)
    if is_and:
        # For ANDed together terms, the number of entries in
        # the MediaTags table must be the same as the number of
        # expected matches to AND terms.
        # However, as tag implication-based terms are added automatically,
        # we do not have to count those.
        q = q.having(func.count() >= (len(ids) - len(implying_tag_ids)))

    return q.all()


# Pass tag_ids_per_category != None to search for "ctags>2",
# or None for "tags>2" etc.
def _find_helper(session, terms, tag_ids_per_category=None):
    found = set()
    for term in terms:
        filters = []

        if tag_ids_per_category:
            tag_ids = tag_ids_per_category[term.category]
            if tag_ids:
                filters.append(MediaTags.c.tag_id.in_(tag_ids))

        q = session\
            .query(MediaTags.c.medium_id)\
            .select_from(MediaTags)\
            .group_by(MediaTags.c.medium_id)

        if filters:
            q = q.filter(*filters)

        # TODO Note that this is not really general enough. It doesn't
        # catch "<1" or "<=0" etc.
        if not (term.number == 0 and term.operator in (":", "=")):
            q = q.having(_having_expr(term))

        medium_ids = q.all()
        medium_ids = set([m.medium_id for m in medium_ids])

        if term.number == 0 and term.operator in (":", "="):
            all_media = Medium.query.all()
            medium_ids = set([m.id for m in all_media]) - medium_ids

        found_medium_ids = set(medium_ids)
        if found:
            found &= found_medium_ids
        else:
            found = found_medium_ids

    return found


def _replace_aliases(session, search_terms):
    possible_alias_terms = set()
    possible_alias_terms |= set([t.term for t in search_terms.positive])
    possible_alias_terms |= set([t.term for t in search_terms.negative])

    if not possible_alias_terms:
        # Nothing to do
        return search_terms

    found_aliases = session.query(TagAlias)\
        .filter(TagAlias.alias.in_(possible_alias_terms))\
        .all()

    replacements = {}

    for found_alias in found_aliases:
        replacements[found_alias.alias] = found_alias.tag.tag

    for old, new in replacements.items():
        for target in [search_terms.positive, search_terms.negative]:
            for term in target:
                if term.term == old:
                    term.term = new

    return search_terms


def _find_by_category(session, search_terms):
    tag_ids_per_category = _tag_ids_per_category(session, search_terms)
    return _find_helper(session, search_terms.category, tag_ids_per_category)


def _find_by_counting(session, counting_terms):
    return _find_helper(session, counting_terms)


def _evaluate(context, search_terms):
    session = context.session()

    search_terms = _replace_aliases(session, search_terms)
    tag_to_id = _tag_to_id(session, search_terms)

    found_by_counting = _find_by_counting(session, search_terms.counting)

    found_by_category = _find_by_category(
        session,
        search_terms)

    pos_medium_tags = _find_medium_tags(
        session, tag_to_id, search_terms.positive, is_and=True)
    neg_medium_tags = _find_medium_tags(
        session, tag_to_id, search_terms.negative, is_and=False)

    to_exclude = set([mt.medium_id for mt in neg_medium_tags])

    found_by_rating = set()
    if search_terms.rating:
        rating_term = search_terms.rating[0]
        ids = session.query(Medium.id).select_from(Medium)\
            .filter(Medium.rating == rating_term.rating).all()
        ids = [i[0] for i in ids]
        found_by_rating = set(ids)

    found_by_pos = \
        set([mt.medium_id for mt in pos_medium_tags])

    # INTERSECT all non-empty result sets.
    non_empty_result_sets = []
    for result_set in [
            found_by_pos, found_by_category,
            found_by_counting, found_by_rating]:
        if len(result_set) > 0:
            non_empty_result_sets.append(result_set)

    if len(non_empty_result_sets) == 0:
        if len(search_terms) == 0 or len(to_exclude) > 0:
            found = set(session.query(MediaTags.c.medium_id).all())
            found = set([f[0] for f in found])
        else:
            found = set()
    else:
        found = non_empty_result_sets[0]
        for other_set in non_empty_result_sets[1:]:
            found &= other_set

    found -= to_exclude

    return found


def run_search(context, search_term_list):
    search_terms = get_search_terms(search_term_list)

    medium_ids = _evaluate(context, search_terms)

    filters = []
    if context.is_sfw:
        filters.append(Medium.rating == 's')
    if context.user_role != 'admin':
        filters.append(Medium.rating != 'e')
        filters.append(Medium.rating != 'u')

    if not medium_ids:
        return []

    if filters:
        result = Medium.query.filter(Medium.id.in_(medium_ids), *filters)\
            .options(load_only("id"))\
            .all()
        medium_ids = [m.id for m in result]

    return medium_ids
