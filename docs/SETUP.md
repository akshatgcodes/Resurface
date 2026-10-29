# Setup

## With Docker (recommended)

```bash
cp .env.example .env          # optional: change APP_PASSWORD, DIGEST_TO, SMTP
docker compose up --build
```

| URL | What |
|---|---|
| http://localhost:5173 | the app |
| http://localhost:8025 | Mailpit inbox (digest emails) |

The digest runs daily at `DIGEST_HOUR` (default 8:00 Asia/Kolkata). Use **Send digest now** on the Digest page to try it immediately.

## Without Docker

```bash
cd backend
uv sync
cp .env.example .env          # set APP_PASSWORD
uv run uvicorn app.main:app --reload      # SQLite, no Redis, no email

cd ../frontend
npm install
npm run dev                               # http://localhost:5173
```

## Environment variables (API)

| Variable | Default | Purpose |
|---|---|---|
| `APP_PASSWORD` | empty | login password (required) |
| `SESSION_SECRET` | insecure dev value | signs the session cookie |
| `DATABASE_URL` | `sqlite:///./resurface.db` | Postgres in Compose |
| `REDIS_URL` | empty | cache + scheduler de-duplication |
| `SCHEDULER_ENABLED` | `false` | run the daily digest job |
| `DIGEST_HOUR` / `DIGEST_TIMEZONE` / `DIGEST_SIZE` | `8` / `Asia/Kolkata` / `5` | |
| `DIGEST_TO` | empty | recipient; empty means build and save only |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_STARTTLS` | – / 587 / – / – / true | for Gmail use an app password |
| `MAIL_FROM` | `Resurface <digest@resurface.local>` | |
| `PUBLIC_URL` | `http://localhost:5173` | link in the email |
| `FRONTEND_URL` / `CROSS_SITE_COOKIES` | `http://localhost:5173` / `false` | CORS and cookies |

## Checks

```bash
cd backend && uv run ruff check . && uv run pytest
cd frontend && npm test && npm run build

# scoring on real Postgres
docker run -d --rm --name pgtest -e POSTGRES_PASSWORD=test -p 55432:5432 postgres:17-alpine
TEST_POSTGRES_URL=postgresql+psycopg://postgres:test@localhost:55432/postgres uv run pytest tests/test_scoring.py
```

---

<div align="center">

<h3>Akshat Gupta</h3>

<a href="https://akshatgcodes.in"><img src="https://img.shields.io/badge/Website-akshatgcodes.in-111111?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"></a>
<a href="https://linkedin.com/in/akshatgcodes"><img src="https://img.shields.io/badge/LinkedIn-akshatgcodes-0A66C2?style=flat-square" alt="LinkedIn"></a>
<a href="https://github.com/akshatgcodes"><img src="https://img.shields.io/badge/GitHub-akshatgcodes-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
<a href="mailto:akshatgcodes@gmail.com"><img src="https://img.shields.io/badge/Email-akshatgcodes%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>

</div>
