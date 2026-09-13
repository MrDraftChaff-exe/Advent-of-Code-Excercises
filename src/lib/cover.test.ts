import { describe, expect, it } from "vitest";
import { coverSourceRect, kenBurnsRect } from "./cover";

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

describe("kenBurnsRect", () => {
  it("zooms into a cover crop without leaving the source", () => {
    const src = { sx: 10, sy: 20, sw: 400, sh: 800 };
    const zoomed = kenBurnsRect(src, 2, 0.5, 0.5);
    expect(zoomed.sw).toBe(200);
    expect(zoomed.sh).toBe(400);
    expect(zoomed.sx).toBe(110);
    expect(zoomed.sy).toBe(220);
    expect(zoomed.sx + zoomed.sw).toBeLessThanOrEqual(src.sx + src.sw + 1e-6);
    expect(zoomed.sy + zoomed.sh).toBeLessThanOrEqual(src.sy + src.sh + 1e-6);
  });
});
