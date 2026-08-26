import type { CatalogEpisode } from "./catalog";
import { extractYear } from "./catalog";
import type { ReelContent } from "../types";

const HANDLE = "@FactsOrWhacks";
const BRAND_TAG = "#FactsOrWhacks";

/** Collapse caption pieces to one line so a CSV cell copies in one click. */
export function oneLine(...chunks: string[]): string {
  return chunks
    .flatMap((chunk) => chunk.split(/\s+/))
    .filter(Boolean)
    .join(" ");
}

export function brandHashtags(raw: string): string {
  const tags: string[] = [];
  const seen = new Set<string>();
  for (const token of raw.split(/\s+/)) {
    if (!token) continue;
    const tag = token.startsWith("#") ? token : `#${token}`;
    const key = tag.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    tags.push(tag);
  }
  if (!seen.has(BRAND_TAG.toLowerCase())) tags.push(BRAND_TAG);
  return tags.join(" ");
}

/** Caption to paste under a Reel. Custom postCaption keeps its line breaks. */
export function buildPasteCaption(reel: ReelContent): string {
  const custom = reel.postCaption?.trim();
  if (custom) return custom;
  return catalogStyleCaption(
    reel.title,
    reel.year,
    "",
    reel.bullets,
    reel.hashtags,
    reel.handle,
  );
}

/** One-line description + handle + hashtags for spreadsheet / catalog copy. */
export function catalogCopyCaption(ep: CatalogEpisode): string {
  const year = extractYear(ep.title, ep.hook, ...ep.bullets);
  return catalogStyleCaption(
    ep.title,
    year,
    ep.hook,
    ep.bullets,
    ep.tags,
    HANDLE,
  );
}

export function glueSentences(...chunks: string[]): string {
  const parts = chunks.map((chunk) => oneLine(chunk)).filter(Boolean);
  if (!parts.length) return "";
  let out = parts[0];
  for (const part of parts.slice(1)) {
    if (!/[.!?…]$/.test(out)) out += ".";
    out += ` ${part}`;
  }
  return out;
}

export function catalogStyleCaption(
  title: string,
  year: string,
  hook: string,
  bullets: string[],
  tags: string,
  handle = HANDLE,
): string {
  const headline = year.trim()
    ? `${title.trim()} (${year.trim()})`
    : title.trim() || "Facts or Whacks";
  const facts = bullets.map((b) => b.trim()).filter(Boolean).slice(0, 2);
  return oneLine(
    glueSentences(headline, hook, ...facts),
    handle.trim() || HANDLE,
    brandHashtags(tags),
  );
}
