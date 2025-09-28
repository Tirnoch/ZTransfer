"""Security helpers shared across dependencies."""

from __future__ import annotations

import hmac
from hashlib import sha256
from secrets import token_urlsafe

from ..config import settings


def _sign_nonce(nonce: str) -> str:
    secret = settings.session_secret.encode("utf-8")
    return hmac.new(secret, nonce.encode("utf-8"), sha256).hexdigest()


def issue_csrf_token() -> str:
    """Return an HMAC-signed CSRF token for double-submit cookie validation."""

    nonce = token_urlsafe(32)
    signature = _sign_nonce(nonce)
    return f"{nonce}.{signature}"


def validate_csrf_token(submitted: str | None, cookie_value: str | None) -> bool:
    """Ensure submitted CSRF token matches the cookie and signature."""

    if not submitted or not cookie_value:
        return False
    if not hmac.compare_digest(submitted, cookie_value):
        return False
    try:
        nonce, signature = submitted.split(".", 1)
    except ValueError:
        return False
    expected = _sign_nonce(nonce)
    return hmac.compare_digest(signature, expected)
