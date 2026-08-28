import { describe, expect, it } from "vitest";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

describe("catalog video pad", () => {
  it("renders an original stereo wav unique to the seed", () => {
    const dir = mkdtempSync(join(tmpdir(), "pad-"));
    const a = join(dir, "a.wav");
    const b = join(dir, "b.wav");
    const runA = spawnSync(
      "python3",
      [
        "scripts/make_pad_audio.py",
        "--out",
        a,
        "--seconds",
        "1",
        "--seed",
        "396-dolly-parton",
      ],
      { encoding: "utf8" },
    );
    const runB = spawnSync(
      "python3",
      [
        "scripts/make_pad_audio.py",
        "--out",
        b,
        "--seconds",
        "1",
        "--seed",
        "400-btk",
      ],
      { encoding: "utf8" },
    );
    expect(runA.status, runA.stderr).toBe(0);
    expect(runB.status, runB.stderr).toBe(0);
    expect(readFileSync(a).equals(readFileSync(b))).toBe(false);
    const ff = spawnSync(
      "ffprobe",
      [
        "-v",
        "error",
        "-show_entries",
        "stream=channels,codec_name:format=duration",
        "-of",
        "default=nw=1:nk=1",
        a,
      ],
      { encoding: "utf8" },
    );
    expect(ff.status, ff.stderr).toBe(0);
    const lines = ff.stdout.trim().split("\n");
    expect(lines).toContain("pcm_s16le");
    expect(lines).toContain("2");
    expect(Number(lines.at(-1))).toBeGreaterThan(0.9);
  });
});
