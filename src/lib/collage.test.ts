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

  it("collages the Billie Jean extra across six public-domain stills", () => {
    const king = TEMPLATES.find((t) => t.id === "billie-jean");
    expect(king).toBeDefined();
    expect(usesCollage(king!)).toBe(true);
    expect(reelSlides(king!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(king!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/Bobby Riggs/);
    expect(beats[5].facts[1]).toMatch(/53 years ago tonight/);
  });

  it("collages the Rosetta extra as six FACT/WHACK beats", () => {
    const rosetta = TEMPLATES.find((t) => t.id === "rosetta");
    expect(rosetta).toBeDefined();
    expect(usesCollage(rosetta!)).toBe(true);
    expect(reelSlides(rosetta!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(rosetta!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/lost code/);
    expect(beats[0].facts[1]).toMatch(/French teacher/);
    expect(beats[5].facts[1]).toMatch(/204 years ago tonight/);
  });

  it("collages the Tylenol extra as six FACT/WHACK beats", () => {
    const tylenol = TEMPLATES.find((t) => t.id === "tylenol");
    expect(tylenol).toBeDefined();
    expect(usesCollage(tylenol!)).toBe(true);
    expect(reelSlides(tylenol!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(tylenol!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/factory/);
    expect(beats[0].facts[1]).toMatch(/store shelves/);
    expect(beats[5].facts[1]).toMatch(/44 years ago tonight/);
  });

  it("collages the James Dean extra as six FACT/WHACK beats", () => {
    const dean = TEMPLATES.find((t) => t.id === "james-dean");
    expect(dean).toBeDefined();
    expect(usesCollage(dean!)).toBe(true);
    expect(reelSlides(dean!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(dean!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/Rebel/);
    expect(beats[1].facts[1]).toMatch(/Porsche 550/);
    expect(beats[5].facts[1]).toMatch(/71 years ago tonight/);
  });

  it("collages the Model T extra as six FACT/WHACK beats", () => {
    const modelT = TEMPLATES.find((t) => t.id === "model-t");
    expect(modelT).toBeDefined();
    expect(usesCollage(modelT!)).toBe(true);
    expect(reelSlides(modelT!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(modelT!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/black/);
    expect(beats[0].facts[1]).toMatch(/red, green, and gray/);
    expect(beats[5].facts[1]).toMatch(/118 years ago tonight/);
  });

  it("collages the Freddie extra as six two-fact beats", () => {
    const freddie = TEMPLATES.find((t) => t.id === "freddie");
    expect(freddie).toBeDefined();
    expect(usesCollage(freddie!)).toBe(true);
    expect(reelSlides(freddie!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(freddie!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/5 minutes and 55 seconds/);
    expect(beats[5].facts[1]).toMatch(/277,000 pounds/);
    expect(beats.map((beat) => beat.imageUrl)).toEqual([
      "/images/freddie-1975.jpg",
      "/images/freddie-1977.jpg",
      "/images/freddie-1977-scarf.jpg",
      "/images/freddie-1977-stage.jpg",
      "/images/freddie-queen-1985.jpg",
      "/images/freddie-harlequin.jpg",
    ]);
  });

  it("collages the SNL extra as six two-fact beats", () => {
    const snl = TEMPLATES.find((t) => t.id === "snl");
    expect(snl).toBeDefined();
    expect(usesCollage(snl!)).toBe(true);
    expect(reelSlides(snl!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(snl!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/George Carlin/);
    expect(beats[5].facts[1]).toMatch(/51 years ago tonight/);
    expect(beats.map((beat) => beat.imageUrl)).toEqual([
      "/images/snl-carlin-1975.jpg",
      "/images/snl-chevy-1980.jpg",
      "/images/snl-belushi-1976.jpg",
      "/images/snl-kaufman-1979.jpg",
      "/images/snl-gilda-1979.jpg",
      "/images/snl-30-rock-1933.jpg",
    ]);
  });

  it("collages the Yeager extra as six two-fact beats", () => {
    const yeager = TEMPLATES.find((t) => t.id === "yeager");
    expect(yeager).toBeDefined();
    expect(usesCollage(yeager!)).toBe(true);
    expect(reelSlides(yeager!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(yeager!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/horse/);
    expect(beats[5].facts[1]).toMatch(/79 years ago tonight/);
    expect(beats.map((beat) => beat.imageUrl)).toEqual([
      "/images/yeager-1950.jpg",
      "/images/yeager-x1-cockpit.jpg",
      "/images/yeager-x1-b29.jpg",
      "/images/yeager-x1-rocket.jpg",
      "/images/yeager-xs1-team.jpg",
      "/images/yeager-x1-flight.jpg",
    ]);
  });

  it("collages the Disney extra as six two-fact beats", () => {
    const disney = TEMPLATES.find((t) => t.id === "disney");
    expect(disney).toBeDefined();
    expect(usesCollage(disney!)).toBe(true);
    expect(reelSlides(disney!).length).toBeGreaterThanOrEqual(5);
    const beats = collageBeats(disney!);
    expect(beats).toHaveLength(BEAT_COUNT);
    expect(beats[0].facts[0]).toMatch(/five years away/);
    expect(beats[5].facts[1]).toMatch(/103 years ago tonight/);
    expect(beats.map((beat) => beat.imageUrl)).toEqual([
      "/images/disney-walt-1938.jpg",
      "/images/disney-roy-1965.jpg",
      "/images/disney-alice-1926.jpg",
      "/images/disney-letterhead-1921.jpg",
      "/images/disney-kingswell-2015.jpg",
      "/images/disney-hyperion-1929.jpg",
    ]);
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

  it("ends the Yorktown series on Fact or whack after the payoff", () => {
    const yorktown = TEMPLATES.find((t) => t.id === "yorktown");
    expect(yorktown?.series).toBe("on-this-day");
    const beats = collageBeats(yorktown!);
    expect(beats[0].facts[0]).toMatch(/On this day in 1781/);
    expect(beats[5].facts).toContain(yorktown!.bullets[11]);
    expect(beats[5].facts[beats[5].facts.length - 1]).toBe("Fact or whack?");
  });

  it("ends the Alaska series on Fact or whack after the payoff", () => {
    const alaska = TEMPLATES.find((t) => t.id === "alaska");
    expect(alaska?.series).toBe("on-this-day");
    const beats = collageBeats(alaska!);
    expect(beats[0].facts[0]).toMatch(/On this day in 1867/);
    expect(beats[5].facts).toContain(alaska!.bullets[11]);
    expect(beats[5].facts[beats[5].facts.length - 1]).toBe("Fact or whack?");
  });

  it("adds Fact or whack only when the daily series flag is set", () => {
    const yeager = TEMPLATES.find((t) => t.id === "yeager");
    expect(yeager?.series).toBeUndefined();
    const beats = collageBeats({ ...yeager!, series: "on-this-day" });
    expect(beats[5].facts[beats[5].facts.length - 1]).toBe("Fact or whack?");
    expect(collageBeats(yeager!)[5].facts).not.toContain("Fact or whack?");
  });

  it("falls back to the hero still when an extra has one photo", () => {
    const magellan = TEMPLATES.find((t) => t.id === "magellan")!;
    expect(usesCollage(magellan)).toBe(false);
    expect(reelSlides(magellan)).toHaveLength(1);
    expect(reelSlides(magellan)[0].imageUrl).toContain("nao-victoria");
  });
});
