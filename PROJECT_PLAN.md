# ZTransfer Project Plan

## 1. Purpose & Goals
- Deliver a local-first, private file sharing service similar to WeTransfer, suitable for a small team (4–5 users).
- Keep setup lightweight and developer-friendly while preparing for containerized deployment.
- Prioritize security basics, predictable storage, and clear operational tasks before expanding features.

## 2. MVP Scope & Constraints
- Multi-user workflow with lightweight authentication (target 4–5 trusted users).
- Max file size: 5 GB per upload (configurable).
- File retention: 10 days by default with optional manual delete token.
- Private, unguessable download links; optional delete key per upload.
- Storage on local disk; metadata in SQLite.
- Streaming uploads/downloads; never buffer entire file in memory.

## 3. Architecture Overview
### Backend
- FastAPI application served by Uvicorn.
- Python dependency management via `uv` (or `poetry` alternative if needed).
- ORM layer: SQLModel (or hand-written SQL if we hit ORM limitations).
- Authentication subsystem: cookie-backed sessions for 4–5 users, with Secure/HttpOnly/SameSite flags plus CSRF tokens on state-changing routes; JWT access/refresh tokens remain a stretch goal if we later need mobile clients or external integrations.
- Pydantic models back request/response validation to keep type hints aligned with runtime data and enable strong runtime validation.

### Data & Storage
- Database: SQLite file located under project storage directory.
- Storage layout: deterministic and versionable: `storage/<owner_id>/<yyyy-mm>/<uuid>/<original_name>` so migrations and future dedupe/hash strategies stay manageable.
- Data models:
  - `users`: `{id, email, password_hash, created_at, last_login_at, is_active}`.
  - `uploads`: `{id, owner_id, download_token, delete_token_hash, path, original_name, content_type, size_bytes, created_at, expires_at, sha256}`.
- Retention worker cleans up expired metadata and files; storage helpers compute and persist SHA-256 hashes during upload to support integrity checks and eventual deduplication.

### Configuration
- `.env` managed via `python-dotenv`; core settings: `STORAGE_DIR`, `DB_PATH`, `MAX_SIZE_BYTES`, `RETENTION_DAYS`, `BASE_URL`, `CHUNK_SIZE`.
- Default storage directory lives inside repo for local dev; overridable via env when containerized.
- Secret management: `SESSION_SECRET`, optional `ADMIN_BOOTSTRAP_TOKEN` for first user creation.

### Security & Compliance
- Enforce max upload size via streaming counter, even if `Content-Length` is missing.
- Sanitize filenames and set `Content-Disposition` safely.
- Generate URL-safe tokens (32+ chars). Store delete tokens hashed and record short-lived share tokens.
- Hash user passwords with `argon2` (preferred) or `bcrypt`; session cookies must be Secure, HttpOnly, SameSite=Lax (or Strict for admin forms) and accompanied by CSRF tokens for POST/PUT/DELETE.
- Rate limit authentication attempts and public download endpoints (per IP and per token) to reduce brute-force surface.
- Signed download links expire quickly; optional link passwords are hashed and rate-limited on failure.
- Disable directory listings; never render user-supplied paths.
- Prepare for optional malware scanning (ClamAV sidecar) once large files are common.

## 4. Implementation Roadmap
### Phase 0 — Tooling & Environment
- Initialize repo structure, `.gitignore`, and base README stub.
- Create Python virtual environment with `uv` or `venv`.
- Add dependencies: `fastapi`, `uvicorn[standard]`, `sqlmodel`, `python-multipart`, `python-dotenv`.
- Add dev dependencies: `pydantic` (explicit models) and `mypy` for static type checking (`uv add --dev pydantic mypy`).
- Scaffold `src/app` package with modules: `main.py`, `config.py`, `models.py`, `db.py`, `storage.py`, `cleanup_worker.py`, `templates/`.
- Provide `.env.example` with sensible defaults.

### Phase 1 — Core API Skeleton
- Implement `FastAPI` app with `GET /healthz` and root upload form placeholder.
- Configure structured JSON logging and startup/shutdown events (DB connection, background worker hooks).
- Add basic HTML template served from `templates/index.html`.
- Introduce auth routes scaffolding (`/login`, `/logout`, `/signup` or admin bootstrap) capped with CSRF token generation helpers.

### Phase 2 — Authentication & User Management
- Implement invite-only user provisioning (admin seeds invite tokens, optional expiry).
- Add login endpoint issuing signed session cookies and CSRF tokens; include logout handler that invalidates server-side session records.
- Guard upload/delete endpoints with authentication; downloads may stay public but still enforce token TTL + rate limiting.
- Store password hashes and session data securely; add unit/integration tests for invites, login throttling, and CSRF middleware.

