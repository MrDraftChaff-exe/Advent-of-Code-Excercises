import type { ReelContent } from "../types";

/** Caption to paste under a Reel. Never drawn on the 9:16 frame. */
export function buildPasteCaption(reel: ReelContent): string {
  const custom = reel.postCaption?.trim();
  if (custom) return custom;
  const title = reel.title.trim() || "Facts or Whacks";
  const headline = reel.year.trim()
    ? `${title} (${reel.year.trim()})`
    : title;
  const facts = reel.bullets.map((b) => b.trim()).filter(Boolean).slice(0, 2);
  const tags = reel.hashtags.trim();
  const parts = [headline];
  if (facts.length) {
    parts.push("", ...facts);
  }
  parts.push("", reel.handle.trim() || "@FactsOrWhacks");
  if (tags) parts.push(tags);
  return parts.join("\n").trim();
}
