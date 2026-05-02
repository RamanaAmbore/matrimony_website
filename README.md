# marathakalyanam

Matrimonial site for Telugu-Maratha people settled in Andhra Pradesh and Telangana. Production domain: **marathakalyanam.com**.

## Stack

- **Backend:** Python · Litestar (async ASGI) · SQLAlchemy 2.x · msgspec · Alembic · Pillow + OpenCV
- **Frontend:** SvelteKit (Svelte 5) · TailwindCSS
- **Database:** PostgreSQL 16
- **Local dev infra:** docker-compose (Postgres + Mailhog)

## Quick start

```bash
# 1. Bring up local infra
docker compose up -d

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp ../.env.example ../.env
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Then open <http://localhost:5173> for the site and <http://localhost:8025> for Mailhog (captures all outbound email in dev).

See [CLAUDE.md](CLAUDE.md) for architecture and conventions.
