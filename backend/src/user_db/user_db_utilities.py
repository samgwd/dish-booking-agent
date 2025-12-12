"""User database utilities."""

from __future__ import annotations

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


def _coerce_user_id(user_id: str | uuid.UUID) -> uuid.UUID:
    """Coerce a user id into a UUID.

    Args:
        user_id: The user ID as a UUID or UUID string.

    Returns:
        The parsed UUID.
    """
    return user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(user_id)


def logout_user(user_id: str | uuid.UUID) -> bool:
    """Log out a user by marking them inactive.

    IMPORTANT: This function intentionally re-fetches the user within the current session
    to avoid "detached instance" updates silently not persisting.

    Args:
        user_id: The user ID as a UUID or UUID string.

    Returns:
        True if the user existed and was updated, otherwise False.
    """
    user_uuid = _coerce_user_id(user_id)
    with session_scope() as session:
        db_user = session.get(models.User, user_uuid)
        if db_user is None:
            return False
        db_user.is_active = False
        return True


def delete_user(user_id: str | uuid.UUID) -> bool:
    """Delete a user by ID.

    IMPORTANT: This function re-fetches the user within the current session so the delete
    is tracked and persisted.

    Args:
        user_id: The user ID as a UUID or UUID string.

    Returns:
        True if the user existed and was deleted, otherwise False.
    """
    user_uuid = _coerce_user_id(user_id)
    with session_scope() as session:
        db_user = session.get(models.User, user_uuid)
        if db_user is None:
            return False
        session.delete(db_user)
        return True


def get_user_by_email(email: str) -> models.User | None:
    """Get a user by email.

    Args:
        email: The email of the user.

    Returns:
        The user if found, None otherwise.
    """
    with session_scope() as session:
        return session.scalar(select(models.User).where(models.User.email == email))


def get_user_by_id(user_id: str | uuid.UUID) -> models.User | None:
    """Get a user by ID.

    Args:
        user_id: The ID of the user (UUID or UUID string).

    Returns:
        The user if found, None otherwise.
    """
    user_uuid = _coerce_user_id(user_id)
    with session_scope() as session:
        return session.scalar(select(models.User).where(models.User.id == user_uuid))
