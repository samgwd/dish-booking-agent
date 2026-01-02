"""Encryption utilities for user secrets."""

from __future__ import annotations

import os
from functools import lru_cache

from cryptography.fernet import Fernet


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    """Get or create the Fernet instance (cached after first call).

    Raises:
        RuntimeError: If SECRETS_ENCRYPTION_KEY is not set.

    Returns:
        The Fernet instance for encryption/decryption.
    """
    key = os.environ.get("SECRETS_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError(
            "SECRETS_ENCRYPTION_KEY is not set. Generate with: Fernet.generate_key().decode()"
        )
    return Fernet(key.encode())


def encrypt_secret(value: str) -> bytes:
    """Encrypt a secret value.

    Args:
        value: The plaintext secret to encrypt.

    Returns:
        The encrypted secret as bytes.
    """
    return _get_fernet().encrypt(value.encode("utf-8"))


def decrypt_secret(encrypted: bytes) -> str:
    """Decrypt a secret value.

    Args:
        encrypted: The encrypted secret bytes.

    Returns:
        The decrypted plaintext secret.
    """
    return _get_fernet().decrypt(encrypted).decode("utf-8")


def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key.

    Returns:
        A new base64-encoded encryption key suitable for SECRETS_ENCRYPTION_KEY.
    """
    return Fernet.generate_key().decode()
