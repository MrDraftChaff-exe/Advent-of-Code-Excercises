import { describe, expect, it } from "vitest";
import { blankReel, cloneTemplate, TEMPLATES, THEMES } from "./templates";
import { canvasHeadlineText } from "./lib/drawReel";
import { formatHeadline, formatYear } from "./lib/text";
import { TARGET_FACT_COUNT } from "./lib/catalog";

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
    expect(reel.bullets).toHaveLength(12);
    expect(reel.bullets[0]).toMatch(/Apartheid was South Africa/);
    expect(reel.bullets[4]).toMatch(/April 27, 1994/);
    expect(reel.bullets[11]).toMatch(/1994 elections/);
    expect(reel.hashtags).toBe(
      "#NelsonMandela #Apartheid #SouthAfrica #HistoryTok",
    );
  });

  it("ships a Dolly Parton post template without replacing apartheid", () => {
    expect(TEMPLATES[0].id).toBe("apartheid");
    const dolly = TEMPLATES.find((t) => t.id === "dolly");
    expect(dolly).toBeDefined();
    expect(dolly?.title).toBe("Dolly Parton");
    expect(dolly?.year).toBe("1973");
    expect(dolly?.imageUrl).toContain("dolly-parton-2010");
    expect(dolly?.imageCredit).toMatch(/Curtis Hilbun/);
    expect(dolly?.theme).toBe("ember");
    expect(dolly?.bullets).toHaveLength(TARGET_FACT_COUNT);
    expect(dolly?.bullets[3]).toMatch(/Jolene/);
    expect(dolly?.bullets[4]).toMatch(/Elvis/);
    expect(dolly?.postCaption).toMatch(/The blueprint/);
    expect(dolly?.postCaption).toContain("@FactsOrWhacks");
    expect(dolly?.hashtags).toContain("#DollyParton");
    expect(canvasHeadlineText(dolly!)).toBe("Dolly Parton");
    expect(canvasHeadlineText(dolly!)).not.toMatch(/\b396\b/);
  });

  it("ships a Tim Curry tribute template without replacing apartheid", () => {
    expect(TEMPLATES[0].id).toBe("apartheid");
    const curry = TEMPLATES.find((t) => t.id === "tim-curry");
    expect(curry).toBeDefined();
    expect(curry?.title).toBe("Tim Curry");
    expect(curry?.year).toBe("1946–2026");
    expect(curry?.imageUrl).toContain("tim-curry-2025");
    expect(curry?.imageCredit).toMatch(/Kevin Paul/);
    expect(curry?.theme).toBe("cosmic");
    expect(curry?.bullets).toHaveLength(TARGET_FACT_COUNT);
    expect(curry?.bullets[3]).toMatch(/Rocky Horror/);
    expect(curry?.bullets[11]).toMatch(/August 25, 2026/);
    expect(curry?.postCaption).toMatch(/villain era/);
    expect(curry?.postCaption).toContain("@FactsOrWhacks");
    expect(curry?.hashtags).toContain("#TimCurry");
    expect(canvasHeadlineText(curry!)).toBe("Tim Curry");
    expect(canvasHeadlineText(curry!)).not.toMatch(/\b397\b/);
  });

  it("uses twelve full-sentence facts on every template", () => {
    for (const template of TEMPLATES) {
      expect(template.bullets).toHaveLength(TARGET_FACT_COUNT);
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
