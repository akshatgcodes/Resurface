"""Scoring runs in SQL, so it's tested on SQLite and, when TEST_POSTGRES_URL is set
(e.g. postgresql+psycopg://postgres:test@localhost:55432/postgres), on Postgres too."""

import os
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import scoring
from app.db import Base
from app.models import Highlight, Source

NOW = datetime(2024, 9, 20, 8, 0)

ENGINES = ["sqlite://"]
if os.environ.get("TEST_POSTGRES_URL"):
    ENGINES.append(os.environ["TEST_POSTGRES_URL"])


@pytest.fixture(params=ENGINES, ids=lambda u: u.split(":")[0].split("+")[0])
def db(request):
    engine = create_engine(request.param)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    Base.metadata.drop_all(engine)
    engine.dispose()


def add(db, text, saved_days_ago, **kw):
    src = Source(kind="book", title="Book")
    h = Highlight(text=text, source=src, created_at=NOW - timedelta(days=saved_days_ago), **kw)
    db.add(h)
    db.commit()
    return h


def order(db, limit=10):
    return [h.text for h, _ in scoring.ranked(db, NOW, limit)]


def test_older_highlights_rank_first(db):
    add(db, "new", 1)
    add(db, "old", 30)
    add(db, "mid", 10)
    assert order(db) == ["old", "mid", "new"]


def test_score_is_days_over_interval(db):
    add(db, "a", 6, interval_days=4.0)
    [(_, score)] = scoring.ranked(db, NOW, 1)
    assert score == pytest.approx(1.5)


def test_important_counts_double(db):
    add(db, "plain", 10)
    add(db, "important", 6, important=True)
    assert order(db) == ["important", "plain"]


def test_recently_surfaced_drops_down(db):
    seen = add(db, "seen yesterday", 60)
    add(db, "never seen", 5)
    scoring.mark_surfaced(seen, NOW - timedelta(days=1))
    db.commit()
    assert order(db) == ["never seen", "seen yesterday"]


def test_interval_doubles_and_caps(db):
    h = add(db, "x", 1)
    for _ in range(10):
        scoring.mark_surfaced(h, NOW)
    assert h.surfaced_count == 10
    assert h.interval_days == scoring.MAX_INTERVAL


def test_well_known_highlight_waits_longer(db):
    # Both last seen 10 days ago, but one has been reviewed many times (interval 32)
    fresh = add(db, "seen once", 100, last_surfaced_at=NOW - timedelta(days=10), interval_days=2)
    known = add(db, "seen often", 100, last_surfaced_at=NOW - timedelta(days=10), interval_days=32)
    assert order(db) == [fresh.text, known.text]


def test_limit(db):
    for i in range(8):
        add(db, f"h{i}", i + 1)
    assert len(order(db, limit=5)) == 5


def test_reason_text():
    h = Highlight(
        text="t",
        created_at=NOW - timedelta(days=12),
        surfaced_count=0,
        interval_days=1,
        important=True,
    )
    assert scoring.reason(h, 24, NOW) == "saved 12 days ago, marked important"
    h.last_surfaced_at, h.surfaced_count, h.interval_days = NOW - timedelta(days=1), 3, 8
    h.important = False
    assert scoring.reason(h, 0.1, NOW) == "last seen 1 day ago, seen 3×, next interval 8d"
