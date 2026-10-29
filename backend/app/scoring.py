"""Spaced-repetition-style ranking, computed in SQL.

Every highlight has an `interval_days` that doubles each time it's surfaced (1, 2, 4, 8 …
capped at MAX_INTERVAL). A highlight is "due" when the time since it was last seen (or
saved, if never seen) reaches its interval:

    score = days_since_last_seen / interval_days        (≥ 1 means due)
    score × IMPORTANT_BOOST                             for highlights marked important

So the digest prefers things you haven't seen in a long time, relative to how well you
already know them, and important ones come back roughly twice as often. No ML, just a
formula the database can sort by.
"""

from datetime import UTC, datetime

from sqlalchemy import case, func, literal, select
from sqlalchemy.orm import Session

from app.db import days_between
from app.models import Highlight

IMPORTANT_BOOST = 2.0
MAX_INTERVAL = 128.0


def utcnow() -> datetime:
    # Naive UTC, matching how the DateTime columns are stored
    return datetime.now(UTC).replace(tzinfo=None)


def score_expr(now: datetime):
    last_seen = func.coalesce(Highlight.last_surfaced_at, Highlight.created_at)
    base = days_between(literal(now), last_seen) / Highlight.interval_days
    return base * case((Highlight.important, IMPORTANT_BOOST), else_=1.0)


def ranked(db: Session, now: datetime, limit: int) -> list[tuple[Highlight, float]]:
    score = score_expr(now).label("score")
    # id breaks ties deterministically (oldest first) so tests and digests are stable
    rows = db.execute(
        select(Highlight, score).order_by(score.desc(), Highlight.id).limit(limit)
    ).all()
    return [(h, float(s)) for h, s in rows]


def reason(h: Highlight, score: float, now: datetime) -> str:
    last = h.last_surfaced_at or h.created_at
    days = max((now - last).total_seconds() / 86400, 0)
    when = "saved" if h.last_surfaced_at is None else "last seen"
    parts = [f"{when} {days:.0f} day{'s' if round(days) != 1 else ''} ago"]
    if h.surfaced_count:
        parts.append(f"seen {h.surfaced_count}×, next interval {h.interval_days:g}d")
    if h.important:
        parts.append("marked important")
    return ", ".join(parts)


def mark_surfaced(h: Highlight, now: datetime) -> None:
    h.last_surfaced_at = now
    h.surfaced_count += 1
    h.interval_days = min(h.interval_days * 2, MAX_INTERVAL)
