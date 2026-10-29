import type { Digest, DigestPick, Highlight, Source, Stats } from "./types";

const BASE = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const d = body.detail;
    const msg = typeof d === "string" ? d : Array.isArray(d) ? d.map((x) => x.msg).join("; ") : res.statusText;
    throw new ApiError(res.status, msg);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

const send = (method: string, body?: unknown): RequestInit => ({
  method,
  body: body === undefined ? undefined : JSON.stringify(body),
});

export type HighlightInput = {
  text: string;
  note?: string;
  tags?: string[];
  important?: boolean;
  source_id?: number;
  source?: { kind: Source["kind"]; title: string; author?: string; url?: string };
};

export const api = {
  me: () => request<{ user: boolean }>("/api/auth/me"),
  login: (password: string) => request("/api/auth/login", send("POST", { password })),
  logout: () => request("/api/auth/logout", send("POST")),

  highlights: (params: Record<string, string>) =>
    request<{ total: number; items: Highlight[] }>(`/api/highlights?${new URLSearchParams(params)}`),
  addHighlight: (input: HighlightInput) => request<Highlight>("/api/highlights", send("POST", input)),
  updateHighlight: (id: number, patch: Partial<Pick<Highlight, "text" | "note" | "tags" | "important">>) =>
    request<Highlight>(`/api/highlights/${id}`, send("PATCH", patch)),
  deleteHighlight: (id: number) => request<void>(`/api/highlights/${id}`, send("DELETE")),
  saveArticle: (input: { url: string; title?: string; highlights: string[]; tags: string[] }) =>
    request<Source & { highlights: number; fetch_error: string | null }>("/api/articles", send("POST", input)),
  sources: () => request<(Source & { highlights: number })[]>("/api/sources"),
  tags: () => request<{ name: string; count: number }[]>("/api/tags"),

  preview: () => request<{ computed_at: string; picks: DigestPick[] }>("/api/digest/preview"),
  sendDigest: () => request<Digest>("/api/digest/send", send("POST")),
  digests: () => request<Digest[]>("/api/digests"),
  stats: () => request<Stats>("/api/stats"),
};

export const parseTags = (s: string) =>
  s.split(/[,\n]/).map((t) => t.trim()).filter(Boolean);
