"""User database utilities."""

import uuid

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


def create_user(email: str, password: str) -> models.User:
    """Create a new user.

    Args:
        email: The email of the user.
        password: The password of the user.

    Returns:
        The created user.
    """
    with session_scope() as session:
        user = models.User(email=email, password_hash=hash_password(password))
        session.add(user)
        session.flush()
        return user


def logout_user(user: models.User) -> None:
    """Logout a user.

    Args:
        user: The user to logout.
    """
    with session_scope() as session:
        user.is_active = False
        session.commit()


def delete_user(user: models.User) -> None:
    """Delete a user.

    Args:
        user: The user to delete.
    """
    with session_scope() as session:
        session.delete(user)
        session.commit()


def get_user_by_email(email: str) -> models.User | None:
    """Get a user by email.

    Args:
        email: The email of the user.

    Returns:
        The user if found, None otherwise.
    """
    with session_scope() as session:
        return session.scalar(select(models.User).where(models.User.email == email))


def get_user_by_id(user_id: str) -> models.User | None:
    """Get a user by ID.

    Args:
        user_id: The ID of the user (UUID string).

    Returns:
        The user if found, None otherwise.
    """
    with session_scope() as session:
        return session.scalar(select(models.User).where(models.User.id == uuid.UUID(user_id)))
