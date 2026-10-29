# PRD: Resurface

## Problem

Highlights pile up in Kindle exports, browser extensions and notes apps, and almost none get read again. Random "daily quote" features resurface things, but with no sense of what you've already seen or what matters to you.

## Goal

One place for highlights, articles and notes, plus a daily digest that picks what's worth rereading using a simple, explainable spaced-repetition rule.

## User

A single reader running their own instance.

## User stories

| As a reader I want to… | So that… |
|---|---|
| paste a highlight with its book and author | it's stored with its source |
| save an article URL and have its title filled in | saving is fast |
| tag and star highlights, and search everything | I can find things again |
| get five highlights by email each morning | I reread without having to open the app |
| see why each one was picked | the digest feels deliberate, not random |
| send a digest on demand and see past ones | I can test it and look back |

## Requirements

- Sources (book / article / note) with highlights; tags (normalised to lowercase-hyphenated); important flag; notes
- Search (text, note, source title, author), filter by tag and important, pagination
- Article save with server-side title/author fetch, safe against SSRF
- Score = days since last seen ÷ interval, ×2 if important; interval doubles on each surfacing (max 128 days)
- Daily scheduled digest at a configurable hour and timezone, sent at most once per day across replicas
- Manual "send now", digest preview, history
- Redis caching of preview and stats; app keeps working if Redis is down
- One-command local stack with Docker Compose

## Non-goals

- Multi-user accounts
- Kindle/Readwise import (v2)
- Reader feedback adjusting intervals (v2)

---

<div align="center">

<h3>Akshat Gupta</h3>

<a href="https://akshatgcodes.in"><img src="https://img.shields.io/badge/Website-akshatgcodes.in-111111?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"></a>
<a href="https://linkedin.com/in/akshatgcodes"><img src="https://img.shields.io/badge/LinkedIn-akshatgcodes-0A66C2?style=flat-square" alt="LinkedIn"></a>
<a href="https://github.com/akshatgcodes"><img src="https://img.shields.io/badge/GitHub-akshatgcodes-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
<a href="mailto:akshatgcodes@gmail.com"><img src="https://img.shields.io/badge/Email-akshatgcodes%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>

</div>
