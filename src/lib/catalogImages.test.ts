import { existsSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { parseCatalogCsv, parseCatalogJson, TARGET_FACT_COUNT } from "./catalog";

const ROOT = fileURLToPath(new URL("../..", import.meta.url));

function sniff(buf: Uint8Array): "jpg" | "png" | "gif" | "webp" | null {
  if (buf.length < 12) return null;
  if (buf[0] === 0xff && buf[1] === 0xd8 && buf[2] === 0xff) return "jpg";
  if (buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4e && buf[3] === 0x47) return "png";
  if (buf[0] === 0x47 && buf[1] === 0x49 && buf[2] === 0x46) return "gif";
  if (
    buf[0] === 0x52 &&
    buf[1] === 0x49 &&
    buf[2] === 0x46 &&
    buf[3] === 0x46 &&
    buf[8] === 0x57 &&
    buf[9] === 0x45 &&
    buf[10] === 0x42 &&
    buf[11] === 0x50
  ) {
    return "webp";
  }
  return null;
}

describe("bundled catalog stills", () => {
  const json = JSON.parse(
    readFileSync(join(ROOT, "public/catalog/episodes.json"), "utf8"),
  );
  const csv = parseCatalogCsv(
    readFileSync(join(ROOT, "public/catalog/facts-or-whacks-395.csv"), "utf8"),
  );
  const episodes = parseCatalogJson(json);

  it("has 395 episodes with local Commons rasters", () => {
    expect(episodes).toHaveLength(395);
    expect(csv).toHaveLength(395);
    expect(episodes.map((ep) => ep.n)).toEqual(
      Array.from({ length: 395 }, (_, i) => i + 1),
    );
    for (const ep of episodes) {
      expect(ep.image.startsWith("/images/catalog/")).toBe(true);
      expect(ep.image.includes("upload.wikimedia.org")).toBe(false);
      expect(ep.credit.length).toBeGreaterThan(3);
      const abs = join(ROOT, "public", ep.image.replace(/^\//, ""));
      expect(existsSync(abs)).toBe(true);
      expect(statSync(abs).size).toBeGreaterThanOrEqual(8000);
      const buf = new Uint8Array(readFileSync(abs).subarray(0, 16));
      expect(sniff(buf)).not.toBeNull();
    }
  });

  it("keeps CSV image_url in lockstep with JSON", () => {
    for (let i = 0; i < 395; i++) {
      expect(csv[i].n).toBe(episodes[i].n);
      expect(csv[i].image).toBe(episodes[i].image);
    }
  });

  it("stores twelve on-screen facts for every episode", () => {
    for (const ep of episodes) {
      expect(ep.bullets, `episode ${ep.n}`).toHaveLength(TARGET_FACT_COUNT);
    }
    for (const ep of csv) {
      expect(ep.bullets, `csv ${ep.n}`).toHaveLength(TARGET_FACT_COUNT);
    }
  });
});
