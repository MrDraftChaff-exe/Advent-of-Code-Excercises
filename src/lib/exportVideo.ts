import { CANVAS_H, CANVAS_W, type ReelContent } from "../types";
import { ambientSeed, createAmbient } from "./audio";
import {
  beatAtTime,
  kenBurnsAt,
  usesCollage,
} from "./collage";
import { drawFrame } from "./drawReel";
import { loadReelImage } from "./images";

function pickMime(): string {
  const types = [
    "video/webm;codecs=vp9,opus",
    "video/webm;codecs=vp8,opus",
    "video/webm;codecs=vp9",
    "video/webm",
  ];
  for (const t of types) {
    if (
      typeof MediaRecorder !== "undefined" &&
      MediaRecorder.isTypeSupported(t)
    ) {
      return t;
    }
  }
  return "video/webm";
}

export async function exportReelVideo(
  reel: ReelContent,
  onProgress?: (ratio: number) => void,
): Promise<Blob> {
  const canvas = document.createElement("canvas");
  canvas.width = CANVAS_W;
  canvas.height = CANVAS_H;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("No 2D context");

  const collage = usesCollage(reel);
  const urls = Array.from(
    new Set(
      [reel.imageUrl, ...(reel.images ?? []).map((s) => s.imageUrl)].filter(
        Boolean,
      ),
    ),
  );
  const photos = new Map<string, HTMLImageElement | null>();
  await Promise.all(
    urls.map(async (url) => {
      photos.set(url, await loadReelImage(url));
    }),
  );
  const hero = photos.get(reel.imageUrl) ?? null;
  const fps = 30;
  const duration = reel.durationSec;
  const videoStream = canvas.captureStream(fps);
  const ambient = createAmbient(false, ambientSeed(reel));
  const mixed = new MediaStream([
    ...videoStream.getVideoTracks(),
    ...ambient.stream.getAudioTracks(),
  ]);

  const mime = pickMime();
  const recorder = new MediaRecorder(mixed, {
    mimeType: mime,
    videoBitsPerSecond: 10_000_000,
  });
  const chunks: Blob[] = [];
  recorder.ondataavailable = (e) => {
    if (e.data.size) chunks.push(e.data);
  };

  const stopped = new Promise<Blob>((resolve, reject) => {
    recorder.onstop = () =>
      resolve(new Blob(chunks, { type: mime.split(";")[0] }));
    recorder.onerror = () => reject(new Error("Recording failed"));
  });

  recorder.start(100);
  const start = performance.now();

  await new Promise<void>((resolve) => {
    const tick = () => {
      const elapsed = (performance.now() - start) / 1000;
      const t = Math.min(elapsed, duration);
      if (collage) {
        const beat = beatAtTime(reel, t);
        const img = photos.get(beat.imageUrl) ?? hero;
        drawFrame(ctx, reel, t, img, {
          mode: "beat",
          kenBurns: kenBurnsAt(beat, t),
          slide: {
            facts: beat.facts,
            imageCaption: beat.imageCaption,
            imageCredit: beat.imageCredit,
          },
        });
      } else {
        drawFrame(ctx, reel, t, hero);
      }
      onProgress?.(Math.min(1, elapsed / duration));
      if (elapsed >= duration + 0.15) {
        if (recorder.state !== "inactive") recorder.stop();
        ambient.stop();
        resolve();
        return;
      }
      requestAnimationFrame(tick);
    };
    tick();
  });

  return stopped;
}
