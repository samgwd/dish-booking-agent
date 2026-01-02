"""Shared fixtures for user_db package tests."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from cryptography.fernet import Fernet


@pytest.fixture
def sample_user_id() -> uuid.UUID:
    """Create a sample UUID for testing."""
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_user_id_str() -> str:
    """Create a sample UUID string for testing."""
    return "12345678-1234-5678-1234-567812345678"


@pytest.fixture
def sample_email() -> str:
    """Create a sample email for testing."""
    return "test@example.com"


@pytest.fixture
def sample_encryption_key() -> str:
    """Create a valid Fernet encryption key for testing."""
    return Fernet.generate_key().decode()


@pytest.fixture
def mock_session() -> Generator[MagicMock, None, None]:
    """Create a mock SQLAlchemy session."""
    session = MagicMock()
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=False)
    yield session


@pytest.fixture
def mock_user(sample_user_id: uuid.UUID, sample_email: str) -> MagicMock:
    """Create a mock User object."""
    user = MagicMock()
    user.id = sample_user_id
    user.email = sample_email
    user.is_active = True
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def mock_user_secret(sample_user_id: uuid.UUID) -> MagicMock:
    """Create a mock UserSecret object."""
    secret = MagicMock()
    secret.id = uuid.uuid4()
    secret.user_id = sample_user_id
    secret.key = "TEST_SECRET"
    secret.encrypted_value = b"encrypted_data"
    secret.created_at = datetime.now(timezone.utc)
    secret.updated_at = datetime.now(timezone.utc)
    return secret


@pytest.fixture
def sample_secret_keys() -> list[str]:
    """Create sample secret key names for testing."""
    return ["DISH_COOKIE", "API_KEY", "OTHER_SECRET"]


@pytest.fixture
def env_with_encryption_key(sample_encryption_key: str) -> dict[str, str]:
    """Create environment variables dict with encryption key."""
    return {"SECRETS_ENCRYPTION_KEY": sample_encryption_key}


@pytest.fixture
def env_with_database_url() -> dict[str, str]:
    """Create environment variables dict with database URL."""
    return {"DATABASE_URL": "postgresql://user:pass@localhost:5432/testdb"}
