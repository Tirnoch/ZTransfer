"""Security helpers and placeholders for authentication scaffolding."""

from secrets import token_urlsafe


def issue_csrf_token() -> str:
    """Return a cryptographically random CSRF token for forms.

    In Phase 2 we will bind these tokens to user sessions and enforce validation.
    """

    return token_urlsafe(32)


def validate_csrf_token(_token: str) -> bool:
    """Placeholder validation hook for CSRF tokens.

    Always returns True for now; real validation arrives with session management.
    """

    return True
