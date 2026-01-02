"""Tests for user database utility functions in user_db.user_db_utilities module."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest


class TestCoerceUserId:
    """Tests for the _coerce_user_id helper function."""

    def test_returns_uuid_unchanged(self, sample_user_id: uuid.UUID) -> None:
        """Returns UUID instance unchanged."""
        from src.user_db.user_db_utilities import _coerce_user_id

        result = _coerce_user_id(sample_user_id)

        assert result == sample_user_id
        assert isinstance(result, uuid.UUID)

    def test_converts_string_to_uuid(self, sample_user_id_str: str) -> None:
        """Converts valid UUID string to UUID instance."""
        from src.user_db.user_db_utilities import _coerce_user_id

        result = _coerce_user_id(sample_user_id_str)

        assert result == uuid.UUID(sample_user_id_str)
        assert isinstance(result, uuid.UUID)

    def test_raises_value_error_for_invalid_string(self) -> None:
        """Raises ValueError for invalid UUID string."""
        from src.user_db.user_db_utilities import _coerce_user_id

        with pytest.raises(ValueError):
            _coerce_user_id("not-a-valid-uuid")


class TestCreateUser:
    """Tests for the create_user function."""

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_creates_user_with_email(
        self, mock_session_scope: MagicMock, sample_email: str
    ) -> None:
        """Creates a new user with the provided email."""
        from src.user_db.user_db_utilities import create_user

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session

        create_user(sample_email, "password123")

        mock_session.add.assert_called_once()
        added_user = mock_session.add.call_args[0][0]
        assert added_user.email == sample_email

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_flushes_session_to_generate_id(
        self, mock_session_scope: MagicMock, sample_email: str
    ) -> None:
        """Flushes session to generate user ID before returning."""
        from src.user_db.user_db_utilities import create_user

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session

        create_user(sample_email, "password123")

        mock_session.flush.assert_called_once()

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_created_user(self, mock_session_scope: MagicMock, sample_email: str) -> None:
        """Returns the created user object."""
        from src.user_db.user_db_utilities import create_user

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session

        result = create_user(sample_email, "password123")

        assert result.email == sample_email


class TestLogoutUser:
    """Tests for the logout_user function."""

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_marks_user_inactive(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID, mock_user: MagicMock
    ) -> None:
        """Marks existing user as inactive."""
        from src.user_db.user_db_utilities import logout_user

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = mock_user

        logout_user(sample_user_id)

        assert mock_user.is_active is False

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_true_when_user_exists(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID, mock_user: MagicMock
    ) -> None:
        """Returns True when user exists and is updated."""
        from src.user_db.user_db_utilities import logout_user

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = mock_user

        result = logout_user(sample_user_id)

        assert result is True

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_false_when_user_not_found(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Returns False when user does not exist."""
        from src.user_db.user_db_utilities import logout_user

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = None

        result = logout_user(sample_user_id)

        assert result is False

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_accepts_string_user_id(
        self, mock_session_scope: MagicMock, sample_user_id_str: str, mock_user: MagicMock
    ) -> None:
        """Accepts string user ID and converts to UUID."""
        from src.user_db.user_db_utilities import logout_user

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = mock_user

        result = logout_user(sample_user_id_str)

        assert result is True


