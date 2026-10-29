import { useEffect, useState, type FormEvent } from "react";
import { api, parseTags } from "../api";
import type { Source } from "../types";

type Tab = "highlight" | "article" | "note";

export default function AddPanel({ onAdded }: { onAdded: () => void }) {
  const [tab, setTab] = useState<Tab>("highlight");
  const [sources, setSources] = useState<(Source & { highlights: number })[]>([]);
  const [text, setText] = useState("");
  const [sourceId, setSourceId] = useState<string>("new");
  const [kind, setKind] = useState<Source["kind"]>("book");
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [url, setUrl] = useState("");
  const [tags, setTags] = useState("");
  const [important, setImportant] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    api.sources().then((s) => setSources(s.filter((x) => x.kind !== "note")));
  }, []);

  const reset = () => {
    setText("");
    setUrl("");
    setTitle("");
    setAuthor("");
    setImportant(false);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      if (tab === "article") {
        const highlights = text.split(/\n\s*\n/).map((s) => s.trim()).filter(Boolean);
        const r = await api.saveArticle({ url, title: title || undefined, highlights, tags: parseTags(tags) });
        setMessage({
          ok: !r.fetch_error,
          text: r.fetch_error
            ? `Saved, but couldn't read the title: ${r.fetch_error}`
            : `Saved "${r.title}" with ${r.highlights} highlight${r.highlights === 1 ? "" : "s"}`,
        });
      } else {
        const base = { text, tags: parseTags(tags), important };
        if (tab === "note") await api.addHighlight(base);
        else if (sourceId !== "new") await api.addHighlight({ ...base, source_id: Number(sourceId) });
        else await api.addHighlight({ ...base, source: { kind, title, author: author || undefined } });
        setMessage({ ok: true, text: "Saved" });
      }
      reset();
      api.sources().then((s) => setSources(s.filter((x) => x.kind !== "note")));
      onAdded();
    } catch (err) {
      setMessage({ ok: false, text: err instanceof Error ? err.message : "Couldn't save" });
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="card add" onSubmit={submit}>
      <div className="tabs" role="tablist">
        {(["highlight", "article", "note"] as Tab[]).map((t) => (
          <button key={t} type="button" role="tab" aria-selected={tab === t} className={tab === t ? "tab active" : "tab"} onClick={() => setTab(t)}>
            {t === "highlight" ? "Highlight" : t === "article" ? "Article URL" : "Note"}
          </button>
        ))}
      </div>

      {tab === "article" && (
        <>
          <input type="url" placeholder="https://…" value={url} onChange={(e) => setUrl(e.target.value)} required aria-label="Article URL" />
          <input placeholder="Title (optional, fetched from the page)" value={title} onChange={(e) => setTitle(e.target.value)} aria-label="Title" />
        </>
      )}

      <textarea
        className="quote-input"
        rows={tab === "article" ? 4 : 3}
        placeholder={
          tab === "article" ? "Highlights from it (optional). Separate them with a blank line." : tab === "note" ? "Write a note to your future self…" : "Paste the passage…"
        }
        value={text}
        onChange={(e) => setText(e.target.value)}
        required={tab !== "article"}
        aria-label="Text"
      />

      {tab === "highlight" && (
        <div className="row wrap">
          <select value={sourceId} onChange={(e) => setSourceId(e.target.value)} aria-label="Source">
            <option value="new">New source…</option>
            {sources.map((s) => (
              <option key={s.id} value={s.id}>
                {s.title}
                {s.author ? ` — ${s.author}` : ""}
              </option>
            ))}
          </select>
          {sourceId === "new" && (
            <>
              <select value={kind} onChange={(e) => setKind(e.target.value as Source["kind"])} aria-label="Source type" className="narrow">
                <option value="book">Book</option>
                <option value="article">Article</option>
              </select>
              <input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} required aria-label="Source title" />
              <input placeholder="Author" value={author} onChange={(e) => setAuthor(e.target.value)} aria-label="Author" />
            </>
          )}
        </div>
      )}

      <div className="row wrap">
        <input placeholder="Tags, comma separated" value={tags} onChange={(e) => setTags(e.target.value)} aria-label="Tags" />
        {tab !== "article" && (
          <label className="check">
            <input type="checkbox" checked={important} onChange={(e) => setImportant(e.target.checked)} /> Important
          </label>
        )}
        <button className="btn btn-primary" disabled={busy}>
          {busy ? "Saving…" : "Save"}
        </button>
      </div>
      {message && <p className={message.ok ? "ok small" : "error small"} role="status">{message.text}</p>}
    </form>
  );
}
