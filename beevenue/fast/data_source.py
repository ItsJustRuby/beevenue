from abc import ABC, abstractmethod
from typing import Dict, Iterable, Set, Tuple

from flask import g
from sqlalchemy import select

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


class SingleLoadDataSource(AbstractDataSource):
    """Data holder for fully loading a single medium's tag metadata."""

    def __init__(self) -> None:
        self.session = g.db

    def alias_names(self, tag_ids: Iterable[int]) -> Set[str]:
        tag_aliases = (
            self.session.execute(
                select(TagAlias.alias).filter(TagAlias.tag_id.in_(tag_ids))
            )
            .scalars()
            .all()
        )

        return set(tag_aliases)

    def implied(self, tag_ids: Iterable[int]) -> Tuple[Set[int], Set[str]]:
        implied_tag_ids = (
            self.session.execute(
                select(TagImplication.implied_tag_id).filter(
                    TagImplication.implying_tag_id.in_(tag_ids)
                )
            )
            .scalars()
            .all()
        )

        implied_tag_names = (
            self.session.execute(
                select(Tag.tag).filter(Tag.id.in_(implied_tag_ids))
            )
            .scalars()
            .all()
        )

        return set(implied_tag_ids), set(implied_tag_names)


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
