import type { Site } from "./types";

export const site: Site = {
  name: "Resurface",
  letter: "R",
  title: "Resurface — bring back the highlights you're about to forget",
  description:
    "A personal library of book and article highlights, with a daily email that brings back the ones you're about to forget.",
  meta: ["live", "highlights + daily digest", "GPLv3"],
  headline: ["The highlights you", "were about to forget."],
  intro:
    "You highlight a great passage, and six months later you've forgotten it existed. Resurface keeps your highlights, articles and notes, and every morning brings back five worth rereading.",
  primary: { label: "Open Resurface", href: "/app/" },
  repo: "https://github.com/akshatgcodes/Resurface",
  note: "Demo password: `demo1234`. The live demo builds digests but doesn't email them; with SMTP set up, your own copy does.",
  xfactor: {
    title: "Five picks a day, not five random ones.",
    intro:
      "A spaced-repetition score decides what comes back. New ideas return often, ones you know well fade out, and nothing needs machine learning.",
    features: [
      {
        icon: "×2",
        title: "Doubling intervals",
        body: "Each highlight's review interval doubles every time it's shown: 1 day, 2, 4, 8… Anything you've marked important comes back about twice as often.",
      },
      {
        icon: "Σ",
        title: "Ranked in SQL",
        body: "`ORDER BY score LIMIT 5` lets the database rank a library of any size. A small SQLAlchemy construct compiles the date maths for Postgres and SQLite alike.",
      },
      {
        icon: "?",
        title: "\"Why this?\"",
        body: "Every pick shows its score and reason: saved 40 days ago, seen 2×, next interval 4d, marked important.",
      },
    ],
  },
  preview: {
    intro: "The library with tags and search, the next digest with each pick's score, and the email it sends.",
    shots: [
      { src: "/shots/library.png", alt: "Library of highlights with tags, stars and a search box", caption: "Library" },
      { src: "/shots/digest.png", alt: "Next digest: five highlights, each with its score and reason", caption: "Next digest" },
      { src: "/shots/email.png", alt: "The digest email with five highlights", caption: "Digest email" },
    ],
  },
  stack: ["React 19", "TypeScript", "Vite", "FastAPI", "SQLAlchemy 2", "APScheduler", "PostgreSQL", "Redis", "SMTP", "Docker Compose", "pytest", "Vitest"],
  concepts: [
    { title: "Versioned cache keys", body: "Every write bumps a counter that's part of each Redis key, so stale entries become unreachable at once and expire on their own." },
    { title: "One sender per day", body: "A Redis lock makes sure only one replica sends the digest, even with several API instances running." },
    { title: "Redis is optional", body: "Without Redis, or when it's down, everything is simply computed fresh." },
    { title: "SSRF-safe URL saving", body: "Saving a URL fetches its title, so hosts must resolve to public IPs and every redirect is re-checked." },
    { title: "HTML and text email", body: "The digest goes out as both, with a link back to the library; Mailpit catches it locally." },
    { title: "Scoring tested on two databases", body: "The ranking tests run on SQLite and on Postgres, so the date maths can't silently differ." },
  ],
  run: {
    title: "Run your own",
    intro: "Docker Compose starts Postgres, Redis, Mailpit, the API and the app with one command.",
    blocks: [
      {
        title: "Docker",
        steps: [
          { text: "Clone and start everything:", cmd: "git clone https://github.com/akshatgcodes/Resurface\ncd Resurface && docker compose up --build" },
          { text: "Open the app (password `resurface`):", cmd: "http://localhost:5173" },
          { text: "Digest emails land in Mailpit:", cmd: "http://localhost:8025" },
        ],
      },
    ],
  },
  tagline: "highlights that come back before you forget them.",
};
