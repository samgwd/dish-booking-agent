"""Tests for encryption utilities in the user_db.secrets module."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet, InvalidToken
from src.user_db.secrets import (
    _get_fernet,
    decrypt_secret,
    encrypt_secret,
    generate_encryption_key,
)

UNIQUE_KEY_TEST_COUNT = 10
FERNET_KEY_LENGTH = 44


class TestGetFernet:
    """Tests for the _get_fernet function."""

    def test_returns_fernet_instance_with_valid_key(
        self, env_with_encryption_key: dict[str, str]
    ) -> None:
        """Returns a Fernet instance when SECRETS_ENCRYPTION_KEY is set."""
        _get_fernet.cache_clear()

        with patch.dict("os.environ", env_with_encryption_key, clear=True):
            result = _get_fernet()

        assert isinstance(result, Fernet)

    def test_raises_runtime_error_without_key(self) -> None:
        """Raises RuntimeError when SECRETS_ENCRYPTION_KEY is not set."""
        _get_fernet.cache_clear()

        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(RuntimeError) as exc_info,
        ):
            _get_fernet()

        assert "SECRETS_ENCRYPTION_KEY is not set" in str(exc_info.value)

    def test_caches_fernet_instance(self, env_with_encryption_key: dict[str, str]) -> None:
        """Caches the Fernet instance after first call."""
        _get_fernet.cache_clear()

        with patch.dict("os.environ", env_with_encryption_key, clear=True):
            first_call = _get_fernet()
            second_call = _get_fernet()

        assert first_call is second_call

    def test_raises_value_error_for_invalid_key(self) -> None:
        """Raises ValueError when key is not a valid Fernet key."""
        _get_fernet.cache_clear()

        with (
            patch.dict("os.environ", {"SECRETS_ENCRYPTION_KEY": "invalid-key"}, clear=True),
            pytest.raises(ValueError),
        ):
            _get_fernet()


class TestEncryptSecret:
    """Tests for the encrypt_secret function."""

    def test_encrypts_plaintext_string(self, env_with_encryption_key: dict[str, str]) -> None:
        """Encrypts a plaintext string to bytes."""
        _get_fernet.cache_clear()

        with patch.dict("os.environ", env_with_encryption_key, clear=True):
            result = encrypt_secret("my-secret-value")

        assert isinstance(result, bytes)
        assert result != b"my-secret-value"

    def test_produces_different_ciphertext_each_time(
        self, env_with_encryption_key: dict[str, str]
    ) -> None:
        """Produces different ciphertext for the same plaintext due to random IV."""
        _get_fernet.cache_clear()

        with patch.dict("os.environ", env_with_encryption_key, clear=True):
            first_encryption = encrypt_secret("same-secret")
            second_encryption = encrypt_secret("same-secret")

        assert first_encryption != second_encryption

    def test_encrypts_empty_string(self, env_with_encryption_key: dict[str, str]) -> None:
        """Encrypts an empty string successfully."""
        _get_fernet.cache_clear()

        with patch.dict("os.environ", env_with_encryption_key, clear=True):
            result = encrypt_secret("")

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_encrypts_unicode_characters(self, env_with_encryption_key: dict[str, str]) -> None:
        """Encrypts strings with unicode characters."""
        _get_fernet.cache_clear()

        with patch.dict("os.environ", env_with_encryption_key, clear=True):
            result = encrypt_secret("password🔐with💪special🎉chars")

        assert isinstance(result, bytes)

    def test_encrypts_long_string(self, env_with_encryption_key: dict[str, str]) -> None:
        """Encrypts a long string successfully."""
        _get_fernet.cache_clear()
        long_secret = "x" * 10000

        with patch.dict("os.environ", env_with_encryption_key, clear=True):
            result = encrypt_secret(long_secret)

        assert isinstance(result, bytes)


class TestDecryptSecret:
    """Tests for the decrypt_secret function."""

    def test_decrypts_encrypted_value(self, env_with_encryption_key: dict[str, str]) -> None:
        """Decrypts an encrypted value back to original plaintext."""
        _get_fernet.cache_clear()
        original = "my-secret-value"

        with patch.dict("os.environ", env_with_encryption_key, clear=True):
            encrypted = encrypt_secret(original)
            result = decrypt_secret(encrypted)

        assert result == original

    def test_decrypts_empty_string(self, env_with_encryption_key: dict[str, str]) -> None:
        """Decrypts an encrypted empty string."""
        _get_fernet.cache_clear()

        with patch.dict("os.environ", env_with_encryption_key, clear=True):
            encrypted = encrypt_secret("")
            result = decrypt_secret(encrypted)

        assert result == ""

    def test_decrypts_unicode_characters(self, env_with_encryption_key: dict[str, str]) -> None:
        """Decrypts strings with unicode characters."""
        _get_fernet.cache_clear()
        original = "password🔐with💪special🎉chars"

        with patch.dict("os.environ", env_with_encryption_key, clear=True):
            encrypted = encrypt_secret(original)
            result = decrypt_secret(encrypted)

        assert result == original

    def test_raises_invalid_token_for_corrupted_data(
        self, env_with_encryption_key: dict[str, str]
    ) -> None:
        """Raises InvalidToken when encrypted data is corrupted."""
        _get_fernet.cache_clear()

        with (
            patch.dict("os.environ", env_with_encryption_key, clear=True),
            pytest.raises(InvalidToken),
        ):
            decrypt_secret(b"corrupted-data")

    def test_raises_invalid_token_for_wrong_key(self, sample_encryption_key: str) -> None:
        """Raises InvalidToken when decrypting with a different key."""
        _get_fernet.cache_clear()
        different_key = Fernet.generate_key().decode()

        with patch.dict(
            "os.environ", {"SECRETS_ENCRYPTION_KEY": sample_encryption_key}, clear=True
        ):
            encrypted = encrypt_secret("secret")

        _get_fernet.cache_clear()

        with (
            patch.dict("os.environ", {"SECRETS_ENCRYPTION_KEY": different_key}, clear=True),
            pytest.raises(InvalidToken),
        ):
            decrypt_secret(encrypted)

    def test_decrypts_long_string(self, env_with_encryption_key: dict[str, str]) -> None:
        """Decrypts a long string successfully."""
        _get_fernet.cache_clear()
        long_secret = "x" * 10000

        with patch.dict("os.environ", env_with_encryption_key, clear=True):
            encrypted = encrypt_secret(long_secret)
            result = decrypt_secret(encrypted)

        assert result == long_secret


class TestGenerateEncryptionKey:
    """Tests for the generate_encryption_key function."""

    def test_returns_string(self) -> None:
        """Returns a string key."""
        result = generate_encryption_key()

        assert isinstance(result, str)

    def test_returns_valid_fernet_key(self) -> None:
        """Returns a key that can be used to create a Fernet instance."""
        key = generate_encryption_key()

        fernet = Fernet(key.encode())

        assert isinstance(fernet, Fernet)

    def test_generates_unique_keys(self) -> None:
        """Generates unique keys on each call."""
        keys = [generate_encryption_key() for _ in range(UNIQUE_KEY_TEST_COUNT)]

        assert len(set(keys)) == UNIQUE_KEY_TEST_COUNT

    def test_key_is_base64_encoded(self) -> None:
        """Generated key is base64 encoded."""
        key = generate_encryption_key()

        assert len(key) == FERNET_KEY_LENGTH
        assert key.endswith("=")
