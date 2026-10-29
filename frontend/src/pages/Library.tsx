import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { Highlight, Stats } from "../types";
import AddPanel from "../components/AddPanel";
import HighlightCard from "../components/HighlightCard";

const PAGE = 30;

export default function Library() {
  const [items, setItems] = useState<Highlight[]>([]);
  const [total, setTotal] = useState(0);
  const [tags, setTags] = useState<{ name: string; count: number }[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [q, setQ] = useState("");
  const [query, setQuery] = useState("");
  const [tag, setTag] = useState<string | null>(null);
  const [onlyImportant, setOnlyImportant] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [loading, setLoading] = useState(true);

  // Debounce typing so every keystroke isn't a request
  useEffect(() => {
    const t = setTimeout(() => setQuery(q.trim()), 250);
    return () => clearTimeout(t);
  }, [q]);

  const params = useCallback(
    (offset: number) => {
      const p: Record<string, string> = { limit: String(PAGE), offset: String(offset) };
      if (query) p.q = query;
      if (tag) p.tag = tag;
      if (onlyImportant) p.important = "true";
      return p;
    },
    [query, tag, onlyImportant],
  );

  const load = useCallback(async () => {
    setLoading(true);
    const r = await api.highlights(params(0));
    setItems(r.items);
    setTotal(r.total);
    setLoading(false);
  }, [params]);

  const refreshMeta = () => {
    api.tags().then(setTags);
    api.stats().then(setStats);
  };

  useEffect(() => {
    load();
  }, [load]);

  useEffect(refreshMeta, []);

  const more = async () => {
    const r = await api.highlights(params(items.length));
    setItems((x) => [...x, ...r.items]);
  };

  const filtered = Boolean(query || tag || onlyImportant);

  return (
    <main className="page">
      <div className="page-head">
        <div>
          <h1>Library</h1>
          {stats && (
            <p className="muted small">
              {stats.highlights} highlights · {stats.due} due for review · {stats.important} important
            </p>
          )}
        </div>
        <button className="btn btn-primary" onClick={() => setShowAdd((s) => !s)} aria-expanded={showAdd}>
          {showAdd ? "Close" : "+ Add"}
        </button>
      </div>

      {showAdd && (
        <AddPanel
          onAdded={() => {
            load();
            refreshMeta();
          }}
        />
      )}

      <div className="filters">
        <input type="search" placeholder="Search text, notes, titles, authors" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search" />
        <button className={`chip ${onlyImportant ? "chip-on" : ""}`} onClick={() => setOnlyImportant((v) => !v)} aria-pressed={onlyImportant}>
          ★ Important
        </button>
        {tags.map((t) => (
          <button key={t.name} className={`chip ${tag === t.name ? "chip-on" : ""}`} onClick={() => setTag(tag === t.name ? null : t.name)} aria-pressed={tag === t.name}>
            #{t.name} <span className="muted">{t.count}</span>
          </button>
        ))}
      </div>

      {!loading && items.length === 0 && (
        <div className="empty">
          {filtered ? (
            <p>Nothing matches these filters.</p>
          ) : (
            <>
              <p>Your library is empty.</p>
              <p className="muted">Add a highlight from a book, save an article, or jot a note. It'll start coming back in your daily digest.</p>
            </>
          )}
        </div>
      )}

      <div className="list">
        {items.map((h) => (
          <HighlightCard
            key={h.id}
            h={h}
            onChange={(n) => {
              setItems((xs) => xs.map((x) => (x.id === n.id ? n : x)));
              refreshMeta();
            }}
            onDelete={(id) => {
              setItems((xs) => xs.filter((x) => x.id !== id));
              setTotal((t) => t - 1);
              refreshMeta();
            }}
            onTag={setTag}
          />
        ))}
      </div>
      {items.length < total && (
        <button className="btn more" onClick={more}>
          Load more ({total - items.length} left)
        </button>
      )}
    </main>
  );
}
