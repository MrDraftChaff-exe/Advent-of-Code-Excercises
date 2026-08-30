import { describe, expect, it } from "vitest";
import { TEMPLATES } from "../templates";
import {
  brandHashtags,
  buildPasteCaption,
  catalogCopyCaption,
  oneLine,
} from "./postCaption";
import type { CatalogEpisode } from "./catalog";

describe("paste captions", () => {
  it("uses the Dolly trendy caption as the paste block", () => {
    const dolly = TEMPLATES.find((t) => t.id === "dolly");
    expect(dolly).toBeDefined();
    const caption = buildPasteCaption(dolly!);
    expect(caption).toContain("same writing streak");
    expect(caption).toContain("The blueprint. Since 1946.");
    expect(caption).toContain("@FactsOrWhacks");
    expect(caption).toContain("#DollyParton");
    expect(caption.startsWith("She wrote")).toBe(true);
  });

  it("uses the Tim Curry tribute caption as the paste block", () => {
    const curry = TEMPLATES.find((t) => t.id === "tim-curry");
    expect(curry).toBeDefined();
    const caption = buildPasteCaption(curry!);
    expect(caption).toContain("50-year party");
    expect(caption).toContain("The villain era lasted five decades.");
    expect(caption).toContain("1946–2026");
    expect(caption).toContain("@FactsOrWhacks");
    expect(caption).toContain("#TimCurry");
    expect(caption.startsWith("He turned")).toBe(true);
  });

  it("uses the Peter Cullen tribute caption as the paste block", () => {
    const cullen = TEMPLATES.find((t) => t.id === "peter-cullen");
    expect(cullen).toBeDefined();
    const caption = buildPasteCaption(cullen!);
    expect(caption).toContain("tough enough to be gentle");
    expect(caption).toContain("The quiet hero in a thousand living rooms.");
    expect(caption).toContain("1941–2026");
    expect(caption).toContain("@FactsOrWhacks");
    expect(caption).toContain("#PeterCullen");
    expect(caption.startsWith("He based")).toBe(true);
  });

  it("uses the Hayden Panettiere tribute caption as the paste block", () => {
    const hayden = TEMPLATES.find((t) => t.id === "hayden-panettiere");
    expect(hayden).toBeDefined();
    const caption = buildPasteCaption(hayden!);
    expect(caption).toContain("cheerleaders superheroes");
    expect(caption).toContain("Thirty-six years was not enough.");
    expect(caption).toContain("1989–2026");
    expect(caption).toContain("@FactsOrWhacks");
    expect(caption).toContain("#HaydenPanettiere");
    expect(caption.startsWith("She made")).toBe(true);
  });

  it("uses the BTK follow-hook caption as the paste block", () => {
    const btk = TEMPLATES.find((t) => t.id === "btk");
    expect(btk).toBeDefined();
    const caption = buildPasteCaption(btk!);
    expect(caption).toContain("Church president");
    expect(caption).toContain("The cases they skip in class");
    expect(caption).toContain("Follow @FactsOrWhacks");
    expect(caption).toContain("#BTK");
    expect(caption.startsWith("Church president")).toBe(true);
  });

  it("uses the Katrina anniversary caption as the paste block", () => {
    const katrina = TEMPLATES.find((t) => t.id === "katrina");
    expect(katrina).toBeDefined();
    const caption = buildPasteCaption(katrina!);
    expect(caption).toContain("didn’t drown New Orleans");
    expect(caption).toContain("The levees did.");
    expect(caption).toContain("21 years ago today");
    expect(caption).toContain("Follow @FactsOrWhacks");
    expect(caption).toContain("#HurricaneKatrina");
    expect(caption.startsWith("The hurricane")).toBe(true);
  });

  it("uses the Thurgood Marshall confirmation caption as the paste block", () => {
    const marshall = TEMPLATES.find((t) => t.id === "thurgood-marshall");
    expect(marshall).toBeDefined();
    const caption = buildPasteCaption(marshall!);
    expect(caption).toContain("wasn’t allowed");
    expect(caption).toContain("59 years ago today");
    expect(caption).toContain("Follow @FactsOrWhacks");
    expect(caption).toContain("#ThurgoodMarshall");
    expect(caption.startsWith("He wasn’t allowed")).toBe(true);
  });

  it("falls back to a one-line title, facts, handle, and hashtags", () => {
    const caption = buildPasteCaption({
      ...TEMPLATES[0],
      postCaption: undefined,
    });
    expect(caption).toContain("The End of Apartheid (1994)");
    expect(caption).toContain(TEMPLATES[0].bullets[0]);
    expect(caption).toContain("@FactsOrWhacks");
    expect(caption).toContain("#NelsonMandela");
    expect(caption).not.toMatch(/\r|\n/);
  });

  it("builds a one-click catalog copy caption", () => {
    const ep: CatalogEpisode = {
      n: 2,
      title: "American Revolution",
      hook: "1776: 13 colonies said NO to a king.",
      bullets: [
        "Boston Tea Party — 342 chests dumped.",
        "Declaration signed July 4, 1776.",
      ],
      image: "/images/x.jpg",
      tags: "#AmericanRevolution #USHistory",
      credit: "Public domain",
      source: "https://example.com",
    };
    const caption = catalogCopyCaption(ep);
    expect(caption).toBe(
      oneLine(
        "American Revolution (1776). 1776: 13 colonies said NO to a king. Boston Tea Party — 342 chests dumped. Declaration signed July 4, 1776.",
        "@FactsOrWhacks",
        brandHashtags(ep.tags),
      ),
    );
    expect(caption).toContain("#FactsOrWhacks");
    expect(caption).not.toMatch(/\r|\n/);
  });
});
