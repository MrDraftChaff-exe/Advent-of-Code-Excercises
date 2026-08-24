/** Prebuilt 395-still zip served from Vite `public/` when present locally. */
export const ALL_STILLS_URL = "/catalog/facts-or-whacks-395-stills.zip";
export const ALL_STILLS_NAME = "facts-or-whacks-395-stills.zip";
export const STILL_PACK_SIZE = 50;

export type StillPackRange = { from: number; to: number };

export function padEpisode(n: number): string {
  return String(n).padStart(3, "0");
}

export function stillPackRanges(
  count = 395,
  size = STILL_PACK_SIZE,
): StillPackRange[] {
  const ranges: StillPackRange[] = [];
  for (let from = 1; from <= count; from += size) {
    ranges.push({ from, to: Math.min(from + size - 1, count) });
  }
  return ranges;
}

export function stillPackFilename(from: number, to: number): string {
  return `facts-or-whacks-stills-${padEpisode(from)}-${padEpisode(to)}.zip`;
}

export function stillPackUrl(from: number, to: number): string {
  return `/catalog/${stillPackFilename(from, to)}`;
}

export async function isZipBlob(blob: Blob): Promise<boolean> {
  if (blob.size < 4) return false;
  const buf = new Uint8Array(await blob.slice(0, 4).arrayBuffer());
  return buf[0] === 0x50 && buf[1] === 0x4b;
}

export async function fetchZip(
  url: string,
  onBytes?: (received: number, total: number) => void,
): Promise<Blob | null> {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) return null;
  const total = Number(res.headers.get("content-length")) || 0;
  if (!res.body || !onBytes) {
    const blob = await res.blob();
    return (await isZipBlob(blob)) ? blob : null;
  }
  const reader = res.body.getReader();
  const chunks: Uint8Array[] = [];
  let received = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    if (value) {
      chunks.push(value);
      received += value.byteLength;
      onBytes(received, total);
    }
  }
  const bytes = new Uint8Array(received);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  const blob = new Blob([bytes], { type: "application/zip" });
  return (await isZipBlob(blob)) ? blob : null;
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
