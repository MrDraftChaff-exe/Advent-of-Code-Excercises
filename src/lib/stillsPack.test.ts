import { describe, expect, it, vi } from "vitest";
import {
  fetchZip,
  isZipBlob,
  padEpisode,
  stillPackFilename,
  stillPackRanges,
  stillPackUrl,
  videoPackFilename,
} from "./stillsPack";

describe("stills packs", () => {
  it("splits 395 episodes into 50-episode zip ranges", () => {
    const ranges = stillPackRanges(395, 50);
    expect(ranges).toHaveLength(8);
    expect(ranges[0]).toEqual({ from: 1, to: 50 });
    expect(ranges[7]).toEqual({ from: 351, to: 395 });
    expect(stillPackFilename(1, 50)).toBe(
      "facts-or-whacks-stills-001-050.zip",
    );
    expect(stillPackUrl(351, 395)).toBe(
      "/catalog/facts-or-whacks-stills-351-395.zip",
    );
    expect(videoPackFilename(1, 50)).toBe(
      "facts-or-whacks-videos-001-050.zip",
    );
    expect(padEpisode(7)).toBe("007");
  });

  it("accepts zip magic bytes and rejects HTML 404 pages", async () => {
    expect(
      await isZipBlob(new Blob([new Uint8Array([0x50, 0x4b, 0x03, 0x04])])),
    ).toBe(true);
    expect(await isZipBlob(new Blob(["<!doctype html>"]))).toBe(false);
    expect(await isZipBlob(new Blob([]))).toBe(false);
  });

  it("returns null when the catalog zip is missing", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      body: null,
      blob: async () => new Blob(["not found"]),
    });
    vi.stubGlobal("fetch", fetchMock);
    await expect(fetchZip("/catalog/missing.zip")).resolves.toBeNull();
    vi.unstubAllGlobals();
  });

  it("returns a blob when the response is a real zip", async () => {
    const zip = new Blob([new Uint8Array([0x50, 0x4b, 0x03, 0x04, 0, 0])]);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        headers: new Headers({ "content-length": String(zip.size) }),
        body: null,
        blob: async () => zip,
      }),
    );
    const got = await fetchZip("/catalog/facts-or-whacks-395-stills.zip");
    expect(got?.size).toBe(zip.size);
    vi.unstubAllGlobals();
  });
});
