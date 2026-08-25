import { describe, expect, it } from "vitest";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

function parseCsv(text: string): string[][] {
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

describe("video captions CSV", () => {
  it("maps every episode to a unique MP4 name, caption, and hashtags", () => {
    const dir = mkdtempSync(join(tmpdir(), "caps-"));
    const out = join(dir, "captions.csv");
    const run = spawnSync(
      "python3",
      [
        "scripts/write_video_captions_csv.py",
        "--episodes",
        "public/catalog/episodes.json",
        "--out",
        out,
      ],
      { encoding: "utf8" },
    );
    expect(run.status, run.stderr).toBe(0);
    const rows = parseCsv(readFileSync(out, "utf8"));
    const header = rows[0];
    const body = rows.slice(1);
    expect(header).toContain("video_filename");
    expect(header).toContain("paste_caption");
    expect(header).toContain("hashtags");
    expect(body).toHaveLength(395);

    const fileIdx = header.indexOf("video_filename");
    const packIdx = header.indexOf("video_zip_pack");
    const hashIdx = header.indexOf("hashtags");
    const pasteIdx = header.indexOf("paste_caption");
    const titleIdx = header.indexOf("title");
    const numIdx = header.indexOf("episode_number");

    const names = body.map((r) => r[fileIdx]);
    expect(new Set(names).size).toBe(395);
    expect(body[0][fileIdx]).toBe("001-the-enlightenment.mp4");
    expect(body[0][packIdx]).toBe("facts-or-whacks-videos-001-050.zip");
    const apartheid = body.find((r) => r[numIdx] === "30");
    expect(apartheid?.[fileIdx]).toBe("030-end-of-apartheid.mp4");
    expect(apartheid?.[titleIdx]).toMatch(/apartheid/i);
    expect(apartheid?.[packIdx]).toBe("facts-or-whacks-videos-001-050.zip");
    expect(apartheid?.[hashIdx]).toContain("#NelsonMandela");
    expect(apartheid?.[pasteIdx]).toContain("@FactsOrWhacks");
    expect(apartheid?.[pasteIdx]).toContain("#");
    expect(body.every((r) => r[hashIdx].includes("#FactsOrWhacks"))).toBe(true);
    expect(body[394][fileIdx]).toMatch(/^395-/);
    expect(body[394][packIdx]).toBe("facts-or-whacks-videos-351-395.zip");
  });
});
