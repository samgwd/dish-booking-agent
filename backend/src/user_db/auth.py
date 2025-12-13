"""Authentication utilities."""

import bcrypt
from sqlalchemy import select

from src.user_db import models
from src.user_db.user_db import session_scope


def hash_password(password: str, rounds: int = 12) -> str:
    """Hash a password with bcrypt (adjust rounds for cost).

    Args:
        password: The password to hash.
        rounds: The number of rounds to use for the hash.

    Returns:
        The hashed password.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds)).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hashed password.

    Args:
        password: The password to verify.
        hashed: The hashed password to verify against.

    Returns:
        True if the password is verified, False otherwise.
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def authenticate(email: str, password: str) -> models.User | None:
    """Authenticate a user.

    Args:
        email: The email of the user.
        password: The password of the user.

    Returns:
        The authenticated user if successful, None otherwise.
    """
    with session_scope() as session:
        user = session.scalar(select(models.User).where(models.User.email == email))
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
