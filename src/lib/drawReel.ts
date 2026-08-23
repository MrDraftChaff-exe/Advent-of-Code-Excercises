import {
  formatYear,
  parseHighlighted,
  wrapPlain,
  wrapTokens,
} from "./text";
import { coverSourceRect } from "./cover";
import { loadReelImage } from "./images";
import { drawNebula } from "./nebula";
import { THEMES } from "../templates";
import type { ReelContent, Word } from "../types";
import { CANVAS_H, CANVAS_W } from "../types";

function clamp(n: number, a: number, b: number) {
  return Math.max(a, Math.min(b, n));
}

function easeOut(t: number) {
  return 1 - Math.pow(1 - clamp(t, 0, 1), 3);
}

function opacityFor(
  time: number,
  slot: number,
  reveal: ReelContent["reveal"],
) {
  if (reveal === "hold") return 1;
  const start = 0.18 + slot * 0.38;
  return easeOut((time - start) / 0.4);
}

function measureFactory(ctx: CanvasRenderingContext2D, font: string) {
  return (text: string) => {
    ctx.font = font;
    return ctx.measureText(text).width;
  };
}

/** On-canvas title only. Episode numbers stay off the video. */
export function canvasHeadlineText(reel: ReelContent): string {
  return reel.title.trim();
}

export function canvasHeadlineTokens(reel: ReelContent): Word[] {
  const tokens = parseHighlighted(canvasHeadlineText(reel));
  return tokens.length ? tokens : [{ text: " ", highlight: false }];
}

function drawCoverImage(
  ctx: CanvasRenderingContext2D,
  image: HTMLImageElement,
  x: number,
  y: number,
  w: number,
  h: number,
) {
  const iw = image.naturalWidth || image.width;
  const ih = image.naturalHeight || image.height;
  const src = coverSourceRect(iw, ih, w, h, 0.28);
  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, w, h);
  ctx.clip();
  ctx.drawImage(image, src.sx, src.sy, src.sw, src.sh, x, y, w, h);
  ctx.restore();
}

function drawPhotoPlaceholder(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  label: string,
) {
  ctx.save();
  ctx.fillStyle = "rgba(8, 4, 14, 0.72)";
  ctx.fillRect(x, y, w, h);
  ctx.fillStyle = "rgba(247, 242, 248, 0.55)";
  ctx.font = "600 28px Montserrat, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(label || "Photo", x + w / 2, y + h / 2);
  ctx.restore();
}

function drawPhotoPanel(
  ctx: CanvasRenderingContext2D,
  reel: ReelContent,
  image: HTMLImageElement | null,
  x: number,
  y: number,
  w: number,
  h: number,
  accent: string,
  text: string,
  mute: string,
) {
  if (image && (image.naturalWidth || image.width)) {
    drawCoverImage(ctx, image, x, y, w, h);
  } else {
    drawPhotoPlaceholder(ctx, x, y, w, h, reel.imageCaption || "Photo");
  }

  const fade = ctx.createLinearGradient(x, y + h * 0.52, x, y + h);
  fade.addColorStop(0, "rgba(6, 2, 12, 0)");
  fade.addColorStop(0.45, "rgba(6, 2, 12, 0.18)");
  fade.addColorStop(1, "rgba(6, 2, 12, 0.88)");
  ctx.fillStyle = fade;
  ctx.fillRect(x, y, w, h);

  ctx.fillStyle = accent;
  ctx.fillRect(x + w - 7, y, 7, h);

  const pad = 28;
  const maxW = w - pad * 2;
  const caption = reel.imageCaption.trim();
  const credit = reel.imageCredit.trim();
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  const captionLines = caption
    ? wrapPlain(caption, maxW, measureFactory(ctx, "700 26px Montserrat, sans-serif"))
    : [];
  const creditLines = credit
    ? wrapPlain(credit, maxW, measureFactory(ctx, "500 16px Montserrat, sans-serif"))
    : [];
  const captionH = captionLines.length * 32;
  const creditH = creditLines.length * 22;
  let ty = y + h - pad - captionH - (creditH ? creditH + 6 : 0);
  ctx.fillStyle = text;
  ctx.font = "700 26px Montserrat, sans-serif";
  for (const line of captionLines) {
    ctx.fillText(line, x + pad, ty);
    ty += 32;
  }
  ctx.fillStyle = mute;
  ctx.font = "500 16px Montserrat, sans-serif";
  if (captionLines.length) ty += 6;
  for (const line of creditLines) {
    ctx.fillText(line, x + pad, ty);
    ty += 22;
  }
}

