from beevenue.strawberry.violations import FixKind, QuickFix
from typing import List, NamedTuple
from marshmallow import fields

from marshmallow.schema import Schema


class FixViewModel(NamedTuple):
    """JSON serialization viewmodel."""

    kind: FixKind
    tag: str


def fix_view_model(fix: QuickFix) -> FixViewModel:
    return FixViewModel(*fix.serialize())


class ViolationViewModel(NamedTuple):
    """JSON serialization viewmodel."""

    text: str
    fixes: List[FixViewModel]


class ViolationsViewModel(NamedTuple):
    """JSON serialization viewmodel."""

    violations: List[ViolationViewModel]


class _FixSchema(Schema):
    kind = fields.String()
    tag = fields.String()


class _ViolationSchema(Schema):
    text = fields.String()
    fixes = fields.Nested(_FixSchema, many=True)


class _ViolationsSchema(Schema):
    violations = fields.Nested(_ViolationSchema, many=True)


VIOLATIONS_SCHEMA = _ViolationsSchema()
