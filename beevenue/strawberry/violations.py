from abc import abstractmethod
from typing import Iterable, List, Literal, Tuple


FixKind = Literal["addTag", "addAbsentTag"]


class QuickFix:
    """Operation which can easily performed on a medium to fix a violation."""

    @abstractmethod
    def serialize(self) -> Tuple[FixKind, str]:
        """Serialize yourself to a JSON holder"""


class AddTag(QuickFix):
    """Add this tag to the medium to fix the violation."""

    def __init__(self, tag: str) -> None:
        self.tag = tag

    def serialize(self) -> Tuple[FixKind, str]:
        return (
            "addTag",
            self.tag,
        )


class AddAbsentTag(QuickFix):
    """Add this absent tag to the medium to fix the violation."""

    def __init__(self, tag: str) -> None:
        self.tag = tag

    def serialize(self) -> Tuple[FixKind, str]:
        return (
            "addAbsentTag",
            self.tag,
        )


class Violation:
    """Base class for all rule violations."""

    @abstractmethod
    def get_fixes(self) -> List[QuickFix]:
        """Which fixes could be applied to immediately fix this issue?

        Might not always be possible, so simply return "empty array"
        to mean "no fixes available"."""


class Nontrivial(Violation):
    """The medium has something wrong with it that can't be fixed easily."""

    def get_fixes(self) -> List[QuickFix]:
        return []


class ShouldHaveTagIn(Violation):
    """The medium should have one of these tags."""

    def __init__(self, tags: Iterable[str]) -> None:
        self.tags = sorted(tags)

    def get_fixes(self) -> List[QuickFix]:
        return [AddTag(t) for t in self.tags]


class ShouldHaveTagPresentOrAbsent(Violation):
    """The medium should have this tag in tags or absentTags."""

    def __init__(self, tag: str) -> None:
        self.tag = tag

    def get_fixes(self) -> List[QuickFix]:
        return [AddTag(self.tag), AddAbsentTag(self.tag)]
