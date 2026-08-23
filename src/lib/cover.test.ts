import { describe, expect, it } from "vitest";
import { coverSourceRect } from "./cover";

describe("coverSourceRect", () => {
  it("crops the top of a portrait photo into a landscape frame", () => {
    const src = coverSourceRect(538, 800, 896, 400, 0.28);
    expect(src.sx).toBe(0);
    expect(src.sw).toBe(538);
    expect(src.sh).toBeCloseTo(538 / (896 / 400));
    expect(src.sy).toBeGreaterThanOrEqual(0);
    expect(src.sy + src.sh).toBeLessThanOrEqual(800 + 1e-6);
  });

  it("crops the sides of a wide photo into a tall frame", () => {
    const src = coverSourceRect(1600, 900, 400, 600, 0.5);
    expect(src.sy).toBe(0);
    expect(src.sh).toBe(900);
    expect(src.sw).toBeCloseTo(900 * (400 / 600));
  });
});
