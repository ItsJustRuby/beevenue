from typing import Dict, List, TypedDict
from itertools import groupby

from beevenue.flask import g
from sqlalchemy import select

from ...models import Tag, TagImplication
from .censorship import Censorship
from .tags import tag_name_selector

ImplicationNodes = Dict[str, object]
ImplicationLinks = Dict[str, List[str]]
Implications = TypedDict(
    "Implications", {"nodes": ImplicationNodes, "links": ImplicationLinks}
)


def get_all_implications() -> Implications:
    session = g.db
    all_rows = session.execute(select(TagImplication)).scalars().all()

    if not all_rows:
        return {"nodes": {}, "links": {}}

    all_tag_ids = set()
    for row in all_rows:
        all_tag_ids.add(row.implying_tag_id)
        all_tag_ids.add(row.implied_tag_id)

    tags = (
        session.execute(select(Tag).filter(Tag.id.in_(all_tag_ids)))
        .scalars()
        .all()
    )

    tag_dict = {t.id: t for t in tags}

    censoring = Censorship(tag_dict, tag_name_selector)

    def grouper(implication: TagImplication) -> int:
        tag_id: int = implication.implying_tag_id
        return tag_id

    links: ImplicationLinks = {}
    for left_id, rows in groupby(all_rows, grouper):
        left = censoring.get_name(left_id)
        right = [censoring.get_name(r.implied_tag_id) for r in rows]
        links[left] = right

    nodes: ImplicationNodes = {}
    for tag_id in all_tag_ids:
        nodes[censoring.get_name(tag_id)] = {}

    return {"nodes": nodes, "links": links}
