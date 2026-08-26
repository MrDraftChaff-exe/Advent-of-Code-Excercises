import { describe, expect, it } from "vitest";
import { TEMPLATES } from "../templates";
import { buildPasteCaption } from "./postCaption";

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

  it("falls back to title, two facts, handle, and hashtags", () => {
    const caption = buildPasteCaption({
      ...TEMPLATES[0],
      postCaption: undefined,
    });
    expect(caption).toContain("The End of Apartheid (1994)");
    expect(caption).toContain(TEMPLATES[0].bullets[0]);
    expect(caption).toContain("@FactsOrWhacks");
    expect(caption).toContain("#NelsonMandela");
  });
});
