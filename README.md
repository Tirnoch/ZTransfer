# ZTransfer

ZTransfer is a local-first, invite-only file transfer service inspired by WeTransfer. The goal is to provide a lightweight sharing workflow for a small trusted team (4–5 users) with private download links, predictable storage, and a clear path to running on a VPS behind Traefik.

## Project Goals

- Deliver a self-hostable file transfer backend that streams uploads to disk without buffering entire files in memory.
- Support multiple authenticated users via invite-only access, session cookies, and CSRF protection.
- Generate unguessable share links with optional passwords and short expirations.
- Enforce retention policies and automate cleanup of expired files.
- Provide a clear upgrade path from SQLite to PostgreSQL and from local disk to resumable uploads (TUS or S3 multipart).
- Keep deployment simple with Docker/Compose and Traefik routing.

## Current Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 0 | Tooling & environment setup | ✅ Completed |
| Phase 1 | Core API skeleton, logging, health checks | ✅ Completed |
| Phase 2 | Authentication & user management | ✅ Completed |
| Phase 3 | Upload flow (streaming + metadata) | ✅ Completed |
| Phase 4 | Share links, downloads, deletion | ⏳ Pending |
| Phase 5 | Retention & background tasks | ⏳ Pending |
| Phase 6 | Frontend (React, Tailwind, shadcn) | ⏳ Pending |
| Phase 7 | Resumable uploads (TUS/S3 multipart) | ⏳ Pending |
| Phase 8 | Packaging & deployment (Docker, Traefik) | ⏳ Pending |
| Phase 9 | Observability & hardening | ⏳ Pending |

## Local Development

### Prerequisites

- Python 3.11+ (the project currently targets >=3.11)
- [uv](https://github.com/astral-sh/uv) (optional but recommended) or `python -m venv`
- Git, make sure submodules are checked out if the repo adds them later

### Setup

```bash
# Clone the repository
 git clone git@github.com:Tirnoch/ZTransfer.git
 cd ZTransfer

# Create a virtual environment
 uv venv              # or: python3 -m venv .venv
 source .venv/bin/activate

# Install dependencies
 python -m pip install --upgrade pip
 python -m pip install -e .[dev]

# Copy environment template and adjust values
 cp .env.example .env
# edit .env to set session secret, optional admin bootstrap token, etc.

# Run type checks
 python -m mypy src

# Run auth flow tests
 python -m pytest

# Launch the API (hot-reload for development)
 uvicorn app.main:app --reload --app-dir src
```

Visit `http://localhost:8000` to see the placeholder interface. Health endpoints are available at:

- `GET /healthz` — liveness probe
- `GET /readyz` — readiness probe (checks DB + storage)
- `GET /version` — current package version

`/auth/login` and `/auth/invite/bootstrap` currently return placeholder responses while Phase 2 is under construction.

## Tech Stack Overview

- **Backend:** FastAPI, SQLModel, Pydantic v2 + pydantic-settings, SQLite (local), Postgres (future)
- **Auth (planned):** Cookie-backed sessions, bcrypt password hashing, invite-only onboarding, optional TOTP
- **Storage:** Local disk (streaming writes), SHA-256 hashes, eventual TUS/S3 multipart support for resumable uploads
- **Frontend (Phase 6):** React, TypeScript, Vite, TailwindCSS, shadcn/ui, TanStack Query
- **Dev Tooling:** mypy, (future) pytest + httpx, ruff for linting, pre-commit
- **Ops:** Docker/Compose, Traefik reverse proxy, Prometheus metrics (Phase 9)

## Roadmap Highlights

1. **Phase 2 — Authentication & User Management**
   - Implement invite-only provisioning, session storage, CSRF tokens, logout.
   - Guard upload/delete routes by user, keep downloads public with short TTL.

2. **Phase 3 — Upload Flow**
   - Stream uploads with size enforcement, compute SHA-256, store metadata.
   - Persist share/delete tokens and retention info.

3. **Phase 4 — Share Links**
   - Create share endpoints with optional passwords, Range-supporting downloads, rate limiting.

4. **Phase 5 — Retention**
   - Scheduled cleanup worker + CLI entry; logging/reporting for storage usage.

5. **Phase 6 — Frontend**
   - Build React UI for login, upload, file management, download pages.

6. **Phase 7 — Resumable Uploads**
   - Integrate TUS or S3 multipart; stress-test 5 GB transfers.

7. **Phase 8 — Deployment**
   - Docker/Compose stack, Traefik integration, Postgres migration script.

8. **Phase 9 — Observability & Hardening**
   - Prometheus metrics, structured logging polish, rate limiting, backups, optional malware scanning.

Refer to [PROJECT_PLAN.md](PROJECT_PLAN.md) for the detailed, living project plan that both documents design decisions and tracks progress.

## Contributing

This project is currently developed in collaboration with an AI assistant. If you want to contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Follow the coding standards (type hints, tests, linting).
4. Submit a pull request describing the change.

Please update tests and documentation when adding new features. Reach out via issues for major design changes before opening a PR.

## License

This repository has not yet declared a license. Until one is specified, all rights are reserved by the author. If you intend to deploy or fork the project, please open an issue to discuss licensing.
