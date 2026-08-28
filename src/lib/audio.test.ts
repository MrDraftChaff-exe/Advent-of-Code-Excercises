import { describe, expect, it } from "vitest";
import { ambientSeed, hashSeed, padParams } from "./audio";

describe("unique ambient pads", () => {
  it("hashes the same seed the same way", () => {
    expect(hashSeed("400-btk")).toBe(hashSeed("400-btk"));
  });

  it("gives different chords or roots to different episodes", () => {
    const a = padParams("396-dolly-parton");
    const b = padParams("400-btk");
    expect(a).not.toEqual(b);
    expect(a.root).toBeGreaterThan(50);
    expect(b.cutoff).toBeLessThan(600);
  });

  it("seeds studio preview from episode identity", () => {
    expect(
      ambientSeed({ episode: "400", id: "btk", title: "BTK" }),
    ).toBe("400-btk-BTK");
  });
});
