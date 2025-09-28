"""Authentication route scaffolding for Phase 1."""

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from ..deps import issue_csrf_token
from ..paths import TEMPLATES_DIR

router = APIRouter(prefix="/auth", tags=["auth"])

_templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request) -> HTMLResponse:
    """Render a placeholder login form with CSRF token."""

    csrf_token = issue_csrf_token()
    return _templates.TemplateResponse(
        "auth/login.html", {"request": request, "csrf_token": csrf_token}
    )


@router.post("/login")
async def login_submit() -> JSONResponse:
    """Placeholder login handler until Phase 2 implements real auth."""

    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Login pending")


@router.post("/logout")
async def logout() -> JSONResponse:
    """Placeholder logout endpoint."""

    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Logout pending")


@router.get("/invite/bootstrap")
async def bootstrap_invite() -> JSONResponse:
    """Placeholder endpoint to seed the first admin invite."""

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "detail": "Bootstrap endpoint placeholder. Phase 2 will generate a one-time admin invite token."
        },
    )
