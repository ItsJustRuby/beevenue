from __future__ import annotations
from typing import List

from ...document_types import MediumDocument


class BatchSearchResults:
    """Viewmodel to hold results of batch (unpaginated) search."""

    @staticmethod
    def empty() -> BatchSearchResults:
        return BatchSearchResults([])

    def __init__(self, items: List[MediumDocument]):
        self.items = items
