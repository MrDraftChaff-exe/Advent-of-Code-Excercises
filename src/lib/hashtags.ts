/** Caption hashtags: five topic tags, no platform bait, no repeating fillers. */
export const MAX_HASHTAGS = 5;

const BANNED = new Set([
  "didyouknow",
  "factsorwhacks",
  "onthisday",
  "fyp",
  "foryou",
  "foryoupage",
  "viral",
  "trending",
  "reels",
  "shorts",
  "tiktok",
  "instagram",
  "youtube",
  "youtubeshorts",
  "historymatters",
  "historyfacts",
  "weirdhistory",
]);

export function isBannedHashtag(tag: string): boolean {
  const key = tag.replace(/^#/, "").toLowerCase();
  if (!key) return true;
  if (key.endsWith("tok")) return true;
  return BANNED.has(key);
}

function titleFallback(title: string): string[] {
  const tags: string[] = [];
  const seen = new Set<string>();
  for (const word of title.split(/[^A-Za-z0-9]+/)) {
    if (word.length < 4 || isBannedHashtag(word)) continue;
    const tag = `#${word}`;
    const key = tag.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    tags.push(tag);
    if (tags.length >= MAX_HASHTAGS) break;
  }
  return tags;
}

/** At most five unique, topic-specific hashtags. */
export function sanitizeHashtags(raw: string, fallbackTitle = ""): string {
  const tags: string[] = [];
  const seen = new Set<string>();
  for (const token of raw.split(/\s+/)) {
    if (!token) continue;
    const tag = token.startsWith("#") ? token : `#${token}`;
    if (isBannedHashtag(tag)) continue;
    const key = tag.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    tags.push(tag);
    if (tags.length >= MAX_HASHTAGS) break;
  }
  if (!tags.length) tags.push(...titleFallback(fallbackTitle));
  return tags.join(" ");
}

/** @deprecated Use sanitizeHashtags. Kept so older tests still compile during the swap. */
export const brandHashtags = sanitizeHashtags;
