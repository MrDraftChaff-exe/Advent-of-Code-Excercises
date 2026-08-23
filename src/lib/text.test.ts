import { describe, expect, it } from "vitest";
import { clampDuration, parseHighlighted, wrapPlain, wrapTokens } from "./text";

describe("parseHighlighted", () => {
  it("splits accent markers into highlight tokens", () => {
    const tokens = parseHighlighted("THE SIZE **OF** THE **MOON**");
    const joined = tokens
      .map((t) => `${t.highlight ? "#" : ""}${t.text}`)
      .join("");
    expect(joined.replace(/\s/g, "")).toBe("THESIZE#OFTHE#MOON");
    expect(tokens.filter((t) => t.highlight).map((t) => t.text)).toEqual([
      "OF",
      "MOON",
    ]);
  });

  it("keeps spaces around highlighted words", () => {
    const tokens = parseHighlighted("HOW **DEEP** EARTH'S **OCEANS**");
    expect(tokens.map((t) => t.text).join("")).toBe("HOW DEEP EARTH'S OCEANS");
  });

  it("keeps newlines as tokens", () => {
    const tokens = parseHighlighted("ONE\n**TWO**");
    expect(tokens.some((t) => t.text === "\n")).toBe(true);
  });
});

describe("wrapTokens", () => {
  const measure = (s: string) => s.length * 10;

  it("wraps when a line exceeds max width", () => {
    const tokens = parseHighlighted("AAAA BBBB CCCC");
    const lines = wrapTokens(tokens, 50, measure);
    expect(lines).toHaveLength(3);
    expect(lines.map((l) => l.map((t) => t.text).join(""))).toEqual([
      "AAAA",
      "BBBB",
      "CCCC",
    ]);
  });

  it("honors explicit newlines", () => {
    const tokens = parseHighlighted("HELLO\nWORLD");
    const lines = wrapTokens(tokens, 1000, measure);
    expect(lines).toHaveLength(2);
  });
});

describe("wrapPlain", () => {
  it("wraps long fact copy", () => {
    const lines = wrapPlain("alpha beta gamma delta", 20, (s) => s.length);
    expect(lines.length).toBeGreaterThan(1);
    expect(lines.join(" ")).toBe("alpha beta gamma delta");
  });
});

describe("clampDuration", () => {
  it("clamps and rounds duration", () => {
    expect(clampDuration(Number.NaN)).toBe(15);
    expect(clampDuration(3)).toBe(8);
    expect(clampDuration(90)).toBe(60);
    expect(clampDuration(15.4)).toBe(15);
  });
});
