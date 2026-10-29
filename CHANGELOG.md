# Changelog

All notable changes to **Resurface** are documented here.

---

## [Unreleased]

---

## [0.1.0] — 2026-10-29

### ✨ Added
- Library of sources (book, article, note) and highlights with tags, notes, important flag, search and filters
- Article saving with server-side title/author fetch, protected against SSRF
- Spaced-repetition scoring computed in SQL on PostgreSQL and SQLite
- Daily digest: preview with reasons, manual send, history, HTML/text email, APScheduler job sent once per day across replicas
- Redis caching with versioned keys and graceful fallback when Redis is unavailable
- Docker Compose stack with Postgres, Redis, Mailpit, API and nginx-served frontend

### 🧪 Tests
- Scoring (SQLite + optional Postgres), cache and lock, fetch guard, and API tests

---

[Unreleased]: https://github.com/akshatgcodes/Resurface/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/akshatgcodes/Resurface/releases/tag/v0.1.0

---

<div align="center">

<h3>Akshat Gupta</h3>

<a href="https://akshatgcodes.in"><img src="https://img.shields.io/badge/Website-akshatgcodes.in-111111?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"></a>
<a href="https://linkedin.com/in/akshatgcodes"><img src="https://img.shields.io/badge/LinkedIn-akshatgcodes-0A66C2?style=flat-square" alt="LinkedIn"></a>
<a href="https://github.com/akshatgcodes"><img src="https://img.shields.io/badge/GitHub-akshatgcodes-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
<a href="mailto:akshatgcodes@gmail.com"><img src="https://img.shields.io/badge/Email-akshatgcodes%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>

</div>
