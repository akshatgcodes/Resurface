# Deploy

Resurface is **not deployed yet**. The Compose file is the reference setup.

## Single server

Run `docker compose up -d --build` on a small VM, put a reverse proxy with TLS in front of the `web` service, and set in `.env`:

- `APP_PASSWORD`, `SESSION_SECRET` (long random values)
- `DIGEST_TO` and real `SMTP_*` settings (remove Mailpit or stop exposing port 8025)
- `PUBLIC_URL` to the public address

## Managed services

| Part | Option |
|---|---|
| Frontend | Vercel (`frontend/`, SPA rewrite to `index.html`, `VITE_API_URL` set) |
| API | Render web service from `backend/Dockerfile` |
| Database | Neon PostgreSQL |
| Redis | Upstash or Render Key Value |

With frontend and API on different domains, set `FRONTEND_URL` and `CROSS_SITE_COOKIES=true`. Keep `SCHEDULER_ENABLED=true` on the API; the Redis claim makes extra instances safe.

---

<div align="center">

<h3>Akshat Gupta</h3>

<a href="https://akshatgcodes.in"><img src="https://img.shields.io/badge/Website-akshatgcodes.in-111111?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"></a>
<a href="https://linkedin.com/in/akshatgcodes"><img src="https://img.shields.io/badge/LinkedIn-akshatgcodes-0A66C2?style=flat-square" alt="LinkedIn"></a>
<a href="https://github.com/akshatgcodes"><img src="https://img.shields.io/badge/GitHub-akshatgcodes-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
<a href="mailto:akshatgcodes@gmail.com"><img src="https://img.shields.io/badge/Email-akshatgcodes%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>

</div>
