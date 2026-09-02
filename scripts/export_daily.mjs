#!/usr/bin/env node
/**
 * Export today's dated studio extra through the running Vite app:
 * 9:16 PNG, 30s MP4 with a unique pad, paste caption.
 *
 * Usage:
 *   npm run dev   # already listening on http://127.0.0.1:5173
 *   npm run daily:pack
 *   npm run daily:pack -- --date 2026-09-02
 *   npm run daily:pack -- --id japan-surrender
 */
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
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

function copyIfDir(src, destDir, name) {
  if (!fs.existsSync(destDir)) return;
  fs.copyFileSync(src, path.join(destDir, name));
}

async function studioUp() {
  try {
    const res = await fetch(BASE, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

async function main() {
  if (!(await studioUp())) {
    console.error(
      `Studio is not running at ${BASE}. Start it with: npm run dev`,
    );
    process.exit(1);
  }

  const forcedId = arg("id");
  const dateArg = arg("date");

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

  const result = await page.evaluate(
    async ({ forcedId, dateArg }) => {
      const templates = await import("/src/templates.ts");
      const daily = await import("/src/lib/dailyReel.ts");
      const draw = await import("/src/lib/drawReel.ts");
      const fonts = await import("/src/lib/fonts.ts");
      const reel = forcedId
        ? templates.TEMPLATES.find((t) => t.id === forcedId)
        : daily.pickDailyTemplate(
            dateArg ? daily.parseIsoDate(dateArg) : new Date(),
          );
      if (!reel) {
        throw new Error(
          forcedId
            ? `Unknown template ${forcedId}`
            : "No dated extra for this calendar day. Search the catalog in the studio, or pass --id.",
        );
      }
      const blob = await draw.snapshotPng(reel, 4);
      const dataUrl = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result));
        reader.onerror = () => reject(new Error("read failed"));
        reader.readAsDataURL(blob);
      });
      const slug = fonts.slugify(`${reel.episode}-${reel.title}`);
      return {
        id: reel.id,
        slug,
        caption: reel.postCaption || "",
        stem: daily.dailyArtifactStem(reel.id),
        dataUrl,
      };
    },
    { forcedId, dateArg },
  );

  await browser.close();

  fs.mkdirSync(OUT_DIR, { recursive: true });
  const still = path.join(OUT_DIR, `${result.slug}.png`);
  const buf = Buffer.from(result.dataUrl.split(",")[1], "base64");
  fs.writeFileSync(still, buf);

  const captionName = `${result.stem}_post.txt`;
  const captionPath = path.join(OUT_DIR, captionName);
  fs.writeFileSync(captionPath, `${result.caption.trim()}\n`);

  const destMp4 = path.join(OUT_DIR, `${result.slug}.mp4`);
  if (fs.existsSync(destMp4) && fs.statSync(destMp4).size > 50_000) {
    fs.unlinkSync(destMp4);
  }

  const encodePy = [
    "from pathlib import Path",
    "import importlib.util",
    "spec = importlib.util.spec_from_file_location('stills', 'scripts/stills_to_videos.py')",
    "mod = importlib.util.module_from_spec(spec)",
    "spec.loader.exec_module(mod)",
    `still = Path(${JSON.stringify(still)})`,
    `dest = Path(${JSON.stringify(destMp4)})`,
    `mod.encode_one(mod.ffmpeg_bin(), still, None, dest, 30.0, seed=${JSON.stringify(result.slug)})`,
    "print(dest, dest.stat().st_size)",
  ].join("\n");
  const encode = spawnSync("python3", ["-c", encodePy], {
    cwd: ROOT,
    encoding: "utf8",
  });
  if (encode.status !== 0) {
    console.error(encode.stdout);
    console.error(encode.stderr);
    process.exit(encode.status || 1);
  }

  const stillName = `${result.stem}_9x16_still.png`;
  const videoName = `${result.stem}_30s.mp4`;
  const packedStill = path.join(OUT_DIR, stillName);
  const packedVideo = path.join(OUT_DIR, videoName);
  fs.copyFileSync(still, packedStill);
  fs.copyFileSync(destMp4, packedVideo);

  for (const dir of ["/opt/cursor/artifacts", "/home/ubuntu/Desktop"]) {
    copyIfDir(packedStill, dir, stillName);
    copyIfDir(packedVideo, dir, videoName);
    copyIfDir(captionPath, dir, captionName);
  }

  console.log(`Wrote ${still} (${buf.length} bytes)`);
  console.log(encode.stdout.trim());
  console.log(`Caption ${captionPath}`);
  console.log(`Pack ${stillName} ${videoName} ${captionName}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
