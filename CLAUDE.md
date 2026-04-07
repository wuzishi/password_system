# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (Python 3.12+, FastAPI)
```bash
cd backend
cp .env.example .env   # fill DATABASE_URL, JWT_SECRET, AES_KEY, FERNET_KEY
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend (Node 20+, Vue 3 + Vite)
```bash
cd frontend
npm install
npx vite --port 3000 --host 0.0.0.0    # dev
npm run build                           # production
```

### Docker (full stack + MySQL)
```bash
export DB_ROOT_PASSWORD=...
docker-compose up -d
```

### Security tests (full pentest suite, 45 checks)
```bash
cd security_tests
python pentest.py --base-url http://localhost:8000 --admin-user admin --admin-pass '...'
```
There is no unit test suite; `pentest.py` is the authoritative automated test harness.

## Architecture

Team password-management platform. Backend is a FastAPI monolith; frontend is a Vue 3 SPA served by nginx. MySQL 8 (utf8mb4) is the only datastore.

### Backend layout (`backend/app/`)
- `api/` — route modules mounted in `main.py`: `auth`, `passwords`, `ws` (WebSocket SSH terminal + remote password change), `sftp`, `approvals`, `permissions`, `users`, `teams`, `audit`.
- `models/` — SQLAlchemy ORM.
- `schemas/` — Pydantic validation.
- `services/` — crypto, auth, scheduler, SSH/SFTP (Paramiko).
- `middleware/` — security headers (CSP / HSTS / X-Frame-Options / Referrer-Policy).
- `core/` — role and permission definitions (dynamic RBAC matrix, stored in DB and editable from the admin UI; do not hardcode permission checks).

### Crypto
Passwords are stored AES-256-GCM encrypted with Fernet-compatible migration path. Viewing a password requires a second-factor re-auth with the user's login password; this opens a **5-minute decryption session**. Touch `services/` crypto helpers rather than reimplementing.

### Auth
JWT dual-token: 30 min access + 7 day refresh. Logout works via a `jti` blacklist — when invalidating tokens, go through the blacklist, not by rotating secrets. slowapi rate-limits login / decrypt / verify endpoints.

### WebSocket terminal + SFTP coupling
`api/ws.py` brokers an xterm.js ↔ Paramiko SSH channel. `FileManager.vue` and `WebTerminal.vue` are shown side-by-side via `SplitPane.vue`; the file manager's cwd tracks the terminal by **polling procfs every 2s** (see recent fixes `5d85f34`, `63dc534` — `run_in_executor`, no PTY marker injection). If you touch cwd sync, preserve this polling model.

Remote password change (servers + MySQL/PostgreSQL) streams command/SQL output through the same WS channel and is **atomic**: verify → change → confirm → persist. Don't split these steps.

### Frontend (`frontend/src/`)
- `views/` — 13 page components; `components/` — shared (WebTerminal, FileManager, SplitPane, layout/AppLayout).
- `stores/` Pinia, `api/` axios clients, `router/` with permission guards that read the dynamic RBAC matrix from the backend.
- Theming is CSS-variable driven (dark/light toggle). UI is Chinese.

### Security model to respect when making changes
- 4 security levels (personal / high / medium / low) gate access; all users can *see* non-personal entries but actions require authorization.
- Approval workflow: unauthorized users file requests, admins approve → auto-grant.
- All sensitive ops (view/modify/delete/share) must write to the audit log.
- Admin account is created on first startup; the generated password is printed to the backend console.

## Environment variables
Required: `DATABASE_URL`, `JWT_SECRET`, `AES_KEY` (base64), `FERNET_KEY`.
Optional: `ADMIN_PASSWORD`, `CORS_ORIGINS`, `SMTP_HOST`, `SITE_URL`.
Key-generation commands live in `backend/.env.example`.
