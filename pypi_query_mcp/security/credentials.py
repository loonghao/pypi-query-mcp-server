"""
Secure credential storage and management for mcpypi.

This module provides secure storage and retrieval of sensitive credentials
like API tokens, with proper encryption and access controls.
"""
import base64
import logging
import os
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class CredentialSecurityError(Exception):
    """Raised when credential operations fail for security reasons."""
    pass


class SecureCredentialManager:
    """Secure credential storage with encryption."""

    def __init__(self, master_key: bytes | None = None):
        """
        Initialize credential manager.

        Args:
            master_key: Optional master key for encryption. If not provided,
                       will be derived from environment variables.
        """
        self._fernet = None
        self._initialize_encryption(master_key)

    def _initialize_encryption(self, master_key: bytes | None = None) -> None:
        """Initialize encryption system."""
        if master_key:
            key = master_key
        else:
            # Derive key from environment
            password = os.environ.get("MCPYPI_MASTER_PASSWORD", "").encode()
            if not password:
                # For development only - in production, require explicit password
                logger.warning("No master password set, using development default")
                password = b"development-only-password-change-in-production"

            salt = os.environ.get("MCPYPI_SALT", "mcpypi-default-salt").encode()

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))

        self._fernet = Fernet(key)

    def store_credential(self, key: str, value: str, encrypted: bool = True) -> bool:
        """
        Store a credential securely.

        Args:
            key: Credential identifier
            value: Credential value
            encrypted: Whether to encrypt the value

        Returns:
            True if stored successfully

        Raises:
            CredentialSecurityError: If storage fails
        """
        try:
            if not key or not value:
                raise CredentialSecurityError("Key and value cannot be empty")

            # Validate key format
            if not key.replace("_", "").replace("-", "").isalnum():
                raise CredentialSecurityError("Key contains invalid characters")

            if encrypted and self._fernet:
                # Encrypt the credential
                encrypted_value = self._fernet.encrypt(value.encode())
                # Store in environment variable (in production, use secure storage)
                os.environ[f"MCPYPI_CRED_{key.upper()}"] = base64.urlsafe_b64encode(encrypted_value).decode()
            else:
                # Store as plain text (not recommended for sensitive data)
                os.environ[f"MCPYPI_CRED_{key.upper()}"] = value

            logger.info(f"Credential stored for key: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to store credential for key '{key}': {e}")
            raise CredentialSecurityError(f"Failed to store credential: {e}")

    def retrieve_credential(self, key: str, encrypted: bool = True) -> str | None:
        """
        Retrieve a stored credential.

        Args:
            key: Credential identifier
            encrypted: Whether the credential is encrypted

        Returns:
            The credential value or None if not found

        Raises:
            CredentialSecurityError: If retrieval fails
        """
        try:
            if not key:
                raise CredentialSecurityError("Key cannot be empty")

            env_key = f"MCPYPI_CRED_{key.upper()}"
            stored_value = os.environ.get(env_key)

            if not stored_value:
                return None

            if encrypted and self._fernet:
                # Decrypt the credential
                encrypted_bytes = base64.urlsafe_b64decode(stored_value.encode())
                decrypted_value = self._fernet.decrypt(encrypted_bytes)
                return decrypted_value.decode()
            else:
                return stored_value

        except Exception as e:
            logger.error(f"Failed to retrieve credential for key '{key}': {e}")
            raise CredentialSecurityError(f"Failed to retrieve credential: {e}")

    def delete_credential(self, key: str) -> bool:
        """
        Delete a stored credential.

        Args:
            key: Credential identifier

        Returns:
            True if deleted successfully
        """
        try:
            env_key = f"MCPYPI_CRED_{key.upper()}"
            if env_key in os.environ:
                del os.environ[env_key]
                logger.info(f"Credential deleted for key: {key}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete credential for key '{key}': {e}")
            return False

    def list_credential_keys(self) -> list[str]:
        """List all stored credential keys."""
        prefix = "MCPYPI_CRED_"
        return [
            key[len(prefix):].lower()
            for key in os.environ.keys()
            if key.startswith(prefix)
        ]

    def mask_credential(self, value: str, visible_chars: int = 4) -> str:
        """
        Mask a credential value for safe display.

        Args:
            value: Credential value to mask
            visible_chars: Number of characters to show at the end

        Returns:
            Masked credential value
        """
        if not value:
            return ""

        if len(value) <= visible_chars:
            return "*" * len(value)

        return "*" * (len(value) - visible_chars) + value[-visible_chars:]


class PyPICredentialManager:
    """Specialized credential manager for PyPI tokens."""

    def __init__(self):
        self._credential_manager = SecureCredentialManager()

    def store_pypi_token(self, token: str, test_pypi: bool = False) -> bool:
        """
        Store a PyPI API token securely.

        Args:
            token: PyPI API token
            test_pypi: Whether this is a TestPyPI token

        Returns:
            True if stored successfully
        """
        if not token or not token.startswith("pypi-"):
            raise CredentialSecurityError("Invalid PyPI token format")

        key = "test_pypi_token" if test_pypi else "pypi_token"
        return self._credential_manager.store_credential(key, token, encrypted=True)

    def get_pypi_token(self, test_pypi: bool = False) -> str | None:
        """
        Retrieve PyPI API token.

        Args:
            test_pypi: Whether to get TestPyPI token

        Returns:
            PyPI token or None if not found
        """
        key = "test_pypi_token" if test_pypi else "pypi_token"
        return self._credential_manager.retrieve_credential(key, encrypted=True)

    def validate_token_format(self, token: str) -> dict[str, Any]:
        """
        Validate PyPI token format and extract metadata.

        Args:
            token: PyPI token to validate

        Returns:
            Dictionary with validation results
        """
        if not token:
            return {"valid": False, "reason": "Token is empty"}

        if not token.startswith("pypi-"):
            return {"valid": False, "reason": "Token must start with 'pypi-'"}

        if len(token) < 50:
            return {"valid": False, "reason": "Token appears too short"}

        if len(token) > 500:
            return {"valid": False, "reason": "Token appears too long"}

        # Basic token structure validation
        parts = token.split("-")
        if len(parts) < 2:
            return {"valid": False, "reason": "Invalid token structure"}

        return {
            "valid": True,
            "masked_token": self._credential_manager.mask_credential(token),
            "token_prefix": parts[0],
            "estimated_length": len(token),
        }

    def get_masked_token(self, test_pypi: bool = False) -> str | None:
        """Get masked version of token for safe display."""
        token = self.get_pypi_token(test_pypi)
        if token:
            return self._credential_manager.mask_credential(token)
        return None


# Global instances for easy access
_credential_manager = SecureCredentialManager()
_pypi_credential_manager = PyPICredentialManager()


def get_credential_manager() -> SecureCredentialManager:
    """Get the global credential manager instance."""
    return _credential_manager


def get_pypi_credential_manager() -> PyPICredentialManager:
    """Get the global PyPI credential manager instance."""
    return _pypi_credential_manager


def secure_get_pypi_token(test_pypi: bool = False) -> str | None:
    """Convenience function to get PyPI token."""
    try:
        return _pypi_credential_manager.get_pypi_token(test_pypi)
    except CredentialSecurityError:
        logger.warning("Failed to retrieve PyPI token securely")
        return None


def secure_store_pypi_token(token: str, test_pypi: bool = False) -> bool:
    """Convenience function to store PyPI token."""
    try:
        return _pypi_credential_manager.store_pypi_token(token, test_pypi)
    except CredentialSecurityError as e:
        logger.error(f"Failed to store PyPI token: {e}")
        return False
