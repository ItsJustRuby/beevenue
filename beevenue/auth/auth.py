from typing import Optional

from flask import session

from ..login_manager import login_manager
from .logged_in_user import LoggedInUser


def init() -> None:
    """Initialize auth component of application."""

    def user_loader(
        username: str,
    ) -> Optional[LoggedInUser]:
        """Try to load user with specified username."""
        if "role" not in session:
            return None

        return LoggedInUser(username, session["role"])

    login_manager.user_loader(user_loader)
