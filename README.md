<p align="center">
  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24"
       fill="none" stroke="#c2410c" stroke-width="1.5"
       stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 7v14"/>
    <path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>
  </svg>
</p>

<h1 align="center">Resurface</h1>

<p align="center">
  <strong>A personal library of book and article highlights, with a daily email that brings back the ones you're about to forget.</strong>
</p>

<p align="center">
  <a href="https://resurface.akshatgcodes.in">
    <img src="https://img.shields.io/badge/live_demo-c2410c-c2410c?style=flat-square" alt="Live Demo">
  </a>
  <img src="https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Docker_Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker Compose">
  <img src="https://img.shields.io/badge/license-GPL--3.0-c2410c?style=flat-square" alt="License">
</p>

---

## What is Resurface?

You highlight a great passage, and six months later you've forgotten it existed. Resurface stores highlights, articles and notes, tags them, and every morning emails you five worth rereading.

The five aren't random. A **spaced-repetition score runs in SQL**: each highlight has a review interval that doubles every time you see it (1 day, 2, 4, 8…), so new ideas come back often and well-known ones fade out, while anything you've marked important returns about twice as often. No ML, just a formula Postgres can sort by.

> **Live demo →** [resurface.akshatgcodes.in](https://resurface.akshatgcodes.in)
> Log in with the demo password `demo1234`. The demo builds digests but doesn't email them. The free host sleeps when idle, so the first load can take up to a minute.

---

## What you get

- **Library:** add highlights (book or article), save an article URL (title fetched for you), or jot a note. Tag, star, search across text, notes, titles and authors.
- **Daily digest:** APScheduler builds it at a set hour, emails it (HTML + plain text) and records it. "Send now" and a history of past digests are in the UI.
- **"Why this?"** Every pick shows its score and reason: *saved 40 days ago, seen 2×, next interval 4d, marked important*.
- **Redis:** caches the digest preview and stats with version-key invalidation, and holds a lock so only one replica sends the digest each day.
- **Docker Compose:** Postgres, Redis, Mailpit (catches the emails locally), API and an nginx-served frontend with one command.

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 19 · TypeScript · Vite · React Router · nginx in Docker |
| Backend | FastAPI · SQLAlchemy 2 · APScheduler · httpx |
| Data | PostgreSQL (SQLite for tests) · Redis |
| Email | SMTP; Mailpit locally |
| Infra | Docker Compose with health-checked dependencies |
| Tooling | uv · pytest · fakeredis · Vitest · ruff · GitHub Actions |

---

## Run it

```bash
docker compose up --build
```

- App: http://localhost:5173 (password `resurface`, change it in `.env`)
- Mailpit inbox: http://localhost:8025, where the digest emails land

Add a few highlights, open **Digest**, and click **Send digest now**. Without Docker, see [docs/SETUP.md](docs/SETUP.md).

---

## Engineering Decisions

**Why is the score computed in SQL?**
`ORDER BY score LIMIT 5` lets the database rank a library of any size without loading it into Python. Postgres and SQLite spell date maths differently, so a tiny custom SQLAlchemy construct (`days_between`) compiles to `EXTRACT(EPOCH …)` on Postgres and `julianday()` on SQLite. The scoring tests run on both.

**Why versioned cache keys instead of deleting entries?**
Every write bumps a counter that's part of each cache key. Old entries become unreachable at once and expire on their own, so there's no tracking of which keys a highlight affects.

**Why does saving a URL need SSRF protection?**
The server fetches whatever URL you type. Without checks, "saving" `http://169.254.169.254/` or `http://redis:6379` would make it read cloud credentials or internal services. Hosts must resolve to public IPs, and every redirect is re-checked.

**What would you do differently in v2?**
Let the reader rate each resurfaced highlight ("knew it" / "forgot") and adjust the interval like SM-2, instead of doubling it no matter what.

More in [docs/DECISIONS.md](docs/DECISIONS.md).

---

## Docs

| Document | Description |
|---|---|
| [PRD](docs/PRD.md) | Product requirements: goals, user stories, non-goals |
| [Architecture](docs/ARCHITECTURE.md) | Services, scoring, caching, digest flow |
| [Decisions](docs/DECISIONS.md) | Every major technical decision and why |
| [Setup](docs/SETUP.md) | Docker and non-Docker setup, env vars |
| [Deploy](docs/DEPLOY.md) | Deployment notes |
| [Contributing](CONTRIBUTING.md) | How to propose changes |
| [Changelog](CHANGELOG.md) | What changed in each release |
| [Security](SECURITY.md) | How to report a vulnerability |

---

<div align="center">

<h3>Akshat Gupta</h3>

<a href="https://akshatgcodes.in"><img src="https://img.shields.io/badge/Website-akshatgcodes.in-111111?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"></a>
<a href="https://linkedin.com/in/akshatgcodes"><img src="https://img.shields.io/badge/LinkedIn-akshatgcodes-0A66C2?style=flat-square" alt="LinkedIn"></a>
<a href="https://github.com/akshatgcodes"><img src="https://img.shields.io/badge/GitHub-akshatgcodes-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
<a href="mailto:akshatgcodes@gmail.com"><img src="https://img.shields.io/badge/Email-akshatgcodes%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>

</div>
