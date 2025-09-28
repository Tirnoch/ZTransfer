"""Authentication routes for session-based login and invite flow."""

from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..config import settings
from ..deps import issue_csrf_token, validate_csrf_token
from ..paths import TEMPLATES_DIR
from . import service
from .schemas import (
    BootstrapInviteRequest,
    InviteAcceptRequest,
    InviteResponse,
    MessageResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _set_cookie(response: Response, *, key: str, value: str, max_age: int, httponly: bool) -> None:
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        path="/" if key == settings.session_cookie_name else "/auth",
        secure=settings.cookie_secure,
        httponly=httponly,
        samesite=settings.cookie_samesite,
    )


def _clear_cookie(response: Response, *, key: str) -> None:
    response.delete_cookie(key=key, path="/" if key == settings.session_cookie_name else "/auth")


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request) -> HTMLResponse:
    """Render the login form, issuing a CSRF cookie."""

    csrf_token = issue_csrf_token()
    response = _templates.TemplateResponse(
        request,
        "auth/login.html",
        {"csrf_token": csrf_token},
    )
    _set_cookie(
        response,
        key=settings.csrf_cookie_name,
        value=csrf_token,
        max_age=settings.csrf_token_max_age,
        httponly=False,
    )
    return response


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
) -> RedirectResponse:
    """Validate credentials and establish an authenticated session."""

    csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
    if not validate_csrf_token(csrf_token, csrf_cookie):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CSRF token")

    try:
        user = service.authenticate_user(email=email, password=password)
    except service.InvalidCredentials as exc:  # pragma: no cover - mapping to HTTP
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc

    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    if user.id is None:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User record invalid")

    session_token = service.create_session(user_id=user.id, ip_address=client_host, user_agent=user_agent)

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    _set_cookie(
        response,
        key=settings.session_cookie_name,
        value=session_token,
        max_age=settings.session_cookie_max_age,
        httponly=True,
    )
    _clear_cookie(response, key=settings.csrf_cookie_name)
    return response


@router.post("/logout")
async def logout(request: Request) -> JSONResponse:
    """Invalidate the active session cookie."""

    session_token = request.cookies.get(settings.session_cookie_name)
    if session_token:
        service.revoke_session(session_token)
    response = JSONResponse(status_code=status.HTTP_200_OK, content={"detail": "Logged out"})
    _clear_cookie(response, key=settings.session_cookie_name)
    _clear_cookie(response, key=settings.csrf_cookie_name)
    return response


@router.post("/invite/bootstrap", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap_invite(payload: BootstrapInviteRequest) -> InviteResponse:
    """Seed the first admin invite using the ADMIN_BOOTSTRAP_TOKEN secret."""

    if not settings.admin_bootstrap_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bootstrap token not configured")
    if payload.admin_token != settings.admin_bootstrap_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bootstrap token")
    if service.users_exist():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Users already exist")

    invite, raw_token = service.create_invite(email=payload.email, role=payload.role)
    return InviteResponse(
        invite_token=raw_token,
        expires_at=invite.expires_at,
        email=invite.email,
        role=invite.role,
    )


@router.post("/invite/accept", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def accept_invite(payload: InviteAcceptRequest) -> MessageResponse:
    """Convert an invite into an active user account."""

    try:
        service.consume_invite(token=payload.token, email=payload.email, password=payload.password)
    except service.InviteAlreadyUsed as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except service.InvalidInvite as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return MessageResponse(detail="Invite accepted. You can now sign in.")
