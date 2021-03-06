# pylint: disable=missing-class-docstring
from ..db import db


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(length=256), unique=True, nullable=False)
    hash = db.Column(db.String(length=256), nullable=False)
    role = db.Column(db.String(length=256), nullable=False)
    google_id = db.Column(db.String(length=256), nullable=True)
