# Decisions

### 1. Doubling intervals, not a full SM-2
**Decision:** Each surfacing doubles the highlight's interval (max 128 days). Important highlights score ×2.
**Why:** Without reader feedback there's nothing to grade, and doubling already gives the key property: new items come back often, familiar ones rarely. It's explainable in one sentence and shown in the UI.
**Trade-off:** Something you forgot still gets a longer interval. v2: "knew it / forgot" feedback.

### 2. Rank in SQL with a dialect-aware function
**Decision:** The score is an SQL expression; `days_between` compiles per dialect.
**Why:** The database sorts and limits; Python never loads the whole library. Tests run the same query on SQLite and Postgres.

### 3. Versioned cache keys
**Decision:** Writes `INCR resurface:version`; keys embed the version.
**Why:** Invalidation is one atomic command with no key bookkeeping; stale entries expire by TTL.
**Trade-off:** Any write invalidates everything cached. With two cached views, that's fine.

### 4. Redis is optional
**Decision:** No `REDIS_URL` or a Redis outage means compute fresh (`X-Cache: BYPASS`).
**Why:** A cache failing shouldn't take the app down. Tests and non-Docker dev run without Redis.

### 5. Scheduler in the API process, de-duplicated through Redis
**Decision:** APScheduler runs inside FastAPI. The scheduled job first claims `digest:<date>` with `SET NX EX`.
**Why:** No separate worker container for one daily job, and scaling the API to several replicas still sends one digest.
**Trade-off:** If the API is down at the scheduled hour, `misfire_grace_time=1h` catches it only if it comes back within the hour.

### 6. Snapshot digest picks
**Decision:** `digests.picks` stores the highlight, score and reason at send time.
**Why:** History stays accurate after edits and deletions, and shows why each was picked then.

### 7. SSRF guard on article fetch
**Decision:** Resolve the host and reject non-global addresses, follow redirects manually and re-check each, cap size and time.
**Why:** The server fetching user-supplied URLs is the textbook SSRF setup, and in Compose the API can reach `redis` and `db` by name.

### 8. Saving never fails because the page did
**Decision:** If the title fetch fails, the article is saved with its URL as the title and the error is returned.
**Why:** Paywalls, timeouts and bot blocks are common; losing the save would be worse than a plain title.

### 9. Mailpit in Compose
**Decision:** Local SMTP goes to Mailpit, with its inbox at :8025.
**Why:** The full email path (SMTP, HTML rendering) is exercised locally without sending real mail or needing credentials.

---

<div align="center">

<h3>Akshat Gupta</h3>

<a href="https://akshatgcodes.in"><img src="https://img.shields.io/badge/Website-akshatgcodes.in-111111?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"></a>
<a href="https://linkedin.com/in/akshatgcodes"><img src="https://img.shields.io/badge/LinkedIn-akshatgcodes-0A66C2?style=flat-square" alt="LinkedIn"></a>
<a href="https://github.com/akshatgcodes"><img src="https://img.shields.io/badge/GitHub-akshatgcodes-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
<a href="mailto:akshatgcodes@gmail.com"><img src="https://img.shields.io/badge/Email-akshatgcodes%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>

</div>
