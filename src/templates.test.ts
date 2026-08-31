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

  it("ships a Peter Cullen tribute template without replacing apartheid", () => {
    expect(TEMPLATES[0].id).toBe("apartheid");
    const cullen = TEMPLATES.find((t) => t.id === "peter-cullen");
    expect(cullen).toBeDefined();
    expect(cullen?.title).toBe("Peter Cullen");
    expect(cullen?.year).toBe("1941–2026");
    expect(cullen?.imageUrl).toContain("peter-cullen-2023");
    expect(cullen?.imageCredit).toMatch(/Pedro Heshike/);
    expect(cullen?.theme).toBe("ocean");
    expect(cullen?.bullets).toHaveLength(TARGET_FACT_COUNT);
    expect(cullen?.bullets[5]).toMatch(/Optimus Prime/);
    expect(cullen?.bullets[11]).toMatch(/August 26, 2026/);
    expect(cullen?.postCaption).toMatch(/quiet hero/);
    expect(cullen?.postCaption).toContain("@FactsOrWhacks");
    expect(cullen?.hashtags).toContain("#PeterCullen");
    expect(canvasHeadlineText(cullen!)).toBe("Peter Cullen");
    expect(canvasHeadlineText(cullen!)).not.toMatch(/\b398\b/);
  });

  it("ships a Hayden Panettiere tribute template without replacing apartheid", () => {
    expect(TEMPLATES[0].id).toBe("apartheid");
    const hayden = TEMPLATES.find((t) => t.id === "hayden-panettiere");
    expect(hayden).toBeDefined();
    expect(hayden?.title).toBe("Hayden Panettiere");
    expect(hayden?.year).toBe("1989–2026");
    expect(hayden?.imageUrl).toContain("hayden-panettiere-2011");
    expect(hayden?.imageCredit).toMatch(/Tabercil/);
    expect(hayden?.theme).toBe("cosmic");
    expect(hayden?.bullets).toHaveLength(TARGET_FACT_COUNT);
    expect(hayden?.bullets[2]).toMatch(/Claire Bennet/);
    expect(hayden?.bullets[11]).toMatch(/August 16, 2026/);
    expect(hayden?.postCaption).toMatch(/Same fire/);
    expect(hayden?.postCaption).toContain("@FactsOrWhacks");
    expect(hayden?.hashtags).toContain("#HaydenPanettiere");
    expect(canvasHeadlineText(hayden!)).toBe("Hayden Panettiere");
    expect(canvasHeadlineText(hayden!)).not.toMatch(/\b399\b/);
  });

  it("ships a BTK template without replacing apartheid", () => {
    expect(TEMPLATES[0].id).toBe("apartheid");
    const btk = TEMPLATES.find((t) => t.id === "btk");
    expect(btk).toBeDefined();
    expect(btk?.title).toBe("BTK");
    expect(btk?.year).toBe("1974–2005");
    expect(btk?.imageUrl).toContain("dennis-rader-airman");
    expect(btk?.imageCredit).toMatch(/Air Force/);
    expect(btk?.theme).toBe("ember");
    expect(btk?.bullets).toHaveLength(TARGET_FACT_COUNT);
    expect(btk?.bullets[9]).toMatch(/floppy|metadata/i);
    expect(btk?.bullets[10]).toMatch(/February 25, 2005/);
    expect(btk?.postCaption).toMatch(/skip in class/);
    expect(btk?.postCaption).toContain("@FactsOrWhacks");
    expect(btk?.hashtags).toContain("#BTK");
    expect(canvasHeadlineText(btk!)).toBe("BTK");
    expect(canvasHeadlineText(btk!)).not.toMatch(/\b400\b/);
  });

  it("ships a Hurricane Katrina anniversary template without replacing apartheid", () => {
    expect(TEMPLATES[0].id).toBe("apartheid");
    const katrina = TEMPLATES.find((t) => t.id === "katrina");
    expect(katrina).toBeDefined();
    expect(katrina?.title).toBe("Hurricane Katrina");
    expect(katrina?.year).toBe("2005");
    expect(katrina?.imageUrl).toContain("katrina-new-orleans-2005");
    expect(katrina?.imageCredit).toMatch(/Coast Guard/);
    expect(katrina?.theme).toBe("ocean");
    expect(katrina?.bullets).toHaveLength(TARGET_FACT_COUNT);
    expect(katrina?.bullets[0]).toMatch(/August 29, 2005/);
    expect(katrina?.bullets[4]).toMatch(/80 percent/);
    expect(katrina?.postCaption).toMatch(/21 years ago today/);
    expect(katrina?.postCaption).toContain("@FactsOrWhacks");
    expect(katrina?.hashtags).toContain("#HurricaneKatrina");
    expect(canvasHeadlineText(katrina!)).toBe("Hurricane Katrina");
    expect(canvasHeadlineText(katrina!)).not.toMatch(/\b401\b/);
  });

  it("ships a Thurgood Marshall confirmation template without replacing apartheid", () => {
    expect(TEMPLATES[0].id).toBe("apartheid");
    const marshall = TEMPLATES.find((t) => t.id === "thurgood-marshall");
    expect(marshall).toBeDefined();
    expect(marshall?.title).toBe("Thurgood Marshall");
    expect(marshall?.year).toBe("1967");
    expect(marshall?.imageUrl).toContain("thurgood-marshall-1967");
    expect(marshall?.imageCredit).toMatch(/Okamoto/);
    expect(marshall?.theme).toBe("ember");
    expect(marshall?.bullets).toHaveLength(TARGET_FACT_COUNT);
    expect(marshall?.bullets[1]).toMatch(/Maryland Law School/);
    expect(marshall?.bullets[11]).toMatch(/August 30, 1967/);
    expect(marshall?.postCaption).toMatch(/59 years ago today/);
    expect(marshall?.postCaption).toContain("@FactsOrWhacks");
    expect(marshall?.hashtags).toContain("#ThurgoodMarshall");
    expect(canvasHeadlineText(marshall!)).toBe("Thurgood Marshall");
    expect(canvasHeadlineText(marshall!)).not.toMatch(/\b402\b/);
  });

  it("ships a Princess Diana anniversary template without replacing apartheid", () => {
    expect(TEMPLATES[0].id).toBe("apartheid");
    const diana = TEMPLATES.find((t) => t.id === "princess-diana");
    expect(diana).toBeDefined();
    expect(diana?.title).toBe("Princess Diana");
    expect(diana?.year).toBe("1961–1997");
    expect(diana?.imageUrl).toContain("princess-diana-1985");
    expect(diana?.imageCredit).toMatch(/White House/);
    expect(diana?.theme).toBe("cosmic");
    expect(diana?.bullets).toHaveLength(TARGET_FACT_COUNT);
    expect(diana?.bullets[3]).toMatch(/AIDS/);
    expect(diana?.bullets[11]).toMatch(/August 31, 1997/);
    expect(diana?.postCaption).toMatch(/29 years ago tonight/);
    expect(diana?.postCaption).toContain("@FactsOrWhacks");
    expect(diana?.hashtags).toContain("#PrincessDiana");
    expect(canvasHeadlineText(diana!)).toBe("Princess Diana");
    expect(canvasHeadlineText(diana!)).not.toMatch(/\b403\b/);
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
