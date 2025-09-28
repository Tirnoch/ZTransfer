from __future__ import annotations

import re

import pytest


def _extract_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, "CSRF token not found in login form"
    return match.group(1)


def test_bootstrap_invite_requires_token(test_client):
    response = test_client.post(
        "/auth/invite/bootstrap",
        json={"admin_token": "wrong", "email": "admin@example.com"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid bootstrap token"


def test_invite_accept_and_login_flow(test_client):
    # Bootstrap admin invite
    bootstrap_response = test_client.post(
        "/auth/invite/bootstrap",
        json={"admin_token": "bootstrap-token", "email": "admin@example.com"},
    )
    assert bootstrap_response.status_code == 201
    invite_token = bootstrap_response.json()["invite_token"]

    # Accept invite and create user
    accept_response = test_client.post(
        "/auth/invite/accept",
        json={
            "token": invite_token,
            "email": "admin@example.com",
            "password": "supersecret",
        },
    )
    assert accept_response.status_code == 201

    # Login form to obtain CSRF token and cookie
    login_form = test_client.get("/auth/login")
    assert login_form.status_code == 200
    csrf_token = _extract_csrf_token(login_form.text)

    # Submit login credentials
    login_response = test_client.post(
        "/auth/login",
        data={
            "email": "admin@example.com",
            "password": "supersecret",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert login_response.status_code == 303
    assert test_client.cookies.get("test_session") is not None

    # Logout should clear the session cookie
    logout_response = test_client.post("/auth/logout")
    assert logout_response.status_code == 200
    assert test_client.cookies.get("test_session") is None

    # Additional bootstrap attempts should now fail because user exists
    conflict_response = test_client.post(
        "/auth/invite/bootstrap",
        json={"admin_token": "bootstrap-token", "email": "other@example.com"},
    )
    assert conflict_response.status_code == 409


def test_login_requires_csrf(test_client):
    # Prepare user via invite
    bootstrap_response = test_client.post(
        "/auth/invite/bootstrap",
        json={"admin_token": "bootstrap-token", "email": "user@example.com"},
    )
    invite_token = bootstrap_response.json()["invite_token"]
    test_client.post(
        "/auth/invite/accept",
        json={"token": invite_token, "email": "user@example.com", "password": "secret"},
    )

    response = test_client.post(
        "/auth/login",
        data={"email": "user@example.com", "password": "secret", "csrf_token": "invalid"},
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid CSRF token"
