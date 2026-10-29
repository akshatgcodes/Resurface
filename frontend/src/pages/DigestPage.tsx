import { useEffect, useState } from "react";
import { api } from "../api";
import type { Digest, DigestPick, Stats } from "../types";
import HighlightCard from "../components/HighlightCard";

export default function DigestPage() {
  const [picks, setPicks] = useState<DigestPick[] | null>(null);
  const [history, setHistory] = useState<Digest[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [sending, setSending] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [open, setOpen] = useState<number | null>(null);

  const load = () => {
    api.preview().then((r) => setPicks(r.picks));
    api.digests().then(setHistory);
    api.stats().then(setStats);
  };
  useEffect(load, []);

  const sendNow = async () => {
    setSending(true);
    try {
      const d = await api.sendDigest();
      setNotice(
        d.picks.length === 0
          ? "Nothing to send yet. Add some highlights first."
          : d.emailed_to
            ? `Sent ${d.picks.length} highlights to ${d.emailed_to}`
            : `Built a digest of ${d.picks.length}. Email isn't configured, so it's saved below only.`,
      );
      load();
    } finally {
      setSending(false);
    }
  };

  const cfg = stats?.digest;
  return (
    <main className="page">
      <div className="page-head">
        <div>
          <h1>Next digest</h1>
          {cfg && (
            <p className="muted small">
              {cfg.scheduled ? `Every day at ${String(cfg.hour).padStart(2, "0")}:00 (${cfg.timezone})` : "Scheduler off: send manually"} ·{" "}
              {cfg.email ? "emailed" : "email not configured"} · {cfg.size} highlights
            </p>
          )}
        </div>
        <button className="btn btn-primary" onClick={sendNow} disabled={sending}>
          {sending ? "Sending…" : "Send digest now"}
        </button>
      </div>

      {notice && (
        <p className="notice" role="status">
          {notice}
        </p>
      )}

      <details className="explain">
        <summary>How are these picked?</summary>
        <p>
          Each highlight has a review interval that doubles every time it appears in a digest (1 day, 2, 4, 8…). Its score is{" "}
          <em>days since you last saw it ÷ its interval</em>, doubled if it's marked important. The top {cfg?.size ?? 5} by score are
          picked; a score of 1 or more means it's due.
        </p>
      </details>

      {picks?.length === 0 && <div className="empty muted">Add highlights to your library and they'll show up here.</div>}
      <div className="list">
        {picks?.map((p) => (
          <HighlightCard
            key={p.id}
            h={p}
            footer={
              <span className="small">
                <span className={p.due ? "badge badge-due" : "badge"}>{p.due ? "due" : "not due yet"}</span>{" "}
                <span className="muted">
                  score {p.score.toFixed(2)} · {p.reason}
                </span>
              </span>
            }
          />
        ))}
      </div>

      {history.length > 0 && (
        <section className="history">
          <h2>Past digests</h2>
          <ul>
            {history.map((d) => (
              <li key={d.id}>
                <button className="history-row" onClick={() => setOpen(open === d.id ? null : d.id)} aria-expanded={open === d.id}>
                  <span>{new Date(d.created_at + "Z").toLocaleString()}</span>
                  <span className="muted small">
                    {d.picks.length} highlights · {d.trigger} · {d.emailed_to ? `emailed to ${d.emailed_to}` : "not emailed"}
                  </span>
                </button>
                {open === d.id && (
                  <ol className="history-picks">
                    {d.picks.map((p) => (
                      <li key={p.id}>
                        <q>{p.text}</q> <span className="muted small">— {p.source.title}</span>
                      </li>
                    ))}
                  </ol>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
