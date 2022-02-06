from abc import ABCMeta, abstractmethod
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Callable, Dict, Generic, TypeVar

from ....document_types import TinyMediumDocument
from ..base import FilteringSearchTerm

Comparable = Any

OPS: Dict[str, Callable[[Comparable, Comparable], bool]] = {
    ":": lambda x, y: bool(x == y),
    "=": lambda x, y: bool(x == y),
    "<": lambda x, y: bool(x < y),
    ">": lambda x, y: bool(x > y),
    "<=": lambda x, y: bool(x <= y),
    ">=": lambda x, y: bool(x >= y),
    "!=": lambda x, y: bool(x != y),
}


TNumber = TypeVar("TNumber")


class ComparisonMixin(Generic[TNumber], metaclass=ABCMeta):
    """Mixin for terms that support comparison against some number."""

    @abstractmethod
    def parse_number(self, number: str) -> TNumber:
        ...


class IntComparisonMixin(ComparisonMixin[int]):
    """Instantiation of above mixin for int."""

    def parse_number(self, number: str) -> int:
        return int(number)


class DecimalComparisonMixin(ComparisonMixin[Decimal]):
    """Instantiation of above mixin for Decimal."""

    def parse_number(self, number: str) -> Decimal:
        return Decimal(number)


class OperatorSearchTerm(
    FilteringSearchTerm, ComparisonMixin[TNumber], metaclass=ABCMeta
):
    """Base class for all filters comparing some value against some number."""

    # Note that the additional "Any" param at the front is always "self".
    op: Callable[
        [Any, Comparable, Comparable], bool
    ]  # pylint: disable=invalid-name

    def __init__(self, operator: str, number: str):
        normal_operator = operator
        # Normalize operator such that "tags=5" and "tags:5"
        # have the same object hash and are treated identically.
        if normal_operator == ":":
            normal_operator = "="

        maybe_op = OPS.get(normal_operator, None)
        if not maybe_op:
            # Should never happen, programming error.
            raise Exception(f"Unknown operator in {self}")

        self.op = maybe_op  # type: ignore # pylint: disable=invalid-name
        self.operator_string = normal_operator

        self.number: TNumber = self.parse_number(number)


class CountingSearchTerm(OperatorSearchTerm[int], IntComparisonMixin):
    """Search term which simply counts innate tags."""

    def applies_to(self, medium: TinyMediumDocument) -> bool:
        # Note! Only count *innate* tags, not implications, aliases, etc...
        return self.op(len(medium.innate_tag_names), self.number)

    def __repr__(self) -> str:
        return f"tags{self.operator_string}{self.number}"


class CategorySearchTerm(OperatorSearchTerm[int], IntComparisonMixin):
    """Search term which counts innate tags of a specific category."""

    def __init__(self, category: str, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.category = category

    def applies_to(self, medium: TinyMediumDocument) -> bool:
        matching_tag_names = [
            t
            for t in medium.innate_tag_names
            if t.startswith(f"{self.category}:")
        ]

        return self.op(len(matching_tag_names), self.number)

    def __repr__(self) -> str:
        return f"{self.category}tags{self.operator_string}{self.number}"


class AgeSearchTerm(OperatorSearchTerm[int], IntComparisonMixin):
    """Search term which compares the medium's age against some period."""

    # This does lots of rounding, but it's close enough.
    DELTA_PER_PERIOD = {
        "w": timedelta(weeks=1),
        "d": timedelta(days=1),
        "m": timedelta(weeks=4),
        "y": timedelta(weeks=52),
    }

    def __init__(self, period: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.period = period[0]

    def applies_to(self, medium: TinyMediumDocument) -> bool:
        target_date = date.today() - (
            self.number * AgeSearchTerm.DELTA_PER_PERIOD[self.period]
        )
        return self.op(target_date, medium.insert_date)

    def __repr__(self) -> str:
        return f"age{self.operator_string}{self.number}{self.period}"


class FilesizeSearchTerm(OperatorSearchTerm[int], IntComparisonMixin):
    """Search term which compares the medium's filesize against some limit."""

    SIZE_PER_UNIT = {"k": 1024, "m": 1024 * 1024, "g": 1024 * 1024 * 1024}

    def __init__(self, unit: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.unit = unit[0].lower()

    def applies_to(self, medium: TinyMediumDocument) -> bool:
        target = self.number * FilesizeSearchTerm.SIZE_PER_UNIT[self.unit]
        return self.op(medium.filesize, target)

    def __repr__(self) -> str:
        return f"filesize{self.operator_string}{self.number}{self.unit}"


class DimensionSearchTerm(OperatorSearchTerm[int], IntComparisonMixin):
    """Search term which compares the medium's width/height against a number."""

    def __init__(self, dimension: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.dimension = dimension

    def applies_to(self, medium: TinyMediumDocument) -> bool:
        if self.dimension == "width":
            target = medium.width
        else:
            target = medium.height
        return self.op(target, self.number)

    def __repr__(self) -> str:
        return f"{self.dimension}{self.operator_string}{self.number}"


class AspectRatioSearchTerm(
    OperatorSearchTerm[Decimal], DecimalComparisonMixin
):
    """Search term which compares the aspect ratio against a decimal."""

    def applies_to(self, medium: TinyMediumDocument) -> bool:
        return self.op(medium.width / medium.height, self.number)

    def __repr__(self) -> str:
        return f"aspectratio{self.operator_string}{self.number}"
