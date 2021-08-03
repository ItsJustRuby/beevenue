from beevenue.document_types import TinyMediumDocument
from typing import Generator, Iterable

from .common import Iff, Then
from .violations import Violation


class Rule:
    """Rule to check against media.

    Consists of one Iff part and one or more Then parts."""

    def __init__(self, iff: Iff, thens: Iterable[Then]):
        if not iff or not thens:
            raise Exception("You must configure one IF and at least one THEN")

        self.iff = iff
        self.thens = thens

    def violations_for(
        self, medium: TinyMediumDocument
    ) -> Generator[Violation, None, None]:
        if not self.iff.applies_to(medium):
            return

        for then in self.thens:
            for violation in then.violations_for(medium):
                yield violation

    def is_violated_by(self, medium: TinyMediumDocument) -> bool:
        """Check if that medium violates this rule."""
        return bool(next(self.violations_for(medium), None))

    def pprint(self) -> str:
        """Pretty-print this rule."""

        result = f"{self.iff.pprint_if()} "
        result += " and ".join([then.pprint_then() for then in self.thens])
        return result
