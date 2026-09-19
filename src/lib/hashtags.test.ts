import { describe, expect, it } from "vitest";
import { TEMPLATES, blankReel } from "../templates";
import {
  MAX_HASHTAGS,
  isBannedHashtag,
  sanitizeHashtags,
} from "./hashtags";

function tagsOf(raw: string): string[] {
  return raw.split(/\s+/).filter(Boolean);
}

describe("hashtag house rule", () => {
  it("drops platform tags, fillers, and anything past five", () => {
    expect(
      sanitizeHashtags(
        "#PrincessDiana #HistoryTok #DidYouKnow #FactsOrWhacks #OnThisDay #RoyalFamily #Diana #Landmines #Panorama",
      ),
    ).toBe("#PrincessDiana #RoyalFamily #Diana #Landmines #Panorama");
    expect(sanitizeHashtags("#MovieTok #TrueCrimeTok #FYP")).toBe("");
    expect(sanitizeHashtags("#HistoryTok", "Jack the Ripper")).toBe(
      "#Jack #Ripper",
    );
  });

  it("keeps every studio template to five topic tags", () => {
    for (const template of [...TEMPLATES, blankReel()]) {
      const tags = tagsOf(template.hashtags);
      expect(tags.length, template.id).toBeGreaterThan(0);
      expect(tags.length, template.id).toBeLessThanOrEqual(MAX_HASHTAGS);
      for (const tag of tags) {
        expect(isBannedHashtag(tag), `${template.id} ${tag}`).toBe(false);
      }
    }
  });
});
