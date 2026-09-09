import type { ReelContent, ReelSlide } from "../types";

/** Posted growth clips are one minute for platform monetization. */
export const VIDEO_DURATION_SEC = 60;
export const BEAT_COUNT = 6;
export const FACTS_PER_BEAT = 2;
export const BEAT_FADE_SEC = 0.6;

export type CollageBeat = ReelSlide & {
  index: number;
  start: number;
  end: number;
  facts: string[];
  zoomIn: boolean;
  focusX: number;
  focusY: number;
};

export function reelSlides(reel: ReelContent): ReelSlide[] {
  if (reel.images?.length) return reel.images;
  if (!reel.imageUrl.trim()) return [];
  return [
    {
      imageUrl: reel.imageUrl,
      imageCaption: reel.imageCaption,
      imageCredit: reel.imageCredit,
    },
  ];
}

/** Collage beats when the clip is a minute long, or the extra ships several photos. */
export function usesCollage(reel: ReelContent): boolean {
  return (reel.images?.length ?? 0) > 1 || reel.durationSec >= 48;
}

export function collageBeats(reel: ReelContent): CollageBeat[] {
  const duration = Math.max(8, reel.durationSec || VIDEO_DURATION_SEC);
  const facts = reel.bullets.map((b) => b.trim()).filter(Boolean);
  const slides = reelSlides(reel);
  const beatDur = duration / BEAT_COUNT;
  return Array.from({ length: BEAT_COUNT }, (_, index) => {
    const slide =
      slides.length > 0
        ? slides[index % slides.length]
        : {
            imageUrl: "",
            imageCaption: reel.imageCaption,
            imageCredit: reel.imageCredit,
          };
    const start = index * beatDur;
    return {
      index,
      start,
      end: start + beatDur,
      imageUrl: slide.imageUrl,
      imageCaption: slide.imageCaption,
      imageCredit: slide.imageCredit,
      facts: facts.slice(index * FACTS_PER_BEAT, (index + 1) * FACTS_PER_BEAT),
      zoomIn: index % 2 === 0,
      focusX: 0.46 + ((index * 17) % 9) * 0.01,
      focusY: 0.24 + ((index * 13) % 7) * 0.012,
    };
  });
}

export function beatAtTime(reel: ReelContent, time: number): CollageBeat {
  const beats = collageBeats(reel);
  const t = Math.max(0, time);
  return beats.find((beat) => t < beat.end - 1e-6) ?? beats[beats.length - 1];
}

export function kenBurnsAt(
  beat: CollageBeat,
  time: number,
): { scale: number; focusX: number; focusY: number } {
  const span = Math.max(0.001, beat.end - beat.start);
  const u = Math.max(0, Math.min(1, (time - beat.start) / span));
  const scale = beat.zoomIn ? 1 + 0.11 * u : 1.11 - 0.11 * u;
  return {
    scale,
    focusX: beat.focusX,
    focusY: beat.focusY,
  };
}
