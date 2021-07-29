from beevenue.types import TinyMediumDocument

from .common import Iff


class All(Iff):
    """Select all media."""

    def applies_to(self, _: TinyMediumDocument) -> bool:
        return True

    def pprint_if(self) -> str:
        return "Any medium"
