"""Tests for database models in the user_db.models module."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest


class TestUtcnow:
    """Tests for the utcnow helper function."""

    @pytest.fixture(autouse=True)
    def setup_env(self, env_with_database_url: dict[str, str]) -> None:
        """Set up environment variables for model imports."""
        with (
            patch.dict("os.environ", env_with_database_url, clear=True),
            patch("src.user_db.user_db.create_engine"),
        ):
            import importlib

            import src.user_db.user_db as user_db_module

            importlib.reload(user_db_module)

    def test_returns_datetime(self) -> None:
        """Returns a datetime object."""
        from src.user_db.models import utcnow

        result = utcnow()

        assert isinstance(result, datetime)

    def test_returns_utc_timezone(self) -> None:
        """Returns datetime with UTC timezone."""
        from src.user_db.models import utcnow

        result = utcnow()

        assert result.tzinfo == timezone.utc

    def test_returns_current_time(self) -> None:
        """Returns approximately the current time."""
        from src.user_db.models import utcnow

        before = datetime.now(timezone.utc)
        result = utcnow()
        after = datetime.now(timezone.utc)

        assert before <= result <= after


class TestUserModel:
    """Tests for the User model class."""

    @pytest.fixture(autouse=True)
    def setup_env(self, env_with_database_url: dict[str, str]) -> None:
        """Set up environment variables for model imports."""
        with (
            patch.dict("os.environ", env_with_database_url, clear=True),
            patch("src.user_db.user_db.create_engine"),
        ):
            import importlib

            import src.user_db.user_db as user_db_module

            importlib.reload(user_db_module)

    def test_tablename_is_users(self) -> None:
        """User model uses 'users' as table name."""
        from src.user_db.models import User

        assert User.__tablename__ == "users"

    def test_id_column_is_uuid(self) -> None:
        """User id column is UUID type."""
        from src.user_db.models import User

        id_column = User.__table__.columns["id"]

        assert str(id_column.type) == "UUID"

    def test_id_column_is_primary_key(self) -> None:
        """User id column is primary key."""
        from src.user_db.models import User

        id_column = User.__table__.columns["id"]

        assert id_column.primary_key is True

    def test_email_column_is_unique(self) -> None:
        """User email column has unique constraint."""
        from src.user_db.models import User

        email_column = User.__table__.columns["email"]

        assert email_column.unique is True

    def test_email_column_is_not_nullable(self) -> None:
        """User email column is not nullable."""
        from src.user_db.models import User

        email_column = User.__table__.columns["email"]

        assert email_column.nullable is False

    def test_email_column_is_indexed(self) -> None:
        """User email column has index."""
        from src.user_db.models import User

        email_column = User.__table__.columns["email"]

        assert email_column.index is True

    def test_is_active_column_defaults_to_true(self) -> None:
        """User is_active column defaults to True."""
        from src.user_db.models import User

        is_active_column = User.__table__.columns["is_active"]

        assert is_active_column.default.arg is True

    def test_is_active_column_is_not_nullable(self) -> None:
        """User is_active column is not nullable."""
        from src.user_db.models import User

        is_active_column = User.__table__.columns["is_active"]

        assert is_active_column.nullable is False

    def test_created_at_column_is_not_nullable(self) -> None:
        """User created_at column is not nullable."""
        from src.user_db.models import User

        created_at_column = User.__table__.columns["created_at"]

        assert created_at_column.nullable is False


class TestUserSecretModel:
    """Tests for the UserSecret model class."""

    @pytest.fixture(autouse=True)
    def setup_env(self, env_with_database_url: dict[str, str]) -> None:
        """Set up environment variables for model imports."""
        with (
            patch.dict("os.environ", env_with_database_url, clear=True),
            patch("src.user_db.user_db.create_engine"),
        ):
            import importlib

            import src.user_db.user_db as user_db_module

            importlib.reload(user_db_module)

    def test_tablename_is_user_secrets(self) -> None:
        """UserSecret model uses 'user_secrets' as table name."""
        from src.user_db.models import UserSecret

        assert UserSecret.__tablename__ == "user_secrets"

    def test_id_column_is_uuid(self) -> None:
        """UserSecret id column is UUID type."""
        from src.user_db.models import UserSecret

        id_column = UserSecret.__table__.columns["id"]

        assert str(id_column.type) == "UUID"

    def test_id_column_is_primary_key(self) -> None:
        """UserSecret id column is primary key."""
        from src.user_db.models import UserSecret

        id_column = UserSecret.__table__.columns["id"]

        assert id_column.primary_key is True

    def test_user_id_column_is_uuid(self) -> None:
        """UserSecret user_id column is UUID type."""
        from src.user_db.models import UserSecret

        user_id_column = UserSecret.__table__.columns["user_id"]

        assert str(user_id_column.type) == "UUID"

    def test_user_id_column_is_not_nullable(self) -> None:
        """UserSecret user_id column is not nullable."""
        from src.user_db.models import UserSecret

        user_id_column = UserSecret.__table__.columns["user_id"]

        assert user_id_column.nullable is False

    def test_user_id_column_is_indexed(self) -> None:
        """UserSecret user_id column has index."""
        from src.user_db.models import UserSecret

        user_id_column = UserSecret.__table__.columns["user_id"]

        assert user_id_column.index is True

    def test_user_id_has_foreign_key_to_users(self) -> None:
        """UserSecret user_id has foreign key to users table."""
        from src.user_db.models import UserSecret

        user_id_column = UserSecret.__table__.columns["user_id"]
        fk = list(user_id_column.foreign_keys)[0]

        assert fk.target_fullname == "users.id"

    def test_user_id_has_cascade_delete(self) -> None:
        """UserSecret user_id foreign key has CASCADE delete."""
        from src.user_db.models import UserSecret

        user_id_column = UserSecret.__table__.columns["user_id"]
        fk = list(user_id_column.foreign_keys)[0]

        assert fk.ondelete == "CASCADE"

    def test_key_column_is_not_nullable(self) -> None:
        """UserSecret key column is not nullable."""
        from src.user_db.models import UserSecret

        key_column = UserSecret.__table__.columns["key"]

        assert key_column.nullable is False

    def test_encrypted_value_column_is_not_nullable(self) -> None:
        """UserSecret encrypted_value column is not nullable."""
        from src.user_db.models import UserSecret

        encrypted_value_column = UserSecret.__table__.columns["encrypted_value"]

        assert encrypted_value_column.nullable is False

    def test_encrypted_value_column_is_binary_type(self) -> None:
        """UserSecret encrypted_value column is binary type (LargeBinary)."""
        from sqlalchemy import LargeBinary
        from src.user_db.models import UserSecret

        encrypted_value_column = UserSecret.__table__.columns["encrypted_value"]

        assert isinstance(encrypted_value_column.type, LargeBinary)

    def test_created_at_column_is_not_nullable(self) -> None:
        """UserSecret created_at column is not nullable."""
        from src.user_db.models import UserSecret

        created_at_column = UserSecret.__table__.columns["created_at"]

        assert created_at_column.nullable is False

    def test_updated_at_column_is_not_nullable(self) -> None:
        """UserSecret updated_at column is not nullable."""
        from src.user_db.models import UserSecret

        updated_at_column = UserSecret.__table__.columns["updated_at"]

        assert updated_at_column.nullable is False

    def test_has_unique_constraint_on_user_id_and_key(self) -> None:
        """UserSecret has unique constraint on user_id and key combination."""
        from sqlalchemy import Table, UniqueConstraint
        from src.user_db.models import UserSecret

        table: Table = UserSecret.__table__  # type: ignore[assignment]
        constraints = [c for c in table.constraints if c.name == "uq_user_secrets_user_id_key"]

        assert len(constraints) == 1
        constraint = constraints[0]
        assert isinstance(constraint, UniqueConstraint)
        column_names = [col.name for col in constraint.columns]
        assert "user_id" in column_names
        assert "key" in column_names
