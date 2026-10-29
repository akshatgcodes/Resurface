from datetime import timedelta

from app import digest, fetch, mail, scoring
from app.db import SessionLocal
from app.models import Highlight


def add(user, text, **kw):
    r = user.post("/api/highlights", json={"text": text, **kw})
    assert r.status_code == 201, r.text
    return r.json()


def age(hid, days):
    """Pretend a highlight was saved `days` ago."""
    with SessionLocal() as db:
        h = db.get(Highlight, hid)
        h.created_at = scoring.utcnow() - timedelta(days=days)
        db.commit()


def test_requires_login(client):
    assert client.get("/api/highlights").status_code == 401
    assert client.post("/api/auth/login", json={"password": "nope"}).status_code == 401


def test_create_with_source_and_tags(user):
    h = add(
        user,
        "  Clarity about what matters provides clarity about what does not. ",
        tags=["#Focus", "deep work", "focus"],
        source={"kind": "book", "title": "Deep Work", "author": "Cal Newport"},
    )
    assert h["text"].startswith("Clarity") and h["text"].endswith("not.")
    assert h["tags"] == ["deep-work", "focus"]
    assert h["source"]["author"] == "Cal Newport"
    # Reuse the same source
    h2 = add(user, "Second", source_id=h["source"]["id"])
    assert h2["source"]["id"] == h["source"]["id"]


def test_bad_tag_rejected(user):
    r = user.post("/api/highlights", json={"text": "x", "tags": ["no/slash"]})
    assert r.status_code == 422


def test_search_filter_patch_delete(user):
    a = add(user, "Hooks let you use state", tags=["react"])
    add(user, "Ownership and borrowing", tags=["rust"], important=True)
    assert user.get("/api/highlights", params={"q": "HOOKS"}).json()["total"] == 1
    assert user.get("/api/highlights", params={"tag": "rust"}).json()["items"][0]["important"]
    assert user.get("/api/highlights", params={"important": True}).json()["total"] == 1

    patched = user.patch(
        f"/api/highlights/{a['id']}", json={"note": "re-read", "tags": ["react", "hooks"]}
    ).json()
    assert patched["note"] == "re-read" and patched["tags"] == ["hooks", "react"]
    assert {t["name"]: t["count"] for t in user.get("/api/tags").json()} == {
        "hooks": 1,
        "react": 1,
        "rust": 1,
    }

    assert user.delete(f"/api/highlights/{a['id']}").status_code == 204
    assert user.get("/api/highlights").json()["total"] == 1


def test_save_article_fetches_title(user, monkeypatch):
    monkeypatch.setattr(fetch, "fetch_meta", lambda url: ("How to Read a Paper", "S. Keshav"))
    r = user.post(
        "/api/articles",
        json={
            "url": "https://example.com/paper",
            "highlights": ["Read it three times", " "],
            "tags": ["papers"],
        },
    )
    body = r.json()
    assert (
        r.status_code == 201 and body["title"] == "How to Read a Paper" and body["highlights"] == 1
    )
    sources = user.get("/api/sources").json()
    assert sources[0]["highlights"] == 1 and sources[0]["author"] == "S. Keshav"


def test_save_article_survives_fetch_error(user):
    r = user.post("/api/articles", json={"url": "http://127.0.0.1:6379/"}).json()
    assert r["title"] == "http://127.0.0.1:6379/"
    assert "private network" in r["fetch_error"]


def test_preview_is_cached_until_a_write(user):
    old = add(user, "old one")
    age(old["id"], 20)
    r1 = user.get("/api/digest/preview")
    r2 = user.get("/api/digest/preview")
    assert (r1.headers["X-Cache"], r2.headers["X-Cache"]) == ("MISS", "HIT")
    assert r1.json()["picks"][0]["due"] is True

    add(user, "new one")
    r3 = user.get("/api/digest/preview")
    assert r3.headers["X-Cache"] == "MISS"
    assert len(r3.json()["picks"]) == 2


def test_send_digest_marks_surfaced_and_emails(user, monkeypatch):
    sent = []
    monkeypatch.setattr(digest.settings, "digest_to", "me@example.com")
    monkeypatch.setattr(digest.settings, "smtp_host", "mailpit")
    monkeypatch.setattr(mail, "send", lambda *a: sent.append(a))

    ids = []
    for i, days in enumerate([40, 5, 20, 1, 60, 10]):
        h = add(user, f"h{i}")
        age(h["id"], days)
        ids.append(h["id"])

    d = user.post("/api/digest/send").json()
    picked = [p["text"] for p in d["picks"]]
    assert picked == ["h4", "h0", "h2", "h5", "h1"]  # oldest first, top 5
    assert d["emailed_to"] == "me@example.com" and d["trigger"] == "manual"
    to, subject, text, body = sent[0]
    assert to == "me@example.com" and "5 highlights" in subject and "h4" in text

    h4 = user.get("/api/highlights", params={"q": "h4"}).json()["items"][0]
    assert h4["surfaced_count"] == 1 and h4["interval_days"] == 2.0
    # The one that wasn't picked now leads the next preview
    assert user.get("/api/digest/preview").json()["picks"][0]["text"] == "h3"
    assert user.get("/api/digests").json()[0]["id"] == d["id"]


def test_email_failure_still_saves_digest(user, monkeypatch):
    monkeypatch.setattr(digest.settings, "digest_to", "me@example.com")
    monkeypatch.setattr(digest.settings, "smtp_host", "mailpit")

    def boom(*a):
        raise OSError("smtp down")

    monkeypatch.setattr(mail, "send", boom)
    add(user, "x")
    d = user.post("/api/digest/send").json()
    assert d["emailed_to"] is None and len(d["picks"]) == 1


def test_scheduled_digest_runs_once_per_day(user):
    add(user, "x")
    digest.run_scheduled()
    digest.run_scheduled()
    history = user.get("/api/digests").json()
    assert len(history) == 1 and history[0]["trigger"] == "schedule"


def test_stats(user):
    h = add(user, "a", important=True)
    age(h["id"], 3)
    add(user, "b")
    s = user.get("/api/stats").json()
    assert (s["highlights"], s["important"], s["due"], s["never_surfaced"]) == (2, 1, 1, 2)
