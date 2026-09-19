import { describe, expect, it } from "vitest";
import { TEMPLATES } from "../templates";
import {
  BEAT_COUNT,
  FACTS_PER_BEAT,
  VIDEO_DURATION_SEC,
  beatAtTime,
  collageBeats,
  kenBurnsAt,
  reelSlides,
  usesCollage,
} from "./collage";

describe("collage beats", () => {
  it("splits twelve facts across six minute-long photo beats", () => {
    const elvis = TEMPLATES.find((t) => t.id === "elvis");
    expect(elvis).toBeDefined();
    expect(usesCollage(elvis!)).toBe(true);
    expect(reelSlides(elvis!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(elvis!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats.every((b) => b.facts.length === FACTS_PER_BEAT)).toBe(true);
    expect(beats[0].facts[0]).toMatch(/Ed Sullivan/);
    expect(beats[5].facts[1]).toMatch(/70 years ago tonight/);
    expect(beats[0].end - beats[0].start).toBeCloseTo(10);
    expect(beats.at(-1)?.end).toBe(VIDEO_DURATION_SEC);
  });

  it("collages the LHC extra across six detector stills", () => {
    const lhc = TEMPLATES.find((t) => t.id === "lhc");
    expect(lhc).toBeDefined();
    expect(usesCollage(lhc!)).toBe(true);
    expect(reelSlides(lhc!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(lhc!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/17-mile/);
    expect(beats[5].facts[1]).toMatch(/18 years ago today/);
  });

  it("collages the 9/11 extra across six public-domain stills", () => {
    const nineEleven = TEMPLATES.find((t) => t.id === "september-11");
    expect(nineEleven).toBeDefined();
    expect(usesCollage(nineEleven!)).toBe(true);
    expect(reelSlides(nineEleven!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(nineEleven!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/Four planes/);
    expect(beats[5].facts[1]).toMatch(/25 years later/);
  });

  it("collages the Star-Spangled Banner extra across six public-domain stills", () => {
    const banner = TEMPLATES.find((t) => t.id === "star-spangled-banner");
    expect(banner).toBeDefined();
    expect(usesCollage(banner!)).toBe(true);
    expect(reelSlides(banner!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(banner!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/sunrise/);
    expect(beats[5].facts[1]).toMatch(/212 years ago tonight/);
  });

  it("collages the Teddy Roosevelt extra across six public-domain stills", () => {
    const teddy = TEMPLATES.find((t) => t.id === "teddy-roosevelt");
    expect(teddy).toBeDefined();
    expect(usesCollage(teddy!)).toBe(true);
    expect(reelSlides(teddy!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(teddy!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/Buffalo/);
    expect(beats[5].facts[1]).toMatch(/125 years ago today/);
  });

  it("collages the El Grito extra across six public-domain stills", () => {
    const grito = TEMPLATES.find((t) => t.id === "el-grito");
    expect(grito).toBeDefined();
    expect(usesCollage(grito!)).toBe(true);
    expect(reelSlides(grito!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(grito!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/Dolores/);
    expect(beats[5].facts[1]).toMatch(/216 years ago tonight/);
  });

  it("collages the Pirates extra across six public-domain stills", () => {
    const pirates = TEMPLATES.find((t) => t.id === "pirate-day");
    expect(pirates).toBeDefined();
    expect(usesCollage(pirates!)).toBe(true);
    expect(reelSlides(pirates!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(pirates!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/golden age/);
    expect(beats[5].facts[1]).toMatch(/31 years later/);
  });

  it("picks the beat for a timestamp and zooms the crop", () => {
    const elvis = TEMPLATES.find((t) => t.id === "elvis")!;
    const mid = beatAtTime(elvis, 25);
    expect(mid.index).toBe(2);
    const ken = kenBurnsAt(mid, mid.start);
    const later = kenBurnsAt(mid, mid.end);
    expect(later.scale).not.toBe(ken.scale);
    expect(later.scale).toBeGreaterThanOrEqual(1);
  });

  it("falls back to the hero still when an extra has one photo", () => {
    const magellan = TEMPLATES.find((t) => t.id === "magellan")!;
    expect(usesCollage(magellan)).toBe(false);
    expect(reelSlides(magellan)).toHaveLength(1);
    expect(reelSlides(magellan)[0].imageUrl).toContain("nao-victoria");
  });
});
