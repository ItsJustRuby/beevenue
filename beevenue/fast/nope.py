from typing import Any, Dict, List, Optional

from .types import Query, SubCache


class NotACache(SubCache):
    """This caches holds and does nothing. It's useful for consistency."""

    def delete(self, *queries: Query) -> int:
        """Should never happen."""
        return 0

    def get(self, query: Query) -> Optional[Any]:
        return None

    def set(self, query: Query, value: Any) -> None:
        """Should never happen."""

    def get_many(self, queries: List[Query]) -> Dict[Query, Any]:
        """Should never happen."""

    def set_many(self, values: Dict[Query, Any]) -> None:
        """Should never happen."""
