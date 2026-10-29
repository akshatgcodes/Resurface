from app.models import Highlight, Source


def source_dict(s: Source) -> dict:
    return {"id": s.id, "kind": s.kind, "title": s.title, "author": s.author, "url": s.url}


def highlight_dict(h: Highlight) -> dict:
    return {
        "id": h.id,
        "text": h.text,
        "note": h.note,
        "important": h.important,
        "tags": sorted(t.name for t in h.tags),
        "source": source_dict(h.source),
        "created_at": h.created_at.isoformat(),
        "last_surfaced_at": h.last_surfaced_at.isoformat() if h.last_surfaced_at else None,
        "surfaced_count": h.surfaced_count,
        "interval_days": h.interval_days,
    }
