from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import cache, digest, scoring
from app.auth import require_user
from app.config import settings
from app.db import get_db
from app.models import Digest, Highlight

router = APIRouter(prefix="/api", tags=["digest"], dependencies=[Depends(require_user)])

# Scores drift slowly (they're measured in days), so a few minutes of staleness is fine;
# any write invalidates immediately through the version bump
PREVIEW_TTL = 300


def _digest_dict(d: Digest) -> dict:
    return {
        "id": d.id,
        "created_at": d.created_at.isoformat(),
        "trigger": d.trigger,
        "emailed_to": d.emailed_to,
        "picks": d.picks,
    }


@router.get("/digest/preview")
def preview(
    response: Response,
    size: int = Query(settings.digest_size, ge=1, le=20),
    db: Session = Depends(get_db),
) -> dict:
    def compute():
        now = scoring.utcnow()
        return {"computed_at": now.isoformat(), "picks": digest.preview(db, now, size)}

    value, status = cache.cached_json(f"preview:{size}", PREVIEW_TTL, compute)
    response.headers["X-Cache"] = status
    return value


@router.post("/digest/send", status_code=201)
def send_now(db: Session = Depends(get_db)) -> dict:
    d = digest.build(db, scoring.utcnow(), settings.digest_size, "manual")
    return _digest_dict(d)


@router.get("/digests")
def history(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(Digest).order_by(Digest.id.desc()).limit(limit)).all()
    return [_digest_dict(d) for d in rows]


@router.get("/digests/{did}")
def get_digest(did: int, db: Session = Depends(get_db)) -> dict:
    d = db.get(Digest, did)
    if d is None:
        raise HTTPException(404, "Digest not found")
    return _digest_dict(d)


@router.get("/stats")
def stats(response: Response, db: Session = Depends(get_db)) -> dict:
    def compute():
        now = scoring.utcnow()
        score = scoring.score_expr(now)
        return {
            "highlights": db.scalar(select(func.count(Highlight.id))) or 0,
            "important": db.scalar(select(func.count()).where(Highlight.important)) or 0,
            "due": db.scalar(select(func.count()).where(score >= 1)) or 0,
            "never_surfaced": db.scalar(
                select(func.count()).where(Highlight.last_surfaced_at.is_(None))
            )
            or 0,
            "digest": {
                "size": settings.digest_size,
                "hour": settings.digest_hour,
                "timezone": settings.digest_timezone,
                "email": bool(settings.digest_to and settings.smtp_host),
                "scheduled": settings.scheduler_enabled,
            },
        }

    value, status = cache.cached_json("stats", PREVIEW_TTL, compute)
    response.headers["X-Cache"] = status
    return value
