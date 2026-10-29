import { useState } from "react";
import { api, parseTags } from "../api";
import type { Highlight } from "../types";

export function ago(iso: string | null): string {
  if (!iso) return "never";
  const days = Math.floor((Date.now() - new Date(iso + "Z").getTime()) / 86_400_000);
  return days <= 0 ? "today" : days === 1 ? "yesterday" : `${days} days ago`;
}

type Props = {
  h: Highlight;
  onChange?: (h: Highlight) => void;
  onDelete?: (id: number) => void;
  onTag?: (tag: string) => void;
  footer?: React.ReactNode;
};

export default function HighlightCard({ h, onChange, onDelete, onTag, footer }: Props) {
  const [editing, setEditing] = useState(false);
  const [note, setNote] = useState(h.note ?? "");
  const [tags, setTags] = useState(h.tags.join(", "));
  const [error, setError] = useState<string | null>(null);

  const patch = async (p: Parameters<typeof api.updateHighlight>[1]) => {
    try {
      onChange?.(await api.updateHighlight(h.id, p));
      setError(null);
      return true;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't update");
      return false;
    }
  };

  const src = h.source;
  return (
    <article className={`card hl ${h.important ? "hl-important" : ""}`}>
      <blockquote>{h.text}</blockquote>
      <div className="hl-source">
        {src.url ? (
          <a href={src.url} target="_blank" rel="noreferrer">
            {src.title}
          </a>
        ) : (
          src.title
        )}
        {src.author && <span className="muted"> — {src.author}</span>}
      </div>

      {editing ? (
        <div className="hl-edit">
          <textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Your note" aria-label="Note" />
          <input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="Tags, comma separated" aria-label="Tags" />
          <div className="row">
            <button className="btn btn-sm btn-primary" onClick={async () => (await patch({ note, tags: parseTags(tags) })) && setEditing(false)}>
              Save
            </button>
            <button className="btn btn-sm" onClick={() => setEditing(false)}>
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <>
          {h.note && <p className="hl-note">{h.note}</p>}
          {h.tags.length > 0 && (
            <div className="chips">
              {h.tags.map((t) => (
                <button key={t} className="chip" onClick={() => onTag?.(t)}>
                  #{t}
                </button>
              ))}
            </div>
          )}
        </>
      )}
      {error && <p className="error small">{error}</p>}

      <div className="hl-foot">
        {footer ?? (
          <span className="muted small">
            {h.surfaced_count ? `Seen ${h.surfaced_count}× · last ${ago(h.last_surfaced_at)}` : `Saved ${ago(h.created_at)} · not resurfaced yet`}
          </span>
        )}
        {onChange && (
          <div className="hl-actions">
            <button
              className={`icon-btn ${h.important ? "star-on" : ""}`}
              onClick={() => patch({ important: !h.important })}
              aria-label={h.important ? "Unmark important" : "Mark important"}
              aria-pressed={h.important}
              title="Important highlights come back about twice as often"
            >
              ★
            </button>
            <button className="icon-btn" onClick={() => setEditing(true)} aria-label="Edit note and tags">
              ✎
            </button>
            {onDelete && (
              <button
                className="icon-btn"
                onClick={async () => {
                  if (confirm("Delete this highlight?")) {
                    await api.deleteHighlight(h.id);
                    onDelete(h.id);
                  }
                }}
                aria-label="Delete"
              >
                ✕
              </button>
            )}
          </div>
        )}
      </div>
    </article>
  );
}