### Phase 3 — Upload Flow
- Implement multipart upload endpoint (`POST /upload`) tied to authenticated user.
- Stream file to disk using chunked writes; enforce max size and accumulate SHA-256 hash during streaming.
- Persist metadata row on success (owner reference, tokens, hash, expiry).
- Return JSON payload and/or HTML confirmation with download/delete URLs.
- Add unit and integration tests for storage writer, hash verification, and quota enforcement.

### Phase 4 — Share Links, Download & Delete
- Implement `POST /shares` to mint short-TTL public tokens (optional password) and `GET /d/{token}` streaming responses with Range support.
- Add `DELETE /files/{id}` or share revocation endpoints, guarded by owner auth or delete token.
- Handle missing/expired files gracefully (404 with guidance) and log suspicious access attempts.
- Integration tests using FastAPI `TestClient` for auth + upload-download-delete cycle, including rate-limit edge cases.

### Phase 5 — Retention & Background Tasks
- Implement cleanup worker that runs at startup (FastAPI `lifespan` or APScheduler) and sweeps daily.
- Ensure worker logs actions and handles partial failures (missing file but DB row, etc.).
- Add CLI entry (`python -m app.cleanup_worker`) for cron/one-shot use when containerized.
- Document manual runbook for emergency cleanup and storage usage reporting.

### Phase 6 — Frontend Enhancements (Later)
- Introduce React + TypeScript + Tailwind + shadcn UI once backend endpoints stabilize.
- Provide upload page with progress bar, drag-and-drop, and success screen.
- Ensure frontend consumes same API endpoints for parity, including auth state awareness via cookie-backed sessions.
- Add rate-limit and error surfacing in UI (e.g., share password failures, quota warnings).

### Phase 7 — Resumable Uploads (Mandatory for 5 GB)
- Select resumable strategy: TUS (with tusd sidecar) or S3 multipart presigned uploads.
- Integrate client and backend flow (pause/resume, finalization webhook) and update metadata persistence accordingly.
- Stress-test with ≥5 GB files over flaky connections to ensure reliability before production.

### Phase 8 — Packaging & Deployment
- Write `Dockerfile` targeting slim Python base, running as non-root.
- Add `docker-compose.yml` for local container testing with volume mount for storage (and tusd/S3 adapters if applicable).
- Document environment variables, storage volume bindings, and Traefik routing labels.
- Prepare Postgres migration script for VPS deployment.

## 5. Testing & QA Strategy
- Unit tests: storage chunk writer, token generation, config loader, password hashing/auth helpers, invite workflow.
- Integration tests: auth + upload/download/delete lifecycle with temporary storage dir, including CSRF validation and quota enforcement.
- Security-focused tests: invalid login attempts, session expiry, rate limiting, share password failures, signed-link expiry.
- Functional smoke test script to verify `/healthz`, `/version`, and share download flow.
- Use GitHub Actions (later) for lint + tests (consider `ruff` for linting, `pytest` for testing).
- Static typing: run `uv run mypy src` locally and in CI to enforce type correctness alongside Pydantic validation.
- Add contract tests for resumable upload finalization once Phase 7 begins.

## 6. Observability & Ops
- Structured JSON logging enabled from the first runnable build (include request IDs, user IDs, share tokens redacted).
- Capture request metrics via middleware later: start with simple counters, upgrade to Prometheus `prometheus-client` in Phase 9.
- Provide disk usage check script/endpoint for monitoring storage consumption and alert when over 80% capacity.
- Health/readiness endpoints: `/healthz` (liveness), `/readyz` (DB + storage checks), optional `/metrics` behind auth when Prometheus arrives.
- Backup plan: nightly SQLite dump + storage rsync (keep 7–14 days) and quarterly restore drills; document Postgres backup method before migration.
- Rate-limit configuration lives alongside Traefik middleware definitions for reproducibility.

## 7. Open Questions & Future Enhancements
- Define public deployment constraints: bandwidth limits, rate limiting, captcha.
- Determine account provisioning flow (admin invites vs. self-signup with approval).
- Optional password-protected downloads or email notifications.
- Consider encrypting files at rest if storing sensitive data.
- Multi-file uploads and zipped packages.
- Role-based permissions (e.g., admin vs member) if team grows.
- Internationalization or branding needs for frontend.
- Postgres migration checklist: UTC timestamps, TEXT vs VARCHAR, unique constraints, ON CONFLICT behavior, extensions, connection pooling, Alembic baseline.
- Malware scanning strategy (ClamAV vs. external service) and how to quarantine flagged files.

## 8. Collaboration Workflow
- Follow feature-branch workflow with PR reviews.
- Keep this plan updated as milestones complete.
- Use issues or checklist inside PRs to track subtasks.
- Announce when ready to tackle frontend milestone so we can adjust roadmap.

---
_Last updated: 2025-09-27_
