import type { ReelContent, ThemeId } from "../types";

export type CatalogEpisode = {
  n: number;
  title: string;
  hook: string;
  bullets: string[];
  image: string;
  tags: string;
  credit: string;
  source: string;
};

const THEME_CYCLE: ThemeId[] = ["cosmic", "ocean", "ember"];
const FILLER = /\s+[—–-]\s+a key part of the story of\s+.+$/i;

export const TARGET_FACT_COUNT = 12;

export function cleanBullet(text: string): string {
  return text.replace(FILLER, "").replace(/\s+/g, " ").trim();
}

export function splitBullets(raw: string): string[] {
  return raw
    .split(/\s*\|\s*|\n+/)
    .map(cleanBullet)
    .filter(Boolean);
}

export function extractYear(...chunks: string[]): string {
  const text = chunks.join(" ");
  const matches = text.match(/\b(1[0-9]{3}|20[0-2][0-9])\b/g);
  return matches ? matches[matches.length - 1] : "";
}

export function episodeToReel(ep: CatalogEpisode): ReelContent {
  const bullets = ep.bullets.map(cleanBullet).filter(Boolean);
  return {
    id: `catalog-${ep.n}`,
    name: `${ep.n}. ${ep.title}`,
    episode: String(ep.n),
    title: ep.title,
    year: extractYear(ep.title, ep.hook, ...bullets),
    imageUrl: ep.image,
    imageCaption: ep.hook,
    imageCredit: ep.credit.trim() || "Wikimedia Commons",
    bullets: bullets.length ? bullets : ["Add a sentence fact."],
    hashtags: ep.tags,
    handle: "@FactsOrWhacks",
    durationSec: 20,
    theme: THEME_CYCLE[(Math.max(1, ep.n) - 1) % THEME_CYCLE.length],
    reveal: "hold",
  };
}

/** Minimal RFC4180 parser for the catalog CSV. */
export function parseCatalogCsv(text: string): CatalogEpisode[] {
  const rows = parseCsvRows(text);
  if (!rows.length) return [];
  const header = rows[0].map((h) => h.trim());
  const idx = (name: string) => header.indexOf(name);
  const topic = idx("topic_number");
  const title = idx("title");
  const hook = idx("hook");
  const bullets = idx("on_screen_bullets");
  const image = idx("image_url");
  const tags = idx("hashtags");
  const credit = idx("image_credit");
  const source = idx("image_source");
  const out: CatalogEpisode[] = [];
  for (const row of rows.slice(1)) {
    const n = Number(row[topic] ?? "");
    if (!Number.isFinite(n) || n <= 0) continue;
    out.push({
      n,
      title: (row[title] ?? "").trim(),
      hook: (row[hook] ?? "").trim(),
      bullets: splitBullets(row[bullets] ?? ""),
      image: (row[image] ?? "").trim(),
      tags: (row[tags] ?? "").trim(),
      credit: credit >= 0 ? (row[credit] ?? "").trim() : "",
      source: source >= 0 ? (row[source] ?? "").trim() : "",
    });
  }
  return out;
}

export function parseCatalogJson(data: unknown): CatalogEpisode[] {
  if (!Array.isArray(data)) return [];
  return data
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const rec = item as Record<string, unknown>;
      const n = Number(rec.n);
      if (!Number.isFinite(n) || n <= 0) return null;
      const bullets = Array.isArray(rec.bullets)
        ? rec.bullets.map((b) => cleanBullet(String(b))).filter(Boolean)
        : [];
      return {
        n,
        title: String(rec.title ?? "").trim(),
        hook: String(rec.hook ?? "").trim(),
        bullets,
        image: String(rec.image ?? "").trim(),
        tags: String(rec.tags ?? "").trim(),
        credit: String(rec.credit ?? "").trim(),
        source: String(rec.source ?? "").trim(),
      } satisfies CatalogEpisode;
    })
    .filter((ep): ep is CatalogEpisode => ep !== null);
}

export async function loadBundledCatalog(): Promise<CatalogEpisode[]> {
  const res = await fetch("/catalog/episodes.json");
  if (!res.ok) throw new Error("Could not load episode catalog");
  return parseCatalogJson(await res.json());
}

function parseCsvRows(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let inQuotes = false;
  const src = text.replace(/^\uFEFF/, "");
  for (let i = 0; i < src.length; i++) {
    const ch = src[i];
    if (inQuotes) {
      if (ch === '"') {
        if (src[i + 1] === '"') {
          cell += '"';
          i += 1;
        } else {
          inQuotes = false;
        }
      } else {
        cell += ch;
      }
      continue;
    }
    if (ch === '"') {
      inQuotes = true;
      continue;
    }
    if (ch === ",") {
      row.push(cell);
      cell = "";
      continue;
    }
    if (ch === "\n") {
      row.push(cell);
      rows.push(row);
      row = [];
      cell = "";
      continue;
    }
    if (ch === "\r") continue;
    cell += ch;
  }
  if (cell.length || row.length) {
    row.push(cell);
    rows.push(row);
  }
  return rows;
}
