#!/usr/bin/env node
/**
 * Render a 9:16 PNG still for every catalog episode using the studio canvas.
 *
 * Usage:
 *   node scripts/export_catalog_stills.mjs
 *   node scripts/export_catalog_stills.mjs --from 1 --to 10
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const puppeteer = require("/tmp/node_modules/puppeteer-core");

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const OUT_DIR = path.join(ROOT, "dist/catalog-stills");
const BASE = "http://127.0.0.1:5173";
const CHROME = "/usr/local/bin/google-chrome";

function arg(name, fallback) {
  const idx = process.argv.indexOf(`--${name}`);
  if (idx >= 0 && process.argv[idx + 1]) return Number(process.argv[idx + 1]);
  return fallback;
}

const fromN = arg("from", 1);
const toN = arg("to", 395);

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: "new",
    args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
  });
  const page = await browser.newPage();
  page.setDefaultTimeout(120_000);
  await page.goto(BASE, { waitUntil: "networkidle0" });
  await page.evaluate(async () => {
    const fonts = await import("/src/lib/fonts.ts");
    await fonts.loadReelFonts();
    await document.fonts.load("800 80px Montserrat");
    await document.fonts.load("700 50px Montserrat");
  });

  const total = await page.evaluate(async () => {
    const catalog = await import("/src/lib/catalog.ts");
    const res = await fetch("/catalog/episodes.json");
    if (!res.ok) throw new Error("Could not load catalog");
    const episodes = catalog.parseCatalogJson(await res.json());
    globalThis.__catalogEpisodes = episodes;
    return episodes.length;
  });
  if (total !== 395) throw new Error(`Expected 395 episodes, got ${total}`);

  const start = Math.max(1, fromN);
  const end = Math.min(395, toN);
  console.log(`Rendering stills ${start}–${end} of ${total}`);

  for (let n = start; n <= end; n++) {
    const result = await page.evaluate(async (index) => {
      const catalog = await import("/src/lib/catalog.ts");
      const draw = await import("/src/lib/drawReel.ts");
      const fonts = await import("/src/lib/fonts.ts");
      const templates = await import("/src/templates.ts");
      const episodes = globalThis.__catalogEpisodes;
      const ep = episodes[index];
      const reel =
        ep.n === 30
          ? { ...templates.TEMPLATES[0], bullets: [...templates.TEMPLATES[0].bullets] }
          : catalog.episodeToReel(ep);
      const blob = await draw.snapshotPng(reel, 4);
      const dataUrl = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result));
        reader.onerror = () => reject(new Error("read failed"));
        reader.readAsDataURL(blob);
      });
      const slug = fonts.slugify(`${String(ep.n).padStart(3, "0")}-${ep.title}`);
      return { slug, bytes: blob.size, dataUrl };
    }, n - 1);

    const file = path.join(OUT_DIR, `${result.slug}.png`);
    const buf = Buffer.from(result.dataUrl.split(",")[1], "base64");
    fs.writeFileSync(file, buf);
    if (n === start || n % 25 === 0 || n === end) {
      console.log(`${n}/${end} ${result.slug}.png (${buf.length} bytes)`);
    }
  }

  await browser.close();
  console.log(`Wrote stills ${start}–${end} to ${OUT_DIR}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
