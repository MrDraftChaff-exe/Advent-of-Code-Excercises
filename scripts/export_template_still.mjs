#!/usr/bin/env node
/**
 * Render a 9:16 PNG for one studio template.
 *
 * Usage:
 *   node scripts/export_template_still.mjs --id dolly
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const puppeteer = require("/tmp/node_modules/puppeteer-core");

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const OUT_DIR = path.join(ROOT, "dist/template-stills");
const BASE = "http://127.0.0.1:5173";
const CHROME = "/usr/local/bin/google-chrome";

function arg(name, fallback = "") {
  const idx = process.argv.indexOf(`--${name}`);
  if (idx >= 0 && process.argv[idx + 1]) return process.argv[idx + 1];
  return fallback;
}

async function main() {
  const id = arg("id", "dolly");
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

  const result = await page.evaluate(async (templateId) => {
    const templates = await import("/src/templates.ts");
    const draw = await import("/src/lib/drawReel.ts");
    const fonts = await import("/src/lib/fonts.ts");
    const reel = templates.TEMPLATES.find((t) => t.id === templateId);
    if (!reel) {
      throw new Error(`Unknown template ${templateId}`);
    }
    const blob = await draw.snapshotPng(reel, 4);
    const dataUrl = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result));
      reader.onerror = () => reject(new Error("read failed"));
      reader.readAsDataURL(blob);
    });
    const slug = fonts.slugify(`${reel.episode}-${reel.title}`);
    return { slug, bytes: blob.size, dataUrl };
  }, id);

  const file = path.join(OUT_DIR, `${result.slug}.png`);
  const buf = Buffer.from(result.dataUrl.split(",")[1], "base64");
  fs.writeFileSync(file, buf);
  await browser.close();
  console.log(`Wrote ${file} (${buf.length} bytes)`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