export function drawFrame(
  ctx: CanvasRenderingContext2D,
  reel: ReelContent,
  time: number,
  image: HTMLImageElement | null = null,
) {
  const w = CANVAS_W;
  const h = CANVAS_H;
  const theme = THEMES[reel.theme];
  drawNebula(ctx, w, h, time, theme);

  const photoW = Math.round(w * 0.48);
  const copyX = photoW + 40;
  const copyW = w - copyX - 36;
  const copyTop = 28;
  const copyBottom = h - 28;
  const handleH = 36;
  const bullets = reel.bullets.filter((b) => b.trim());
  const yearLabel = formatYear(reel.year);
  const hashtags = reel.hashtags.trim();

  ctx.save();
  ctx.shadowColor = "rgba(0, 0, 0, 0.45)";
  ctx.shadowBlur = 28;
  ctx.shadowOffsetX = 10;
  ctx.globalAlpha = opacityFor(time, 1, reel.reveal);
  drawPhotoPanel(
    ctx,
    reel,
    image,
    0,
    0,
    photoW,
    h,
    theme.accent,
    theme.text,
    theme.mute,
  );
  ctx.restore();

  const titleSize = 54;
  const yearSize = 30;
  const bodySize = 26;
  const tagSize = 22;
  const titleLh = 64;
  const yearLh = 40;
  const bodyLh = 34;
  const tagLh = 30;
  const minBulletGap = 8;
  let scale = 1;

  const measureLayout = (s: number) => {
    const ts = titleSize * s;
    const ys = yearSize * s;
    const bs = bodySize * s;
    const gs = tagSize * s;
    const tLh = titleLh * s;
    const yLh = yearLh * s;
    const bLh = bodyLh * s;
    const gLh = tagLh * s;
    const titleLines = wrapTokens(
      canvasHeadlineTokens(reel),
      copyW,
      measureFactory(ctx, `800 ${ts}px Montserrat, sans-serif`),
    );
    const bulletBlocks = bullets.map((bullet) =>
      wrapPlain(
        bullet.trim(),
        copyW - 36 * s,
        measureFactory(ctx, `500 ${bs}px Montserrat, sans-serif`),
      ),
    );
    const tagLines = hashtags
      ? wrapPlain(
          hashtags,
          copyW,
          measureFactory(ctx, `600 ${gs}px Montserrat, sans-serif`),
        )
      : [];
    const titleH = titleLines.length * tLh;
    const yearH = yearLabel ? yLh : 0;
    const bulletsH = bulletBlocks.reduce(
      (sum, lines) => sum + lines.length * bLh,
      0,
    );
    const tagsH = tagLines.length * gLh;
    const headerGap = 10 * s;
    const ruleGap = 14 * s;
    const tagsGap = tagLines.length ? 16 * s : 0;
    const minGaps = Math.max(0, bulletBlocks.length - 1) * minBulletGap * s;
    const used =
      titleH +
      yearH +
      headerGap +
      ruleGap +
      bulletsH +
      minGaps +
      tagsGap +
      tagsH +
      handleH;
    return {
      titleLines,
      bulletBlocks,
      tagLines,
      yearH,
      tagsH,
      headerGap,
      ruleGap,
      tagsGap,
      used,
      ts,
      ys,
      bs,
      gs,
      tLh,
      yLh,
      bLh,
      gLh,
      s,
    };
  };

  const available = copyBottom - copyTop;
  let layout = measureLayout(1);
  while (layout.used > available && scale > 0.68) {
    scale *= 0.94;
    layout = measureLayout(scale);
  }

  const leftover = Math.max(0, available - layout.used);
  const spread =
    layout.bulletBlocks.length > 1
      ? Math.min(22 * layout.s, leftover / layout.bulletBlocks.length)
      : 0;
  const bulletGap = minBulletGap * layout.s + spread;

  ctx.textBaseline = "top";
  ctx.textAlign = "left";

  let y = copyTop;
  ctx.globalAlpha = opacityFor(time, 0, reel.reveal);
  for (const line of layout.titleLines) {
    let x = copyX;
    for (const tok of line) {
      ctx.fillStyle = tok.highlight ? theme.accent : theme.text;
      ctx.font = `800 ${layout.ts}px Montserrat, sans-serif`;
      ctx.fillText(tok.text, x, y);
      x += ctx.measureText(tok.text).width;
    }
    y += layout.tLh;
  }

  if (yearLabel) {
    ctx.fillStyle = theme.accent;
    ctx.font = `600 ${layout.ys}px Montserrat, sans-serif`;
    ctx.fillText(yearLabel, copyX, y);
    y += layout.yLh;
  }

  y += layout.headerGap;
  ctx.strokeStyle = "rgba(247, 242, 248, 0.16)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(copyX, y);
  ctx.lineTo(copyX + Math.min(copyW, 280), y);
  ctx.stroke();
  y += layout.ruleGap;

  let slot = 2;
  layout.bulletBlocks.forEach((lines, i) => {
    ctx.globalAlpha = opacityFor(time, slot++, reel.reveal);
    const markX = copyX + 6 * layout.s;
    const markY = y + layout.bs * 0.42;
    ctx.fillStyle = theme.accent;
    ctx.beginPath();
    ctx.arc(markX, markY, 5.5 * layout.s, 0, Math.PI * 2);
    ctx.fill();
    for (const line of lines) {
      ctx.fillStyle = theme.text;
      ctx.font = `500 ${layout.bs}px Montserrat, sans-serif`;
      ctx.fillText(line, copyX + 28 * layout.s, y);
      y += layout.bLh;
    }
    if (i < layout.bulletBlocks.length - 1) y += bulletGap;
  });

  const tagsH = layout.tagLines.length ? layout.tagLines.length * layout.gLh : 0;
  if (layout.tagLines.length) {
    ctx.globalAlpha = opacityFor(time, slot++, reel.reveal);
    ctx.fillStyle = theme.accent;
    ctx.font = `600 ${layout.gs}px Montserrat, sans-serif`;
    let ty = copyBottom - handleH - tagsH;
    for (const line of layout.tagLines) {
      ctx.fillText(line, copyX, ty);
      ty += layout.gLh;
    }
  }

  ctx.globalAlpha = 0.9;
  ctx.fillStyle = theme.mute;
  ctx.font = "600 22px Montserrat, sans-serif";
  ctx.fillText(reel.handle, copyX, copyBottom - 22);
  ctx.globalAlpha = 1;
}

export async function snapshotPng(
  reel: ReelContent,
  time = 4,
): Promise<Blob> {
  const canvas = document.createElement("canvas");
  canvas.width = CANVAS_W;
  canvas.height = CANVAS_H;
  const ctx = canvas.getContext("2d");
  if (!ctx) return Promise.reject(new Error("No 2D context"));
  const photo = await loadReelImage(reel.imageUrl);
  drawFrame(ctx, reel, time, photo);
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error("PNG export failed"))),
      "image/png",
    );
  });
}
