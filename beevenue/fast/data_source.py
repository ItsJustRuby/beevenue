from abc import ABC, abstractmethod
from typing import Dict, FrozenSet, Iterable, Set, Tuple

from sqlalchemy import select

from beevenue.flask import g
from beevenue.models import TagAlias, TagImplication, Tag


class AbstractDataSource(ABC):
    """Abstract SQL data source used to load media from SQL database.

    Used to populate caches (e.g. on initial load, or when reindexing)."""

    @abstractmethod
    def alias_names(self, tag_ids: Iterable[int]) -> Set[str]:
        """Returns all names of aliases for the given tag_ids."""

    @abstractmethod
    def implied(self, tag_ids: Iterable[int]) -> Tuple[Set[int], Set[str]]:
        """Returns ids and names of tags implied by the given tag_ids."""


class MultiLoadDataSource(AbstractDataSource):
    """Data holder for fully loading a single medium's tag metadata."""

    def __init__(self, all_tag_ids: FrozenSet[int]) -> None:
        self.session = g.db
        tag_aliases = self.session.execute(
            select(TagAlias.tag_id, TagAlias.alias).filter(
                TagAlias.tag_id.in_(all_tag_ids)
            )
        ).all()
        self.tag_alias_dict = {t.tag_id: t.alias for t in tag_aliases}

        implications = self.session.execute(
            select(
                TagImplication.implying_tag_id,
                TagImplication.implied_tag_id,
            ).filter(TagImplication.implying_tag_id.in_(all_tag_ids))
        ).all()
        self.implication_dict = {
            ti.implying_tag_id: ti.implied_tag_id for ti in implications
        }

        implied_tag_names = self.session.execute(
            select(Tag.id, Tag.tag).filter(
                Tag.id.in_(list(self.implication_dict.values()))
            )
        ).all()
        self.tag_name_dict = {t.id: t.tag for t in implied_tag_names}

    def alias_names(self, tag_ids: Iterable[int]) -> Set[str]:
        result = set()
        for tag_id in tag_ids:
            if tag_id in self.tag_alias_dict:
                result.add(self.tag_alias_dict[tag_id])
        return result

    def implied(self, tag_ids: Iterable[int]) -> Tuple[Set[int], Set[str]]:
        implied_ids = set()
        for tag_id in tag_ids:
            if tag_id in self.implication_dict:
                implied_ids.add(self.implication_dict[tag_id])

        implied_names = set()
        for implied_id in implied_ids:
            implied_names.add(self.tag_name_dict[implied_id])

        return implied_ids, implied_names


class FullLoadDataSource(AbstractDataSource):
    """Data holder for fully loading multiple media's tag metadata."""

    def __init__(
        self,
        implied_by_this: Dict[int, Set[int]],
        aliases_by_id: Dict[int, Set[str]],
        tag_name_by_id: Dict[int, str],
    ):
        self.implied_by_this = implied_by_this
        self.aliases_by_id = aliases_by_id
        self.tag_name_by_id = tag_name_by_id

    def alias_names(self, tag_ids: Iterable[int]) -> Set[str]:
        result = set()
        for tag_id in tag_ids:
            result |= self.aliases_by_id[tag_id]
        return result

    def implied(self, tag_ids: Iterable[int]) -> Tuple[Set[int], Set[str]]:
        implied_ids = set()
        for tag_id in tag_ids:
            implied_ids |= self.implied_by_this[tag_id]

        implied_names = {self.tag_name_by_id[i] for i in implied_ids}

        return implied_ids, implied_names
