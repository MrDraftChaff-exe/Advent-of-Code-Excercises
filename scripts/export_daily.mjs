#!/usr/bin/env node
/**
 * Export today's dated studio extra through the running Vite app:
 * 9:16 poster PNG, 60s collage MP4 with Ken Burns + unique pad, paste caption.
 *
 * Usage:
 *   npm run dev   # already listening on http://127.0.0.1:5173
 *   npm run daily:pack
 *   npm run daily:pack -- --date 2026-09-09
 *   npm run daily:pack -- --id elvis
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
const VIDEO_SECONDS = 60;

function arg(name, fallback = "") {
  const idx = process.argv.indexOf(`--${name}`);
  if (idx >= 0 && process.argv[idx + 1]) return process.argv[idx + 1];
  return fallback;
}

function copyIfDir(src, destDir, name) {
  if (!fs.existsSync(destDir)) return;
  fs.copyFileSync(src, path.join(destDir, name));
}

function writePng(file, dataUrl) {
  const buf = Buffer.from(String(dataUrl).split(",")[1], "base64");
  fs.writeFileSync(file, buf);
  return buf.length;
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
  page.setDefaultTimeout(180_000);
  await page.goto(BASE, { waitUntil: "networkidle0" });
  await page.evaluate(async () => {
    const fonts = await import("/src/lib/fonts.ts");
    await fonts.loadReelFonts();
    await document.fonts.load("800 80px Montserrat");
    await document.fonts.load("700 50px Montserrat");
  });

  const result = await page.evaluate(
    async ({ forcedId, dateArg, videoSeconds }) => {
      const templates = await import("/src/templates.ts");
      const daily = await import("/src/lib/dailyReel.ts");
      const draw = await import("/src/lib/drawReel.ts");
      const fonts = await import("/src/lib/fonts.ts");
      const collage = await import("/src/lib/collage.ts");
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
      const videoReel = { ...reel, durationSec: videoSeconds };
      const poster = await draw.snapshotPng(reel, 4);
      const toUrl = (blob) =>
        new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(String(reader.result));
          reader.onerror = () => reject(new Error("read failed"));
          reader.readAsDataURL(blob);
        });
      const beats = collage.collageBeats(videoReel);
      const beatUrls = [];
      for (let i = 0; i < beats.length; i++) {
        const blob = await draw.snapshotBeatPng(videoReel, i);
        beatUrls.push(await toUrl(blob));
      }
      const slug = fonts.slugify(`${reel.episode}-${reel.title}`);
      return {
        id: reel.id,
        slug,
        caption: reel.postCaption || "",
        stem: daily.dailyArtifactStem(reel.id),
        posterUrl: await toUrl(poster),
        beatUrls,
      };
    },
    { forcedId, dateArg, videoSeconds: VIDEO_SECONDS },
  );

  await browser.close();

  fs.mkdirSync(OUT_DIR, { recursive: true });
  const still = path.join(OUT_DIR, `${result.slug}.png`);
  const posterBytes = writePng(still, result.posterUrl);

  const beatDir = path.join(OUT_DIR, `${result.slug}-beats`);
  fs.mkdirSync(beatDir, { recursive: true });
  const beatFiles = result.beatUrls.map((url, i) => {
    const file = path.join(beatDir, `beat-${String(i).padStart(2, "0")}.png`);
    writePng(file, url);
    return file;
  });

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
    `stills = [Path(p) for p in ${JSON.stringify(beatFiles)}]`,
    `dest = Path(${JSON.stringify(destMp4)})`,
    `mod.encode_collage(mod.ffmpeg_bin(), stills, dest, ${VIDEO_SECONDS}, seed=${JSON.stringify(result.slug)})`,
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
  const videoName = `${result.stem}_60s.mp4`;
  const packedStill = path.join(OUT_DIR, stillName);
  const packedVideo = path.join(OUT_DIR, videoName);
  fs.copyFileSync(still, packedStill);
  fs.copyFileSync(destMp4, packedVideo);

  for (const dir of ["/opt/cursor/artifacts", "/home/ubuntu/Desktop"]) {
    copyIfDir(packedStill, dir, stillName);
    copyIfDir(packedVideo, dir, videoName);
    copyIfDir(captionPath, dir, captionName);
  }

  console.log(`Wrote ${still} (${posterBytes} bytes)`);
  console.log(`Beats ${beatFiles.length} in ${beatDir}`);
  console.log(encode.stdout.trim());
  console.log(`Caption ${captionPath}`);
  console.log(`Pack ${stillName} ${videoName} ${captionName}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
