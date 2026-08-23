import JSZip from "jszip";
import type { ReelContent } from "../types";
import { snapshotPng } from "./drawReel";
import { exportReelVideo } from "./exportVideo";
import { slugify } from "./fonts";

export async function zipReelExports(
  reels: ReelContent[],
  kind: "webm" | "png",
  onProgress?: (done: number, total: number, name: string) => void,
): Promise<Blob> {
  const zip = new JSZip();
  const total = reels.length;
  for (let i = 0; i < total; i++) {
    const reel = reels[i];
    const base = slugify(`${reel.episode}-${reel.title}`);
    onProgress?.(i, total, reel.name);
    if (kind === "png") {
      zip.file(`${base}.png`, await snapshotPng(reel, Math.max(3, reel.durationSec / 2)));
    } else {
      zip.file(`${base}.webm`, await exportReelVideo(reel));
    }
  }
  onProgress?.(total, total, "zip");
  return zip.generateAsync({ type: "blob" });
}
