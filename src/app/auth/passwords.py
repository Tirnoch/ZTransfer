"""Password hashing helpers using Argon2."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return the Argon2 hash for the supplied password."""

    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against the stored hash."""

    try:
        return _hasher.verify(hashed, password)
    except VerificationError:
        return False
