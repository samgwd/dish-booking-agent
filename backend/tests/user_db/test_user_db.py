"""Tests for database session management in the user_db.user_db module."""

from __future__ import annotations

import sys
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest


class TestDatabaseUrlConfiguration:
    """Tests for DATABASE_URL environment variable handling."""

    def test_raises_runtime_error_without_database_url(self) -> None:
        """Raises RuntimeError when DATABASE_URL is not set during module load."""
        modules_to_remove = [key for key in sys.modules if key.startswith("src.user_db")]
        for mod in modules_to_remove:
            del sys.modules[mod]

        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(RuntimeError) as exc_info,
        ):
            from src.user_db import user_db  # noqa: F401

        assert "DATABASE_URL is not set" in str(exc_info.value)


class TestSessionScope:
    """Tests for the session_scope context manager."""

    @pytest.fixture
    def mock_session_local(
        self, env_with_database_url: dict[str, str]
    ) -> Generator[MagicMock, None, None]:
        """Set up mocked SessionLocal for testing session_scope."""
        modules_to_remove = [key for key in sys.modules if key.startswith("src.user_db")]
        for mod in modules_to_remove:
            del sys.modules[mod]

        with (
            patch.dict("os.environ", env_with_database_url, clear=True),
            patch("sqlalchemy.create_engine"),
        ):
            mock_session = MagicMock()
            mock_session_local_class = MagicMock(return_value=mock_session)

            with patch("sqlalchemy.orm.sessionmaker", return_value=mock_session_local_class):
                from src.user_db import user_db

                original_session_local = user_db.SessionLocal
                user_db.SessionLocal = mock_session_local_class

                yield mock_session

                user_db.SessionLocal = original_session_local

    def test_yields_session_instance(
        self, mock_session_local: MagicMock, env_with_database_url: dict[str, str]
    ) -> None:
        """Yields a Session instance within the context."""
        from src.user_db.user_db import session_scope

        with session_scope() as session:
            result = session

        assert result is mock_session_local

    def test_commits_on_success(
        self, mock_session_local: MagicMock, env_with_database_url: dict[str, str]
    ) -> None:
        """Commits the session when context exits normally."""
        from src.user_db.user_db import session_scope

        with session_scope():
            pass

        mock_session_local.commit.assert_called_once()

    def test_rollback_on_exception(
        self, mock_session_local: MagicMock, env_with_database_url: dict[str, str]
    ) -> None:
        """Rolls back the session when an exception occurs."""
        from src.user_db.user_db import session_scope

        with pytest.raises(ValueError), session_scope():
            raise ValueError("Test error")

        mock_session_local.rollback.assert_called_once()
        mock_session_local.commit.assert_not_called()

    def test_closes_session_on_success(
        self, mock_session_local: MagicMock, env_with_database_url: dict[str, str]
    ) -> None:
        """Closes the session when context exits normally."""
        from src.user_db.user_db import session_scope

        with session_scope():
            pass

        mock_session_local.close.assert_called_once()

    def test_closes_session_on_exception(
        self, mock_session_local: MagicMock, env_with_database_url: dict[str, str]
    ) -> None:
        """Closes the session even when an exception occurs."""
        from src.user_db.user_db import session_scope

        with pytest.raises(ValueError), session_scope():
            raise ValueError("Test error")

        mock_session_local.close.assert_called_once()

    def test_re_raises_original_exception(
        self, mock_session_local: MagicMock, env_with_database_url: dict[str, str]
    ) -> None:
        """Re-raises the original exception after rollback."""
        from src.user_db.user_db import session_scope

        with pytest.raises(ValueError) as exc_info, session_scope():
            raise ValueError("Original error message")

        assert "Original error message" in str(exc_info.value)


class TestBase:
    """Tests for the Base declarative base class."""

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

    def test_base_is_declarative_base(self) -> None:
        """Base class is a SQLAlchemy DeclarativeBase subclass."""
        from sqlalchemy.orm import DeclarativeBase
        from src.user_db.user_db import Base

        assert issubclass(Base, DeclarativeBase)
