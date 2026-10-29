export type Source = { id: number; kind: "article" | "book" | "note"; title: string; author: string | null; url: string | null };

export type Highlight = {
  id: number;
  text: string;
  note: string | null;
  important: boolean;
  tags: string[];
  source: Source;
  created_at: string;
  last_surfaced_at: string | null;
  surfaced_count: number;
  interval_days: number;
};

export type DigestPick = Highlight & { score: number; due: boolean; reason: string };

export type Digest = {
  id: number;
  created_at: string;
  trigger: "schedule" | "manual";
  emailed_to: string | null;
  picks: DigestPick[];
};

export type Stats = {
  highlights: number;
  important: number;
  due: number;
  never_surfaced: number;
  digest: { size: number; hour: number; timezone: string; email: boolean; scheduled: boolean };
};
