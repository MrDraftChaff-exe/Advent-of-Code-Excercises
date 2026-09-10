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
});
