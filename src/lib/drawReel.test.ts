import { describe, expect, it } from "vitest";
import { canvasHeadlineText, canvasHeadlineTokens } from "./drawReel";
import { TEMPLATES } from "../templates";
import { CANVAS_H, CANVAS_W } from "../types";

describe("canvas layout rules", () => {
  it("exports 9:16 phone frames", () => {
    expect(CANVAS_W).toBe(1080);
    expect(CANVAS_H).toBe(1920);
    expect(CANVAS_H / CANVAS_W).toBeCloseTo(16 / 9);
  });

  it("does not put hashtags on the canvas title", () => {
    const reel = TEMPLATES[0];
    expect(reel.hashtags).toContain("#");
    expect(canvasHeadlineText(reel)).not.toContain("#");
  });

  it("omits the episode number from the on-canvas title", () => {
    const reel = TEMPLATES[0];
    expect(reel.episode).toBe("30");
    expect(canvasHeadlineText(reel)).toBe("The End of Apartheid");
    const joined = canvasHeadlineTokens(reel)
      .map((t) => t.text)
      .join("");
    expect(joined).not.toMatch(/^\s*30\./);
    expect(joined).not.toContain("30.");
  });
});
