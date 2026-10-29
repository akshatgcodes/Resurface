from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

highlight_tags = Table(
    "highlight_tags",
    Base.metadata,
    Column("highlight_id", ForeignKey("highlights.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Source(Base):
    """Where highlights come from: an article URL, a book, or a standalone note."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(10))  # article | book | note
    title: Mapped[str] = mapped_column(String(500))
    author: Mapped[str | None] = mapped_column(String(200))
    url: Mapped[str | None] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    highlights: Mapped[list["Highlight"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)


class Highlight(Base):
    __tablename__ = "highlights"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    important: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Spaced-repetition state (see app/scoring.py)
    last_surfaced_at: Mapped[datetime | None] = mapped_column(DateTime)
    surfaced_count: Mapped[int] = mapped_column(Integer, default=0)
    interval_days: Mapped[float] = mapped_column(Float, default=1.0)

    source: Mapped[Source] = relationship(back_populates="highlights")
    tags: Mapped[list[Tag]] = relationship(secondary=highlight_tags, lazy="selectin")


class Digest(Base):
    __tablename__ = "digests"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    highlight_ids: Mapped[list[int]] = mapped_column(JSON)
    # Score + reason per highlight at the moment it was picked, for the "why this?" UI
    picks: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    emailed_to: Mapped[str | None] = mapped_column(String(320))
    trigger: Mapped[str] = mapped_column(String(10))  # schedule | manual
