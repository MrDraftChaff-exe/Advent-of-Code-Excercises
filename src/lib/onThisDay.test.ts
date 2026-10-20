import { describe, expect, it } from "vitest";
import { TEMPLATES } from "../templates";
import { collageBeats } from "./collage";
import {
  PINNED_COMMENT,
  SERIES_CLOSER,
  seriesCaption,
  seriesHashtags,
  seriesIntro,
  seriesSpeak,
} from "./onThisDay";

describe("on this day series", () => {
  it("uses one intro shape and one closer", () => {
    expect(seriesIntro("1947", "a man broke the sound barrier with two broken ribs.")).toBe(
      "On this day in 1947, a man broke the sound barrier with two broken ribs",
    );
    expect(SERIES_CLOSER).toBe("Fact or whack?");
    expect(PINNED_COMMENT).toBe("Guess fact or whack before you watch.");
  });

  it("tags historytok, historyfacts, and one topic, and leaves fyp off", () => {
    expect(seriesHashtags("Yeager")).toBe("#historytok #historyfacts #Yeager");
    expect(seriesHashtags("#Yeager")).not.toMatch(/fyp/i);
  });

  it("writes a plain hook, not a riddle", () => {
    const caption = seriesCaption(
      "1947",
      "a man broke the sound barrier with two broken ribs",
      "He locked the door with a broom handle",
      "Yeager",
    );
    expect(caption.startsWith("On this day in 1947,")).toBe(true);
    expect(caption).toContain("broom handle");
    expect(caption).toContain("Follow @FactsOrWhacks");
    expect(caption).toContain("#historytok #historyfacts #Yeager");
    expect(caption).not.toMatch(/horse doctor/);
  });

  it("gives the same spoken open and the same closer to record", () => {
    const script = seriesSpeak("1947", "a man broke the sound barrier with two broken ribs");
    expect(script).toContain("On this day in 1947, a man broke the sound barrier with two broken ribs.");
    expect(script).toContain("Fact or whack?");
    expect(script).toContain(PINNED_COMMENT);
  });

  it("ends a series collage on Fact or whack without dropping the payoff", () => {
    const yeager = TEMPLATES.find((t) => t.id === "yeager");
    expect(yeager).toBeDefined();
    const beats = collageBeats({ ...yeager!, series: "on-this-day" });
    expect(beats[0].facts[0]).toBe(yeager!.bullets[0]);
    expect(beats[5].facts).toContain(yeager!.bullets[11]);
    expect(beats[5].facts[beats[5].facts.length - 1]).toBe("Fact or whack?");
    const plain = collageBeats(yeager!);
    expect(plain[5].facts).not.toContain("Fact or whack?");
  });
});
