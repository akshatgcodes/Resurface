"""Build, record and (optionally) email a digest."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app import cache, mail, scoring
from app.config import settings
from app.db import SessionLocal
from app.models import Digest
from app.serialize import highlight_dict

log = logging.getLogger("resurface.digest")


def _picks(ranked: list, now: datetime) -> list[dict]:
    return [
        highlight_dict(h)
        | {"score": round(score, 2), "due": score >= 1, "reason": scoring.reason(h, score, now)}
        for h, score in ranked
    ]


def preview(db: Session, now: datetime, size: int) -> list[dict]:
    """What a digest would contain right now, without marking anything as seen."""
    return _picks(scoring.ranked(db, now, size), now)


def build(db: Session, now: datetime, size: int, trigger: str) -> Digest:
    ranked = scoring.ranked(db, now, size)
    # Snapshot the reasons before updating, so the digest explains why each was picked
    picks = _picks(ranked, now)
    for h, _ in ranked:
        scoring.mark_surfaced(h, now)
    digest = Digest(highlight_ids=[p["id"] for p in picks], picks=picks, trigger=trigger)
    db.add(digest)
    db.commit()
    db.refresh(digest)
    cache.bump_version()

    if picks and settings.digest_to and settings.smtp_host:
        subject, text, body = mail.render(picks, settings.public_url)
        try:
            mail.send(settings.digest_to, subject, text, body)
            digest.emailed_to = settings.digest_to
            db.commit()
        except Exception:  # noqa: BLE001 — the digest is saved even if email fails
            log.exception("digest email failed")
    return digest


def run_scheduled() -> None:
    tz = ZoneInfo(settings.digest_timezone)
    today = datetime.now(tz).date().isoformat()
    # Once per calendar day across all replicas and restarts
    if not cache.claim_once(f"digest:{today}", ttl=26 * 3600):
        log.info("digest for %s already sent by another worker", today)
        return
    with SessionLocal() as db:
        d = build(db, scoring.utcnow(), settings.digest_size, "schedule")
        log.info("scheduled digest %s: %d highlights", d.id, len(d.highlight_ids))


def make_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=ZoneInfo(settings.digest_timezone))
    scheduler.add_job(
        run_scheduled,
        "cron",
        hour=settings.digest_hour,
        minute=0,
        id="daily-digest",
        coalesce=True,
        misfire_grace_time=3600,
    )
    return scheduler
