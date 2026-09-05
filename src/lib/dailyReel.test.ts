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

  it("returns nothing on a day with no dated extra", () => {
    expect(pickDailyTemplate(parseIsoDate("2026-12-25"))).toBeUndefined();
  });

  it("formats local month-day with leading zeros", () => {
    expect(monthDay(parseIsoDate("2026-08-09"))).toBe("08-09");
  });
});
