import { describe, expect, it } from "vitest";
import { spawnSync } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

describe("catalog video pad", () => {
  it("renders an original 30s wav", () => {
    const dir = mkdtempSync(join(tmpdir(), "pad-"));
    const out = join(dir, "pad.wav");
    const run = spawnSync(
      "python3",
      ["scripts/make_pad_audio.py", "--out", out, "--seconds", "1"],
      { encoding: "utf8" },
    );
    expect(run.status, run.stderr).toBe(0);
    const ff = spawnSync(
      "ffprobe",
      [
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=nw=1:nk=1",
        out,
      ],
      { encoding: "utf8" },
    );
    expect(ff.status, ff.stderr).toBe(0);
    expect(Number(ff.stdout.trim())).toBeGreaterThan(0.9);
  });
});
