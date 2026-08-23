import { describe, expect, it } from "vitest";
import { blankReel, cloneTemplate, TEMPLATES, THEMES } from "./templates";

describe("templates", () => {
  it("ships original fact copy, not a transcript of the source reel", () => {
    const blob = JSON.stringify(TEMPLATES).toLowerCase();
    expect(blob).not.toContain("308 million");
    expect(blob).not.toContain("animals killed");
    expect(TEMPLATES.length).toBeGreaterThanOrEqual(4);
  });

  it("clones without sharing fact array identity", () => {
    const a = cloneTemplate(TEMPLATES[0]);
    const b = cloneTemplate(TEMPLATES[0]);
    a.facts[0].text = "changed";
    expect(b.facts[0].text).not.toBe("changed");
    expect(THEMES[a.theme]).toBeDefined();
  });

  it("creates a custom blank reel", () => {
    const reel = blankReel();
    expect(reel.id).toBe("custom");
    expect(reel.facts.length).toBeGreaterThan(0);
  });
});