class TestDeleteUser:
    """Tests for the delete_user function."""

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_deletes_existing_user(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID, mock_user: MagicMock
    ) -> None:
        """Deletes existing user from database."""
        from src.user_db.user_db_utilities import delete_user

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = mock_user

        delete_user(sample_user_id)

        mock_session.delete.assert_called_once_with(mock_user)

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_true_when_user_deleted(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID, mock_user: MagicMock
    ) -> None:
        """Returns True when user is successfully deleted."""
        from src.user_db.user_db_utilities import delete_user

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = mock_user

        result = delete_user(sample_user_id)

        assert result is True

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_false_when_user_not_found(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Returns False when user does not exist."""
        from src.user_db.user_db_utilities import delete_user

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = None

        result = delete_user(sample_user_id)

        assert result is False

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_accepts_string_user_id(
        self, mock_session_scope: MagicMock, sample_user_id_str: str, mock_user: MagicMock
    ) -> None:
        """Accepts string user ID and converts to UUID."""
        from src.user_db.user_db_utilities import delete_user

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = mock_user

        result = delete_user(sample_user_id_str)

        assert result is True


class TestGetUserByEmail:
    """Tests for the get_user_by_email function."""

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_user_when_found(
        self, mock_session_scope: MagicMock, sample_email: str, mock_user: MagicMock
    ) -> None:
        """Returns user when found by email."""
        from src.user_db.user_db_utilities import get_user_by_email

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = mock_user

        result = get_user_by_email(sample_email)

        assert result is mock_user

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_none_when_not_found(
        self, mock_session_scope: MagicMock, sample_email: str
    ) -> None:
        """Returns None when user not found."""
        from src.user_db.user_db_utilities import get_user_by_email

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = None

        result = get_user_by_email(sample_email)

        assert result is None


class TestGetUserById:
    """Tests for the get_user_by_id function."""

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_user_when_found(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID, mock_user: MagicMock
    ) -> None:
        """Returns user when found by ID."""
        from src.user_db.user_db_utilities import get_user_by_id

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = mock_user

        result = get_user_by_id(sample_user_id)

        assert result is mock_user

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_none_when_not_found(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Returns None when user not found."""
        from src.user_db.user_db_utilities import get_user_by_id

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = None

        result = get_user_by_id(sample_user_id)

        assert result is None

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_accepts_string_user_id(
        self, mock_session_scope: MagicMock, sample_user_id_str: str, mock_user: MagicMock
    ) -> None:
        """Accepts string user ID and converts to UUID."""
        from src.user_db.user_db_utilities import get_user_by_id

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = mock_user

        result = get_user_by_id(sample_user_id_str)

        assert result is mock_user


class TestEnsureUserExists:
    """Tests for the ensure_user_exists function."""

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_existing_user_when_found(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID, mock_user: MagicMock
    ) -> None:
        """Returns existing user when found in database."""
        from src.user_db.user_db_utilities import ensure_user_exists

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = mock_user

        result = ensure_user_exists(sample_user_id)

        assert result is mock_user

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_creates_new_user_when_not_found(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Creates new user when not found in database."""
        from src.user_db.user_db_utilities import ensure_user_exists

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = None

        ensure_user_exists(sample_user_id)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_uses_provided_email_for_new_user(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID, sample_email: str
    ) -> None:
        """Uses provided email when creating new user."""
        from src.user_db.user_db_utilities import ensure_user_exists

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = None

        ensure_user_exists(sample_user_id, email=sample_email)

        added_user = mock_session.add.call_args[0][0]
        assert added_user.email == sample_email

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_uses_placeholder_email_when_not_provided(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Uses placeholder email when email not provided."""
        from src.user_db.user_db_utilities import ensure_user_exists

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = None

        ensure_user_exists(sample_user_id)

        added_user = mock_session.add.call_args[0][0]
        assert added_user.email == f"{sample_user_id}@keycloak.local"

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_sets_user_id_from_keycloak_sub(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Sets user ID from keycloak subject."""
        from src.user_db.user_db_utilities import ensure_user_exists

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = None

        ensure_user_exists(sample_user_id)

        added_user = mock_session.add.call_args[0][0]
        assert added_user.id == sample_user_id

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_sets_user_active_to_true(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Sets is_active to True for new user."""
        from src.user_db.user_db_utilities import ensure_user_exists

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = None

        ensure_user_exists(sample_user_id)

        added_user = mock_session.add.call_args[0][0]
        assert added_user.is_active is True

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_accepts_string_keycloak_sub(
        self, mock_session_scope: MagicMock, sample_user_id_str: str, mock_user: MagicMock
    ) -> None:
        """Accepts string keycloak subject and converts to UUID."""
        from src.user_db.user_db_utilities import ensure_user_exists

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = mock_user

        result = ensure_user_exists(sample_user_id_str)

        assert result is mock_user


class TestSetUserSecret:
    """Tests for the set_user_secret function."""

    @patch("src.user_db.user_db_utilities.encrypt_secret")
    @patch("src.user_db.user_db_utilities.session_scope")
    def test_encrypts_secret_value(
        self, mock_session_scope: MagicMock, mock_encrypt: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Encrypts the secret value before storing."""
        from src.user_db.user_db_utilities import set_user_secret

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_encrypt.return_value = b"encrypted"

        set_user_secret(sample_user_id, "API_KEY", "secret-value")

        mock_encrypt.assert_called_once_with("secret-value")

    @patch("src.user_db.user_db_utilities.encrypt_secret")
    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_user_secret_instance(
        self, mock_session_scope: MagicMock, mock_encrypt: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Returns the created or updated UserSecret instance."""
        from src.user_db.user_db_utilities import set_user_secret

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_encrypt.return_value = b"encrypted"
        mock_secret = MagicMock()
        mock_session.scalar.return_value = mock_secret

        result = set_user_secret(sample_user_id, "API_KEY", "secret-value")

        assert result is mock_secret

    @patch("src.user_db.user_db_utilities.encrypt_secret")
    @patch("src.user_db.user_db_utilities.session_scope")
    def test_accepts_string_user_id(
        self,
        mock_session_scope: MagicMock,
        mock_encrypt: MagicMock,
        sample_user_id_str: str,
        mock_user_secret: MagicMock,
    ) -> None:
        """Accepts string user ID and converts to UUID."""
        from src.user_db.user_db_utilities import set_user_secret

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_encrypt.return_value = b"encrypted"
        mock_session.scalar.return_value = mock_user_secret

        result = set_user_secret(sample_user_id_str, "API_KEY", "secret-value")

        assert result is mock_user_secret


class TestGetUserSecret:
    """Tests for the get_user_secret function."""

    @patch("src.user_db.user_db_utilities.decrypt_secret")
    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_decrypted_value_when_found(
        self,
        mock_session_scope: MagicMock,
        mock_decrypt: MagicMock,
        sample_user_id: uuid.UUID,
        mock_user_secret: MagicMock,
    ) -> None:
        """Returns decrypted secret value when found."""
        from src.user_db.user_db_utilities import get_user_secret

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = mock_user_secret
        mock_decrypt.return_value = "decrypted-value"

        result = get_user_secret(sample_user_id, "API_KEY")

        assert result == "decrypted-value"

    @patch("src.user_db.user_db_utilities.decrypt_secret")
    @patch("src.user_db.user_db_utilities.session_scope")
    def test_decrypts_encrypted_value(
        self,
        mock_session_scope: MagicMock,
        mock_decrypt: MagicMock,
        sample_user_id: uuid.UUID,
        mock_user_secret: MagicMock,
    ) -> None:
        """Decrypts the stored encrypted value."""
        from src.user_db.user_db_utilities import get_user_secret

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = mock_user_secret
        mock_decrypt.return_value = "decrypted-value"

        get_user_secret(sample_user_id, "API_KEY")

        mock_decrypt.assert_called_once_with(mock_user_secret.encrypted_value)

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_none_when_not_found(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Returns None when secret not found."""
        from src.user_db.user_db_utilities import get_user_secret

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = None

        result = get_user_secret(sample_user_id, "API_KEY")

        assert result is None

    @patch("src.user_db.user_db_utilities.decrypt_secret")
    @patch("src.user_db.user_db_utilities.session_scope")
    def test_accepts_string_user_id(
        self,
        mock_session_scope: MagicMock,
        mock_decrypt: MagicMock,
        sample_user_id_str: str,
        mock_user_secret: MagicMock,
    ) -> None:
        """Accepts string user ID and converts to UUID."""
        from src.user_db.user_db_utilities import get_user_secret

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = mock_user_secret
        mock_decrypt.return_value = "decrypted-value"

        result = get_user_secret(sample_user_id_str, "API_KEY")

        assert result == "decrypted-value"


class TestGetAllUserSecrets:
    """Tests for the get_all_user_secrets function."""

    @patch("src.user_db.user_db_utilities.decrypt_secret")
    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_dict_of_decrypted_secrets(
        self, mock_session_scope: MagicMock, mock_decrypt: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Returns dictionary of decrypted secrets."""
        from src.user_db.user_db_utilities import get_all_user_secrets

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session

        mock_secret1 = MagicMock()
        mock_secret1.key = "API_KEY"
        mock_secret1.encrypted_value = b"encrypted1"

        mock_secret2 = MagicMock()
        mock_secret2.key = "DISH_COOKIE"
        mock_secret2.encrypted_value = b"encrypted2"

        mock_session.scalars.return_value.all.return_value = [mock_secret1, mock_secret2]
        mock_decrypt.side_effect = ["value1", "value2"]

        result = get_all_user_secrets(sample_user_id)

        assert result == {"API_KEY": "value1", "DISH_COOKIE": "value2"}

    @patch("src.user_db.user_db_utilities.decrypt_secret")
    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_empty_dict_when_no_secrets(
        self, mock_session_scope: MagicMock, mock_decrypt: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Returns empty dictionary when user has no secrets."""
        from src.user_db.user_db_utilities import get_all_user_secrets

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalars.return_value.all.return_value = []

        result = get_all_user_secrets(sample_user_id)

        assert result == {}

    @patch("src.user_db.user_db_utilities.decrypt_secret")
    @patch("src.user_db.user_db_utilities.session_scope")
    def test_accepts_string_user_id(
        self, mock_session_scope: MagicMock, mock_decrypt: MagicMock, sample_user_id_str: str
    ) -> None:
        """Accepts string user ID and converts to UUID."""
        from src.user_db.user_db_utilities import get_all_user_secrets

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalars.return_value.all.return_value = []

        result = get_all_user_secrets(sample_user_id_str)

        assert result == {}


class TestDeleteUserSecret:
    """Tests for the delete_user_secret function."""

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_deletes_existing_secret(
        self,
        mock_session_scope: MagicMock,
        sample_user_id: uuid.UUID,
        mock_user_secret: MagicMock,
    ) -> None:
        """Deletes existing secret from database."""
        from src.user_db.user_db_utilities import delete_user_secret

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = mock_user_secret

        delete_user_secret(sample_user_id, "API_KEY")

        mock_session.delete.assert_called_once_with(mock_user_secret)

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_true_when_secret_deleted(
        self,
        mock_session_scope: MagicMock,
        sample_user_id: uuid.UUID,
        mock_user_secret: MagicMock,
    ) -> None:
        """Returns True when secret is successfully deleted."""
        from src.user_db.user_db_utilities import delete_user_secret

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = mock_user_secret

        result = delete_user_secret(sample_user_id, "API_KEY")

        assert result is True

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_false_when_secret_not_found(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Returns False when secret does not exist."""
        from src.user_db.user_db_utilities import delete_user_secret

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = None

        result = delete_user_secret(sample_user_id, "API_KEY")

        assert result is False

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_accepts_string_user_id(
        self,
        mock_session_scope: MagicMock,
        sample_user_id_str: str,
        mock_user_secret: MagicMock,
    ) -> None:
        """Accepts string user ID and converts to UUID."""
        from src.user_db.user_db_utilities import delete_user_secret

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalar.return_value = mock_user_secret

        result = delete_user_secret(sample_user_id_str, "API_KEY")

        assert result is True


class TestListUserSecretKeys:
    """Tests for the list_user_secret_keys function."""

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_list_of_secret_keys(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Returns list of secret key names."""
        from src.user_db.user_db_utilities import list_user_secret_keys

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session

        mock_secret1 = MagicMock()
        mock_secret1.key = "API_KEY"

        mock_secret2 = MagicMock()
        mock_secret2.key = "DISH_COOKIE"

        mock_session.scalars.return_value.all.return_value = [mock_secret1, mock_secret2]

        result = list_user_secret_keys(sample_user_id)

        assert result == ["API_KEY", "DISH_COOKIE"]

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_returns_empty_list_when_no_secrets(
        self, mock_session_scope: MagicMock, sample_user_id: uuid.UUID
    ) -> None:
        """Returns empty list when user has no secrets."""
        from src.user_db.user_db_utilities import list_user_secret_keys

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalars.return_value.all.return_value = []

        result = list_user_secret_keys(sample_user_id)

        assert result == []

    @patch("src.user_db.user_db_utilities.session_scope")
    def test_accepts_string_user_id(
        self, mock_session_scope: MagicMock, sample_user_id_str: str
    ) -> None:
        """Accepts string user ID and converts to UUID."""
        from src.user_db.user_db_utilities import list_user_secret_keys

        mock_session = MagicMock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        mock_session.scalars.return_value.all.return_value = []

        result = list_user_secret_keys(sample_user_id_str)

        assert result == []
