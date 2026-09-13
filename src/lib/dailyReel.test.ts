import { describe, expect, it } from "vitest";
import { TEMPLATES } from "../templates";
import {
  DAILY_TEMPLATE_BY_MD,
  dailyArtifactStem,
  monthDay,
  parseIsoDate,
  pickDailyTemplate,
} from "./dailyReel";

describe("daily reel calendar", () => {
  it("maps September 2 to the Japan surrender extra", () => {
    const reel = pickDailyTemplate(parseIsoDate("2026-09-02"));
    expect(reel?.id).toBe("japan-surrender");
    expect(TEMPLATES[0].id).toBe("apartheid");
    expect(DAILY_TEMPLATE_BY_MD["09-01"]).toBe("tupac");
    expect(dailyArtifactStem("japan-surrender")).toBe("japan_surrender");
  });

  it("maps September 3 to the Gloria Steinem extra", () => {
    const reel = pickDailyTemplate(parseIsoDate("2026-09-03"));
    expect(reel?.id).toBe("gloria-steinem");
    expect(dailyArtifactStem("gloria-steinem")).toBe("gloria_steinem");
  });

  it("maps September 5 to the Squeaky Fromme extra", () => {
    const reel = pickDailyTemplate(parseIsoDate("2026-09-05"));
    expect(reel?.id).toBe("squeaky-fromme");
    expect(dailyArtifactStem("squeaky-fromme")).toBe("squeaky_fromme");
  });

  it("maps September 6 to the Magellan extra", () => {
    const reel = pickDailyTemplate(parseIsoDate("2026-09-06"));
    expect(reel?.id).toBe("magellan");
    expect(dailyArtifactStem("magellan")).toBe("magellan");
  });

  it("maps September 8 to the Star Trek extra", () => {
    const reel = pickDailyTemplate(parseIsoDate("2026-09-08"));
    expect(reel?.id).toBe("star-trek");
    expect(dailyArtifactStem("star-trek")).toBe("star_trek");
  });

  it("maps September 9 to the Elvis extra", () => {
    const reel = pickDailyTemplate(parseIsoDate("2026-09-09"));
    expect(reel?.id).toBe("elvis");
    expect(dailyArtifactStem("elvis")).toBe("elvis");
  });

  it("maps September 10 to the LHC extra", () => {
    const reel = pickDailyTemplate(parseIsoDate("2026-09-10"));
    expect(reel?.id).toBe("lhc");
    expect(dailyArtifactStem("lhc")).toBe("lhc");
  });

  it("maps September 11 to the 9/11 extra", () => {
    const reel = pickDailyTemplate(parseIsoDate("2026-09-11"));
    expect(reel?.id).toBe("september-11");
    expect(dailyArtifactStem("september-11")).toBe("september_11");
  });

  it("maps September 13 to the Star-Spangled Banner extra", () => {
    const reel = pickDailyTemplate(parseIsoDate("2026-09-13"));
    expect(reel?.id).toBe("star-spangled-banner");
    expect(dailyArtifactStem("star-spangled-banner")).toBe(
      "star_spangled_banner",
    );
  });

  it("returns nothing on a day with no dated extra", () => {
    expect(pickDailyTemplate(parseIsoDate("2026-12-25"))).toBeUndefined();
  });

  it("formats local month-day with leading zeros", () => {
    expect(monthDay(parseIsoDate("2026-08-09"))).toBe("08-09");
  });
});
