# pylint: disable=missing-class-docstring
from typing import List, Optional

from .db import db


class TagImplication(db.Model):
    __tablename__ = "tagImplication"
    implying_tag_id = db.Column(
        db.Integer,
        db.ForeignKey("tag.id"),
        index=True,
        primary_key=True,
        nullable=False,
    )
    implied_tag_id = db.Column(
        db.Integer,
        db.ForeignKey("tag.id"),
        index=True,
        primary_key=True,
        nullable=False,
    )


class Tag(db.Model):
    __tablename__ = "tag"
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(length=256), unique=True, nullable=False)
    rating = db.Column(
        db.Enum("e", "s", "q", "u", name="Rating"), nullable=False
    )

    aliases = db.relationship("TagAlias", back_populates="tag", lazy="raise")

    implying_this = db.relationship(
        "Tag",
        secondary=TagImplication.__tablename__,
        primaryjoin=id == TagImplication.implied_tag_id,
        secondaryjoin=id == TagImplication.implying_tag_id,
        lazy="raise",
        back_populates="implied_by_this",
    )

    implied_by_this = db.relationship(
        "Tag",
        secondary=TagImplication.__tablename__,
        primaryjoin=id == TagImplication.implying_tag_id,
        secondaryjoin=id == TagImplication.implied_tag_id,
        lazy="raise",
        back_populates="implying_this",
    )

    def __init__(self, tag: str):
        self.tag = tag
        self.rating = "u"

    @staticmethod
    def create(tag: str) -> Optional["Tag"]:
        clean_tag = tag.strip()
        if clean_tag:
            return Tag(clean_tag)
        return None


class TagAlias(db.Model):
    __tablename__ = "tagAlias"
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(
        db.Integer, db.ForeignKey("tag.id"), index=True, nullable=False
    )
    alias = db.Column(db.String(length=256), unique=True, nullable=False)

    tag = db.relationship(Tag, lazy="raise")

    def __init__(self, tag_id: int, alias: str):
        self.tag_id = tag_id
        self.alias = alias


class MediumTag(db.Model):
    __tablename__ = "medium_tag"
    medium_id = db.Column(
        db.Integer,
        db.ForeignKey("medium.id"),
        index=True,
        primary_key=True,
        nullable=False,
    )
    tag_id = db.Column(
        db.Integer,
        db.ForeignKey("tag.id"),
        index=True,
        primary_key=True,
        nullable=False,
    )


class MediumTagAbsence(db.Model):
    __tablename__ = "mediumTagAbsence"
    id = db.Column(db.Integer, primary_key=True)
    medium_id = db.Column(
        db.Integer, db.ForeignKey("medium.id"), index=True, nullable=False
    )
    tag_id = db.Column(
        db.Integer, db.ForeignKey("tag.id"), index=True, nullable=False
    )

    __table_args__ = (db.UniqueConstraint("medium_id", "tag_id"),)


class Medium(db.Model):
    __tablename__ = "medium"
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(length=32), unique=True, nullable=False)
    mime_type = db.Column(db.String(length=256), nullable=False)
    aspect_ratio = db.Column(db.Numeric(precision=4, scale=2), nullable=True)
    rating = db.Column(
        db.Enum("e", "s", "q", "u", name="Rating"), nullable=False
    )

    tiny_thumbnail = db.Column(db.LargeBinary(), nullable=True)

    tags = db.relationship(
        "Tag",
        secondary=MediumTag.__tablename__,
        lazy="raise",
        backref=db.backref("media", lazy="raise"),
    )

    absent_tags = db.relationship(
        "Tag",
        secondary=MediumTagAbsence.__tablename__,
        lazy="raise",
    )

    def __init__(
        self,
        medium_hash: str,
        mime_type: str,
        rating: str = "u",
        tags: List[Tag] = None,
        absent_tags: List[Tag] = None,
        aspect_ratio: Optional[float] = None,
    ):
        self.rating = rating
        self.mime_type = mime_type
        self.hash = medium_hash
        self.tags = tags or []
        self.absent_tags = absent_tags or []
        self.aspect_ratio = aspect_ratio
