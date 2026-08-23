import { describe, expect, it } from "vitest";
import { blankReel, cloneTemplate, TEMPLATES, THEMES } from "./templates";
import { canvasHeadlineText } from "./lib/drawReel";
import { formatHeadline, formatYear } from "./lib/text";

describe("templates", () => {
  it("ships original fact copy, not a transcript of the source reel", () => {
    const blob = JSON.stringify(TEMPLATES).toLowerCase();
    expect(blob).not.toContain("308 million");
    expect(blob).not.toContain("animals killed");
    expect(TEMPLATES.length).toBeGreaterThanOrEqual(4);
  });

  it("clones without sharing bullet array identity", () => {
    const a = cloneTemplate(TEMPLATES[0]);
    const b = cloneTemplate(TEMPLATES[0]);
    a.bullets[0] = "changed";
    expect(b.bullets[0]).not.toBe("changed");
    expect(THEMES[a.theme]).toBeDefined();
  });

  it("defaults to the HistoryTok apartheid episode", () => {
    const reel = TEMPLATES[0];
    expect(formatHeadline(reel.episode, reel.title)).toBe(
      "30. The End of Apartheid",
    );
    expect(canvasHeadlineText(reel)).toBe("The End of Apartheid");
    expect(canvasHeadlineText(reel)).not.toMatch(/\b30\b/);
    expect(formatYear(reel.year)).toBe("(1994)");
    expect(reel.imageCaption).toBe("Nelson Mandela voting, 1994");
    expect(reel.imageUrl).toContain("mandela-voting-1994");
    expect(reel.imageCredit).toMatch(/Paul Weinberg/);
    expect(reel.bullets).toHaveLength(8);
    expect(reel.bullets[0]).toMatch(/Apartheid was South Africa/);
    expect(reel.bullets[4]).toMatch(/April 27, 1994/);
    expect(reel.hashtags).toBe(
      "#NelsonMandela #Apartheid #SouthAfrica #HistoryTok",
    );
  });

  it("uses full-sentence bullets instead of labeled stats", () => {
    for (const template of TEMPLATES) {
      expect(template.bullets.length).toBeGreaterThan(0);
      for (const bullet of template.bullets) {
        expect(bullet).not.toMatch(/^\d+\)\s+\S+\s+—\s/);
      }
    }
  });

  it("brands templates with the Facts or Whacks handle", () => {
    for (const template of TEMPLATES) {
      expect(template.handle).toBe("@FactsOrWhacks");
    }
  });

  it("creates a custom blank reel", () => {
    const reel = blankReel();
    expect(reel.id).toBe("custom");
    expect(reel.bullets.length).toBeGreaterThan(0);
    expect(reel.hashtags).toContain("#");
  });
});
