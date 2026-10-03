import { describe, expect, it } from "vitest";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

describe("collage encoder duration", () => {
  it("sets 30 fps inputs and does not use -shortest", () => {
    const src = readFileSync("scripts/stills_to_videos.py", "utf8");
    const start = src.indexOf("def encode_collage(");
    const end = src.indexOf("\ndef collect_stills(");
    expect(start).toBeGreaterThan(-1);
    expect(end).toBeGreaterThan(start);
    const fn = src.slice(start, end);
    expect(fn).toContain('"-framerate"');
    expect(fn).toContain("tpad=");
    expect(fn).not.toMatch(/"-shortest"/);
    expect(fn).toContain("overlays");
  });

  it("encodes an 8s six-still collage that is not short", () => {
    const dir = mkdtempSync(join(tmpdir(), "collage-"));
    const py = `
from pathlib import Path
from PIL import Image
import importlib.util
root = Path(${JSON.stringify(process.cwd())})
spec = importlib.util.spec_from_file_location("stills", root / "scripts/stills_to_videos.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
stills = []
for i, color in enumerate([(20,20,40),(180,40,30),(30,80,140),(200,160,40),(40,140,90),(90,40,140)]):
    p = Path(${JSON.stringify(dir)}) / f"beat-{i}.png"
    Image.new("RGB", (1080, 1920), color).save(p)
    stills.append(p)
dest = Path(${JSON.stringify(dir)}) / "out.mp4"
mod.encode_collage(mod.ffmpeg_bin(), stills, dest, 8.0, seed="duration-test")
print(mod.probe_duration(dest))
`;
    const run = spawnSync("python3", ["-c", py], { encoding: "utf8" });
    expect(run.status, `${run.stdout}\n${run.stderr}`).toBe(0);
    const duration = Number.parseFloat(run.stdout.trim().split("\n").at(-1) || "");
    expect(duration).toBeGreaterThanOrEqual(8);
  });

  it("zooms the photo and keeps an edge overlay inside the frame", () => {
    const dir = mkdtempSync(join(tmpdir(), "collage-lock-"));
    const py = `
from pathlib import Path
from PIL import Image, ImageDraw
import subprocess
import importlib.util
root = Path(${JSON.stringify(process.cwd())})
spec = importlib.util.spec_from_file_location("stills", root / "scripts/stills_to_videos.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
folder = Path(${JSON.stringify(dir)})
photo = Image.new("RGB", (1080, 1920), (220, 30, 30))
ImageDraw.Draw(photo).rectangle((0, 0, 1080, 36), fill=(20, 20, 240))
still = folder / "photo.png"
photo.save(still)
overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
ImageDraw.Draw(overlay).rectangle((0, 0, 1080, 64), fill=(40, 220, 60, 255))
plate = folder / "overlay.png"
overlay.save(plate)
dest = folder / "locked.mp4"
mod.encode_collage(mod.ffmpeg_bin(), [still], dest, 8.0, seed="lock-test", overlays=[plate])
frame = folder / "frame.png"
subprocess.check_call([
    "ffmpeg", "-y", "-ss", "6", "-i", str(dest), "-frames:v", "1", str(frame),
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
top = Image.open(frame).convert("RGB").getpixel((540, 8))
print(top[0], top[1], top[2])
`;
    const run = spawnSync("python3", ["-c", py], { encoding: "utf8" });
    expect(run.status, `${run.stdout}\n${run.stderr}`).toBe(0);
    const [r, g, b] = run.stdout
      .trim()
      .split("\n")
      .at(-1)!
      .split(" ")
      .map(Number);
    expect(g).toBeGreaterThan(r + 40);
    expect(g).toBeGreaterThan(b);
  });
});
