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
  it("maps every video to a one-line copy_caption with description and hashtags", () => {
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
    const raw = readFileSync(out, "utf8");
    const physicalLines = raw.replace(/^\uFEFF/, "").trimEnd().split("\n");
    expect(physicalLines).toHaveLength(404);

    const rows = parseCsv(raw);
    const header = rows[0];
    const body = rows.slice(1);
    expect(header[0]).toBe("video_filename");
    expect(header[1]).toBe("copy_caption");
    expect(header).toContain("hashtags");
    expect(header).toContain("description");
    expect(header).not.toContain("paste_caption");
    expect(body).toHaveLength(403);

    const fileIdx = header.indexOf("video_filename");
    const copyIdx = header.indexOf("copy_caption");
    const packIdx = header.indexOf("video_zip_pack");
    const hashIdx = header.indexOf("hashtags");
    const descIdx = header.indexOf("description");
    const titleIdx = header.indexOf("title");
    const numIdx = header.indexOf("episode_number");

    const names = body.map((r) => r[fileIdx]);
    expect(new Set(names).size).toBe(403);
    expect(body[0][fileIdx]).toBe("001-the-enlightenment.mp4");
    expect(body[0][packIdx]).toBe("facts-or-whacks-videos-001-050.zip");
    const apartheid = body.find((r) => r[numIdx] === "30");
    expect(apartheid?.[fileIdx]).toBe("030-end-of-apartheid.mp4");
    expect(apartheid?.[titleIdx]).toMatch(/apartheid/i);
    expect(apartheid?.[packIdx]).toBe("facts-or-whacks-videos-001-050.zip");
    expect(apartheid?.[hashIdx]).toContain("#NelsonMandela");
    expect(apartheid?.[copyIdx]).toContain("@FactsOrWhacks");
    expect(apartheid?.[copyIdx]).toContain("#NelsonMandela");
    expect(apartheid?.[copyIdx]).toContain(apartheid?.[descIdx] ?? "missing");
    expect(apartheid?.[copyIdx]).not.toMatch(/\r|\n/);
    expect(
      body.every((r) => {
        const tags = r[hashIdx].split(/\s+/).filter(Boolean);
        if (tags.length > 5) return false;
        return tags.every(
          (tag) =>
            !/tok$/i.test(tag) &&
            !/^#(didyouknow|factsorwhacks|onthisday|fyp|foryou)$/i.test(tag),
        );
      }),
    ).toBe(true);
    expect(body.every((r) => !r[copyIdx].includes("\n"))).toBe(true);
    expect(body.every((r) => r[copyIdx].includes("@FactsOrWhacks"))).toBe(true);
    expect(body.every((r) => r[copyIdx].includes("#"))).toBe(true);

    const catalog = body.filter((r) => Number(r[numIdx]) <= 395);
    expect(catalog).toHaveLength(395);
    expect(catalog[394][fileIdx]).toMatch(/^395-/);
    expect(catalog[394][packIdx]).toBe("facts-or-whacks-videos-351-395.zip");

    const dolly = body.find((r) => r[numIdx] === "396");
    expect(dolly?.[fileIdx]).toBe("396-dolly-parton.mp4");
    expect(dolly?.[copyIdx]).toContain("#DollyParton");
    expect(dolly?.[copyIdx]).not.toMatch(/\r|\n/);

    const curry = body.find((r) => r[numIdx] === "397");
    expect(curry?.[fileIdx]).toBe("397-tim-curry.mp4");
    expect(curry?.[copyIdx]).toContain("#TimCurry");
    expect(curry?.[copyIdx]).not.toMatch(/\r|\n/);

    const cullen = body.find((r) => r[numIdx] === "398");
    expect(cullen?.[fileIdx]).toBe("398-peter-cullen.mp4");
    expect(cullen?.[copyIdx]).toContain("#PeterCullen");
    expect(cullen?.[copyIdx]).not.toMatch(/\r|\n/);

    const hayden = body.find((r) => r[numIdx] === "399");
    expect(hayden?.[fileIdx]).toBe("399-hayden-panettiere.mp4");
    expect(hayden?.[copyIdx]).toContain("#HaydenPanettiere");
    expect(hayden?.[copyIdx]).not.toMatch(/\r|\n/);

    const btk = body.find((r) => r[numIdx] === "400");
    expect(btk?.[fileIdx]).toBe("400-btk.mp4");
    expect(btk?.[copyIdx]).toContain("#BTK");
    expect(btk?.[copyIdx]).toContain("Follow @FactsOrWhacks");
    expect(btk?.[copyIdx]).not.toMatch(/\r|\n/);

    const katrina = body.find((r) => r[numIdx] === "401");
    expect(katrina?.[fileIdx]).toBe("401-hurricane-katrina.mp4");
    expect(katrina?.[copyIdx]).toContain("#HurricaneKatrina");
    expect(katrina?.[copyIdx]).toContain("21 years ago today");
    expect(katrina?.[copyIdx]).not.toMatch(/\r|\n/);

    const marshall = body.find((r) => r[numIdx] === "402");
    expect(marshall?.[fileIdx]).toBe("402-thurgood-marshall.mp4");
    expect(marshall?.[copyIdx]).toContain("#ThurgoodMarshall");
    expect(marshall?.[copyIdx]).toContain("59 years ago today");
    expect(marshall?.[copyIdx]).toContain("Follow @FactsOrWhacks");
    expect(marshall?.[copyIdx]).not.toMatch(/\r|\n/);

    const diana = body.find((r) => r[numIdx] === "403");
    expect(diana?.[fileIdx]).toBe("403-princess-diana.mp4");
    expect(diana?.[copyIdx]).toContain("#PrincessDiana");
    expect(diana?.[copyIdx]).toContain("29 years ago tonight");
    expect(diana?.[copyIdx]).toContain("Follow @FactsOrWhacks");
    expect(diana?.[copyIdx]).not.toMatch(/\r|\n/);
  });
});
