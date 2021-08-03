from abc import ABC, abstractmethod
import os
from typing import Any, Dict, List

import capnp  # type: ignore

from beevenue.documents import IndexedMedium, TinyIndexedMedium
from beevenue.document_types import MediumDocument, TinyMediumDocument

from ..types import CacheEntityKind


def _camel_case(string: str) -> str:
    parts = string.split("_")
    return "".join([parts[0], *[p.title() for p in parts[1:]]])


def _path(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), filename)


MDT_SCHEMA = capnp.load(  # pylint: disable=no-member
    _path("medium_document_tiny.capnp")
)
MDTA_SCHEMA = capnp.load(  # pylint: disable=no-member
    _path("medium_document_tiny_all.capnp")
)
MD_SCHEMA = capnp.load(  # pylint: disable=no-member
    _path("medium_document.capnp")
)
LISTS_SCHEMA = capnp.load(_path("lists.capnp"))  # pylint: disable=no-member


class Schema(ABC):
    """Base class for all schemas used for (de)serialization."""

    @abstractmethod
    def serialize(self, obj: Any) -> bytes:
        """Take an object, encode it as bytes."""

    @abstractmethod
    def deserialize(self, raw_bytes: bytes) -> Any:
        """Take some bytes, get an object back out."""


TBase = Any
TSerializable = Any


class CapnpSchema(Schema):
    """Base class for Cap'n Proto based schemas."""

    SIMPLE: List[str] = []
    LISTS: List[str] = []

    @property
    @abstractmethod
    def target(self) -> TBase:
        """Base on which to create new document using Capnp."""

    @abstractmethod
    def construct_object(self, doc: TBase) -> Any:
        """Take 'obj' in schema form and make a Python object out of it."""

    def construct_document(self, base: TBase, obj: TSerializable) -> None:
        for key in self.__class__.SIMPLE:
            self._construct_simple(base, obj, key)

        for field in self.__class__.LISTS:
            self._construct_list(base, obj, field)

    def _construct_simple(
        self, base: TBase, obj: TSerializable, key: str
    ) -> None:
        value = getattr(obj, key)
        setattr(base, _camel_case(key), value)

    def _construct_list(
        self, base: TBase, obj: TSerializable, key: str
    ) -> None:
        attribute = getattr(obj, key)
        field = base.init(_camel_case(key), len(attribute))
        i = 0
        for part in attribute:
            field[i] = part
            i += 1

    def serialize(self, obj: Any) -> bytes:
        document = self.target.new_message()
        self.construct_document(document, obj)
        result: bytes = document.to_bytes()
        return result

    def deserialize(self, raw_bytes: bytes) -> Any:
        obj: TBase = self.target.from_bytes(raw_bytes)
        return self.construct_object(obj)


class FullMediumDocumentSchema(CapnpSchema):
    """Cap'n Proto based schema for MediumDocument."""

    SIMPLE = [
        "medium_id",
        "medium_hash",
        "mime_type",
        "rating",
        "tiny_thumbnail",
    ]

    LISTS = [
        "absent_tag_names",
        "innate_tag_names",
        "searchable_tag_names",
    ]

    @property
    def target(self) -> TBase:
        return MD_SCHEMA.MediumDocument

    def construct_object(self, doc: Any) -> MediumDocument:
        return IndexedMedium(
            doc.mediumId,
            doc.mediumHash,
            doc.mimeType,
            doc.rating,
            doc.tinyThumbnail,
            frozenset(doc.innateTagNames),
            frozenset(doc.searchableTagNames),
            frozenset(doc.absentTagNames),
        )


class TinyMediumDocumentSchema(CapnpSchema):
    """Cap'n Proto based schema for TinyMediumDocument."""

    SIMPLE = [
        "medium_id",
        "medium_hash",
        "rating",
    ]

    LISTS = [
        "absent_tag_names",
        "innate_tag_names",
        "searchable_tag_names",
    ]

    @property
    def target(self) -> Any:
        return MDT_SCHEMA.MediumDocumentTiny

    def construct_object(self, doc: Any) -> TinyMediumDocument:
        return TinyIndexedMedium(
            doc.mediumId,
            doc.mediumHash,
            doc.rating,
            frozenset(doc.innateTagNames),
            frozenset(doc.searchableTagNames),
            frozenset(doc.absentTagNames),
        )


# Note: This isn't actually all that generic
class AllMetaSchema(CapnpSchema):
    """Cap'n Proto based schema for Lists of TinyMediumDocuments."""

    def __init__(self, wrapped_schema: CapnpSchema):
        self.wrapped_schema = wrapped_schema

    @property
    def target(self) -> Any:
        return MDTA_SCHEMA.AllMediumDocumentTiny

    def serialize(self, obj: List[Any]) -> bytes:
        document = self.target.new_message()
        field = document.init("all", len(obj))
        i = 0
        for subdocument in obj:
            self.wrapped_schema.construct_document(field[i], subdocument)
            i += 1

        result: bytes = document.to_bytes()
        return result

    def construct_object(self, doc: Any) -> List[Any]:
        return [self.wrapped_schema.construct_object(obj) for obj in doc.all]


class StringListSchema(CapnpSchema):
    """Cap'n Proto based schema for simle string lists."""

    @property
    def target(self) -> Any:
        return LISTS_SCHEMA.StringList

    def construct_object(self, doc: Any) -> Any:
        return doc.strings

    def construct_document(self, base: Any, obj: List[str]) -> None:
        field = base.init("strings", len(obj))
        i = 0
        for string in obj:
            field[i] = string
            i += 1


class AsciiStringSchema(Schema):
    """Simple schema for single ASCII string."""

    def serialize(self, obj: str) -> bytes:
        return obj.encode("ascii")

    def deserialize(self, raw_bytes: bytes) -> str:
        return raw_bytes.decode("ascii")


_FULL_MEDIUM_DOCUMENT_SCHEMA = FullMediumDocumentSchema()
_TINY_MEDIUM_DOCUMENT_SCHEMA = TinyMediumDocumentSchema()
_RATING_BY_HASH_SCHEMA = AsciiStringSchema()

_ALL_TINY_MEDIUM_DOCUMENT_SCHEMA = AllMetaSchema(_TINY_MEDIUM_DOCUMENT_SCHEMA)

_STRING_LIST_SCHEMA = StringListSchema()

SCHEMAS: Dict[CacheEntityKind, Schema] = {
    CacheEntityKind.MEDIUM_DOCUMENT: _FULL_MEDIUM_DOCUMENT_SCHEMA,
    CacheEntityKind.MEDIUM_DOCUMENT_TINY: _TINY_MEDIUM_DOCUMENT_SCHEMA,
    CacheEntityKind.MEDIUM_DOCUMENT_TINY_ALL: _ALL_TINY_MEDIUM_DOCUMENT_SCHEMA,
    CacheEntityKind.RATING_BY_HASH: _RATING_BY_HASH_SCHEMA,
    CacheEntityKind.SEARCHABLE_TAGS: _STRING_LIST_SCHEMA,
}
