# Indicator Library (UNIDO)

FastAPI web application for managing, exploring, and exporting industrial indicators, with bilingual UI (EN/AR), AI-assisted features, and deployment under a reverse-proxy subpath (`/indicator-library`).

## Stack
- Backend: FastAPI, SQLAlchemy, Uvicorn
- Templates/UI: Jinja2 + HTML/CSS/JS
- DB: SQLite by default, PostgreSQL supported via `DATABASE_URL`
- Auth: JWT + bcrypt password hashing
- Optional AI: OpenAI API (`OPENAI_API_KEY`)

## Main Features
- Indicator catalog and filtering dashboard
- Upload CSV data (`indicators` and `values`)
- Tracking and trend views
- Overview metrics page
- User management and permissions
- Department views/policies + Excel export
- EN/AR language support (including RTL)

## Project Structure
- `main.py`: app bootstrap, HTML routes, dashboard logic
- `auth.py`: login/register + token validation
- `db.py`: DB engine/session initialization (`Base.metadata.create_all`)
- `models.py`: ORM models
- `routers/`: modular routes (permissions, departments, translate)
- `templates/`: Jinja templates
- `static/`: images/translations/assets
- `start.sh`: production-safe Uvicorn startup wrapper
- `Dockerfile`: container build/run

## Configuration
Environment variables:
- `OPENAI_API_KEY` (optional, required for AI translation/prioritization features)
- `DATABASE_URL` (optional; default: `sqlite:///./indicator_system.db`)
- `SECRET_KEY` (recommended in non-dev environments)
- `HOST` (optional; default `0.0.0.0`)
- `PORT` (optional; default `8000`)
- `ROOT_PATH` (optional; default `/indicator-library`)

## Run Locally
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./start.sh
```

App URL:
- `http://localhost:8000/indicator-library/`

## Docker / Podman
Build:
```bash
docker build -t indicator-library .
```

Run:
```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=YOUR_KEY \
  -e ROOT_PATH=/indicator-library \
  indicator-library
```

`start.sh` enforces safe defaults and enables `--proxy-headers`, which is required for NGINX/Cloudflare-style proxying.

## Reverse Proxy Notes (NGINX)
Expected external context path: `/indicator-library/`.

The app includes middleware that accepts both:
- proxied requests where prefix is stripped before reaching app
- direct local requests that still include `/indicator-library/...`

## Utility Scripts
- `create_superuser.py`: create admin user
- `create_user.py`: create user
- `delete_user.py`: delete user
- `seed_demo_data.py`: load demo data
- `seeds_permissions.py`: seed permissions

## Pre-push Checklist
- Start app with `./start.sh`
- Verify login + dashboard load under `/indicator-library/`
- Verify static assets load (logo/CSS)
- Verify `Contact` toggle in sidebar
- Ensure local DB artifacts are not unintentionally committed
