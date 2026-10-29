import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import cache, fetch
from app.auth import require_user
from app.db import get_db
from app.models import Highlight, Source, Tag, highlight_tags
from app.serialize import highlight_dict, source_dict

router = APIRouter(prefix="/api", tags=["library"], dependencies=[Depends(require_user)])

TAG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,49}$")


def _clean_tags(tags: list[str]) -> list[str]:
    """'#Deep Work ' -> 'deep-work'; dedupe; reject anything else odd."""
    out = sorted({t.strip().lower().lstrip("#").replace(" ", "-") for t in tags if t.strip()})
    bad = [t for t in out if not TAG_RE.match(t)]
    if bad:
        raise ValueError(f"invalid tag(s): {', '.join(bad)}")
    return out


class SourceIn(BaseModel):
    kind: str = Field(pattern="^(article|book|note)$")
    title: str = Field(min_length=1, max_length=500)
    author: str | None = Field(None, max_length=200)
    url: str | None = Field(None, max_length=2000)


class HighlightIn(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)
    note: str | None = Field(None, max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    important: bool = False
    source_id: int | None = None
    source: SourceIn | None = None

    @field_validator("tags")
    @classmethod
    def _tags(cls, v: list[str]) -> list[str]:
        return _clean_tags(v)


class HighlightPatch(BaseModel):
    text: str | None = Field(None, min_length=1, max_length=10_000)
    note: str | None = Field(None, max_length=5000)
    tags: list[str] | None = Field(None, max_length=20)
    important: bool | None = None

    @field_validator("tags")
    @classmethod
    def _tags(cls, v):
        return None if v is None else _clean_tags(v)


class ArticleIn(BaseModel):
    url: str = Field(min_length=8, max_length=2000)
    title: str | None = Field(None, max_length=500)
    highlights: list[str] = Field(default_factory=list, max_length=50)
    tags: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("tags")
    @classmethod
    def _tags(cls, v: list[str]) -> list[str]:
        return _clean_tags(v)


def _tags(db: Session, names: list[str]) -> list[Tag]:
    existing = {t.name: t for t in db.scalars(select(Tag).where(Tag.name.in_(names)))}
    for name in names:
        if name not in existing:
            existing[name] = Tag(name=name)
            db.add(existing[name])
    return [existing[n] for n in names]


def _get(db: Session, hid: int) -> Highlight:
    h = db.get(Highlight, hid)
    if h is None:
        raise HTTPException(404, "Highlight not found")
    return h


@router.get("/highlights")
def list_highlights(
    q: str | None = Query(None, max_length=200),
    tag: str | None = None,
    important: bool | None = None,
    source_id: int | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(Highlight).join(Source)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Highlight.text).like(like),
                func.lower(func.coalesce(Highlight.note, "")).like(like),
                func.lower(Source.title).like(like),
                func.lower(func.coalesce(Source.author, "")).like(like),
            )
        )
    if tag:
        stmt = stmt.where(Highlight.tags.any(Tag.name == tag))
    if important is not None:
        stmt = stmt.where(Highlight.important == important)
    if source_id is not None:
        stmt = stmt.where(Highlight.source_id == source_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(
        stmt.order_by(Highlight.created_at.desc(), Highlight.id.desc()).limit(limit).offset(offset)
    ).all()
    return {"total": total, "items": [highlight_dict(h) for h in rows]}


@router.post("/highlights", status_code=201)
def create_highlight(body: HighlightIn, db: Session = Depends(get_db)) -> dict:
    if body.source_id is not None:
        source = db.get(Source, body.source_id)
        if source is None:
            raise HTTPException(404, "Source not found")
    elif body.source is not None:
        source = Source(**body.source.model_dump())
        db.add(source)
    else:
        source = Source(kind="note", title="Notes")
        db.add(source)
    h = Highlight(
        text=body.text.strip(),
        note=body.note,
        important=body.important,
        source=source,
        tags=_tags(db, body.tags),
    )
    db.add(h)
    db.commit()
    db.refresh(h)
    cache.bump_version()
    return highlight_dict(h)


@router.patch("/highlights/{hid}")
def update_highlight(hid: int, body: HighlightPatch, db: Session = Depends(get_db)) -> dict:
    h = _get(db, hid)
    if body.text is not None:
        h.text = body.text.strip()
    if body.note is not None:
        h.note = body.note or None
    if body.important is not None:
        h.important = body.important
    if body.tags is not None:
        h.tags = _tags(db, body.tags)
    db.commit()
    cache.bump_version()
    return highlight_dict(h)


@router.delete("/highlights/{hid}", status_code=204)
def delete_highlight(hid: int, db: Session = Depends(get_db)) -> None:
    db.delete(_get(db, hid))
    db.commit()
    cache.bump_version()


@router.post("/articles", status_code=201)
def save_article(body: ArticleIn, db: Session = Depends(get_db)) -> dict:
    """Save a URL. The title is fetched from the page unless given."""
    title, author = body.title, None
    fetch_error = None
    if not title:
        try:
            title, author = fetch.fetch_meta(body.url)
        except fetch.FetchError as e:
            fetch_error = str(e)
        except httpx.HTTPError:
            # A dead or slow link shouldn't block saving; the URL becomes the title
            fetch_error = "Couldn't load the page"
    source = Source(kind="article", title=title or body.url, author=author, url=body.url)
    db.add(source)
    tags = _tags(db, body.tags)
    for text in body.highlights:
        if text.strip():
            db.add(Highlight(text=text.strip(), source=source, tags=tags))
    db.commit()
    db.refresh(source)
    cache.bump_version()
    return source_dict(source) | {"highlights": len(source.highlights), "fetch_error": fetch_error}


@router.get("/sources")
def list_sources(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        select(Source, func.count(Highlight.id))
        .outerjoin(Highlight)
        .group_by(Source.id)
        .order_by(Source.created_at.desc())
    ).all()
    return [source_dict(s) | {"highlights": n} for s, n in rows]


@router.delete("/sources/{sid}", status_code=204)
def delete_source(sid: int, db: Session = Depends(get_db)) -> None:
    s = db.get(Source, sid)
    if s is None:
        raise HTTPException(404, "Source not found")
    db.delete(s)
    db.commit()
    cache.bump_version()


@router.get("/tags")
def list_tags(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        select(Tag.name, func.count(highlight_tags.c.highlight_id))
        .join(highlight_tags)
        .group_by(Tag.name)
        .order_by(func.count().desc(), Tag.name)
    ).all()
    return [{"name": n, "count": c} for n, c in rows]
