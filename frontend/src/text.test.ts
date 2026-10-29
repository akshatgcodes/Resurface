import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { parseTags, splitHighlights } from "./api";
import { ago } from "./components/HighlightCard";

describe("parseTags", () => {
  it("splits on commas and newlines and drops blanks", () => {
    expect(parseTags(" design, ux ,\nwriting,, ")).toEqual(["design", "ux", "writing"]);
    expect(parseTags("")).toEqual([]);
  });
});

describe("splitHighlights", () => {
  it("makes one highlight per paragraph", () => {
    expect(splitHighlights("First idea.\nstill first.\n\n  \n\nSecond idea.\n")).toEqual(["First idea.\nstill first.", "Second idea."]);
  });
});

describe("ago", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-30T12:00:00Z"));
  });
  afterEach(() => vi.useRealTimers());

  it("reads server UTC timestamps as days ago", () => {
    expect(ago(null)).toBe("never");
    expect(ago("2026-10-30T01:00:00")).toBe("today");
    expect(ago("2026-10-29T11:00:00")).toBe("yesterday");
    expect(ago("2026-10-20T12:00:00")).toBe("10 days ago");
  });
});
