from typing import Optional, Tuple

from sqlalchemy import select

from beevenue.flask import g

from .models import User


def connect_google_account(
    username: str, google_id: str
) -> Tuple[bool, Optional[str]]:
    session = g.db

    maybe_user = (
        session.execute(select(User).filter(User.username == username))
        .scalars()
        .first()
    )

    if maybe_user.google_id is None:
        maybe_user.google_id = google_id
        session.commit()
        return (True, None)

    if maybe_user.google_id == google_id:
        return (
            False,
            "This Google account is already connected.",
        )

    return (
        False,
        "This Google account is already connected to another Beevenue account.",
    )
