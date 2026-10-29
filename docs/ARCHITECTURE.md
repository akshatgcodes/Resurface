# Architecture

```
 Browser ──▶ web (nginx :5173)
             ├─ /        React SPA (Library, Digest)
             └─ /api/ ─▶ api (FastAPI :8000)
                          ├─ routers/library.py   highlights · articles · sources · tags
                          ├─ routers/digest.py    preview · send · history · stats
                          ├─ scoring.py           score in SQL (days_between ÷ interval)
                          ├─ cache.py             versioned keys · lock · claim_once ──▶ redis
                          ├─ fetch.py             title fetch with SSRF guard ──▶ the web
                          ├─ digest.py            build · email · APScheduler cron ──▶ SMTP (mailpit)
                          └─ SQLAlchemy ──────────────────────────────────────────▶ db (postgres)
```

## Data model

```
sources     id · kind (article|book|note) · title · author · url · created_at
highlights  id · source_id → sources · text · note · important · created_at
            last_surfaced_at · surfaced_count · interval_days
tags        id · name (unique)
highlight_tags  highlight_id · tag_id
digests     id · created_at · highlight_ids (JSON) · picks (JSON snapshot) · emailed_to · trigger
```

`digests.picks` snapshots each highlight with its score and reason at send time, so history shows why something was picked even after it's edited or deleted.

## Scoring

```
last_seen = COALESCE(last_surfaced_at, created_at)
score     = days_between(now, last_seen) / interval_days × (2 if important else 1)
```

`days_between` is a SQLAlchemy `FunctionElement` with per-dialect compilation:

| Dialect | SQL |
|---|---|
| PostgreSQL | `EXTRACT(EPOCH FROM (now - last_seen)) / 86400.0` |
| SQLite | `julianday(now) - julianday(last_seen)` |

Surfacing a highlight sets `last_surfaced_at = now`, `surfaced_count += 1`, `interval_days = min(interval_days × 2, 128)`.

## Digest flow

1. **Trigger:** APScheduler cron at `DIGEST_HOUR` in `DIGEST_TIMEZONE`, or `POST /api/digest/send`
2. **Once per day (scheduled only):** `claim_once("digest:YYYY-MM-DD")` is a Redis `SET NX EX 26h`; other replicas or a restarted process skip
3. `ranked()` → top `DIGEST_SIZE` by score; snapshot picks with reasons
4. Mark each surfaced, save a `Digest` row, bump the cache version
5. If `DIGEST_TO` and `SMTP_HOST` are set, render HTML + text and send; a mail failure is logged and the digest stays saved

## Caching

| Key | TTL | Invalidated by |
|---|---|---|
| `resurface:v{N}:preview:{size}` | 5 min | any write (version bump) |
| `resurface:v{N}:stats` | 5 min | any write |

Responses carry `X-Cache: HIT | MISS | BYPASS`. Redis errors fall back to computing (`BYPASS`). `cache.lock()` (SET NX + compare-and-delete Lua script) is available for mutual exclusion.

## Article fetch

1. Scheme must be http/https; every address the host resolves to must be global (no loopback, private, link-local, metadata)
2. Redirects are followed manually (max 4), each hop re-checked
3. Only HTML is parsed; body capped at 512 KB; 8s timeout
4. Title from `og:title`, then `<title>`; author from `<meta name="author">`
5. Any failure saves the article anyway with the URL as its title and returns `fetch_error`

## API

| Method | Path |
|---|---|
| POST | `/api/auth/login` · `/api/auth/logout` · GET `/api/auth/me` |
| GET / POST | `/api/highlights` (`q`, `tag`, `important`, `source_id`, `limit`, `offset`) |
| PATCH / DELETE | `/api/highlights/{id}` |
| POST | `/api/articles` |
| GET / DELETE | `/api/sources` · `/api/sources/{id}` |
| GET | `/api/tags` |
| GET | `/api/digest/preview` · `/api/stats` (cached) |
| POST | `/api/digest/send` |
| GET | `/api/digests` · `/api/digests/{id}` |

---

<div align="center">

<h3>Akshat Gupta</h3>

<a href="https://akshatgcodes.in"><img src="https://img.shields.io/badge/Website-akshatgcodes.in-111111?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"></a>
<a href="https://linkedin.com/in/akshatgcodes"><img src="https://img.shields.io/badge/LinkedIn-akshatgcodes-0A66C2?style=flat-square" alt="LinkedIn"></a>
<a href="https://github.com/akshatgcodes"><img src="https://img.shields.io/badge/GitHub-akshatgcodes-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
<a href="mailto:akshatgcodes@gmail.com"><img src="https://img.shields.io/badge/Email-akshatgcodes%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>

</div>
