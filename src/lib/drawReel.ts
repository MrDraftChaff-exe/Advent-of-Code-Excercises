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

function headlineTokens(reel: ReelContent): Word[] {
  const episode = reel.episode.trim();
  const tokens: Word[] = [];
  if (episode) {
    tokens.push({ text: `${episode}.`, highlight: true });
    tokens.push({ text: " ", highlight: false });
  }
  tokens.push(...parseHighlighted(reel.title.trim()));
  return tokens.length ? tokens : [{ text: " ", highlight: false }];
}

function roundRectPath(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  const radius = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  if (typeof ctx.roundRect === "function") {
    ctx.roundRect(x, y, w, h, radius);
    return;
  }
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + w, y, x + w, y + h, radius);
  ctx.arcTo(x + w, y + h, x, y + h, radius);
  ctx.arcTo(x, y + h, x, y, radius);
  ctx.arcTo(x, y, x + w, y, radius);
  ctx.closePath();
}

function drawCoverImage(
  ctx: CanvasRenderingContext2D,
  image: HTMLImageElement,
  x: number,
  y: number,
  w: number,
  h: number,
  radius: number,
) {
  const iw = image.naturalWidth || image.width;
  const ih = image.naturalHeight || image.height;
  const src = coverSourceRect(iw, ih, w, h, 0.28);
  ctx.save();
  roundRectPath(ctx, x, y, w, h, radius);
  ctx.clip();
  ctx.drawImage(image, src.sx, src.sy, src.sw, src.sh, x, y, w, h);
  ctx.restore();
  ctx.save();
  ctx.strokeStyle = "rgba(255, 255, 255, 0.16)";
  ctx.lineWidth = 2;
  roundRectPath(ctx, x, y, w, h, radius);
  ctx.stroke();
  ctx.restore();
}

function drawPhotoPlaceholder(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  radius: number,
  label: string,
) {
  ctx.save();
  roundRectPath(ctx, x, y, w, h, radius);
  ctx.fillStyle = "rgba(8, 4, 14, 0.55)";
  ctx.fill();
  ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.fillStyle = "rgba(247, 242, 248, 0.55)";
  ctx.font = "600 26px Montserrat, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(label || "Photo", x + w / 2, y + h / 2);
  ctx.restore();
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

  const marginX = 88;
  const maxW = w - marginX * 2;
  const handleY = h - 88;
  const showPhoto = Boolean(reel.imageUrl);
  const bullets = reel.bullets.filter((b) => b.trim());
  const yearLabel = formatYear(reel.year);
  const hashtags = reel.hashtags.trim();

  const titleSize = 46;
  const yearSize = 28;
  const bodySize = 28;
  const tagSize = 24;
  const captionSize = 22;
  const creditSize = 16;
  const titleLh = 56;
  const yearLh = 40;
  const bodyLh = 38;
  const tagLh = 34;
  const captionLh = 32;
  const blockGap = 28;
  const bulletGap = 12;
  const photoRadius = 28;
  let scale = 1;
  let photoH = showPhoto ? 400 : 0;

  const measureLayout = (s: number, ph: number) => {
    const ts = titleSize * s;
    const ys = yearSize * s;
    const bs = bodySize * s;
    const gs = tagSize * s;
    const cs = captionSize * s;
    const ds = creditSize * s;
    const tLh = titleLh * s;
    const yLh = yearLh * s;
    const bLh = bodyLh * s;
    const gLh = tagLh * s;
    const cLh = captionLh * s;
    const titleLines = wrapTokens(
      headlineTokens(reel),
      maxW,
      measureFactory(ctx, `800 ${ts}px Montserrat, sans-serif`),
    );
    const bulletBlocks = bullets.map((bullet) =>
      wrapPlain(
        bullet.trim(),
        maxW - 36 * s,
        measureFactory(ctx, `500 ${bs}px Montserrat, sans-serif`),
      ),
    );
    const captionLines = reel.imageCaption.trim()
      ? wrapPlain(
          reel.imageCaption.trim(),
          maxW,
          measureFactory(ctx, `600 ${cs}px Montserrat, sans-serif`),
        )
      : [];
    const creditLines = reel.imageCredit.trim()
      ? wrapPlain(
          reel.imageCredit.trim(),
          maxW,
          measureFactory(ctx, `500 ${ds}px Montserrat, sans-serif`),
        )
      : [];
    const tagLines = hashtags
      ? wrapPlain(
          hashtags,
          maxW,
          measureFactory(ctx, `600 ${gs}px Montserrat, sans-serif`),
        )
      : [];
    const titleH = titleLines.length * tLh;
    const yearH = yearLabel ? yLh : 0;
    const bulletsH = bulletBlocks.reduce(
      (sum, lines) => sum + lines.length * bLh,
      0,
    );
    const bulletGaps = Math.max(0, bulletBlocks.length - 1) * bulletGap * s;
    const captionH = captionLines.length * (cLh * 0.95);
    const creditH = creditLines.length * (cLh * 0.75);
    const tagsH = tagLines.length * gLh;
    const photoBlock = ph
      ? ph + (captionH || creditH ? 14 * s : 0) + captionH + creditH
      : 0;
    const gaps =
      (ph ? blockGap * s : 0) +
      (bulletBlocks.length ? blockGap * s : 0) +
      (tagLines.length ? blockGap * 0.85 * s : 0);
    const height =
      titleH + yearH + photoBlock + bulletsH + bulletGaps + tagsH + gaps;
    return {
      titleLines,
      bulletBlocks,
      captionLines,
      creditLines,
      tagLines,
      height,
      ts,
      ys,
      bs,
      gs,
      cs,
      ds,
      tLh,
      yLh,
      bLh,
      gLh,
      cLh,
      s,
      ph,
    };
  };

  let layout = measureLayout(1, photoH);
  const available = handleY - 150;
  while (layout.height > available && photoH > 220) {
    photoH -= 18;
    layout = measureLayout(scale, photoH);
  }
  while (layout.height > available && scale > 0.7) {
    scale *= 0.94;
    layout = measureLayout(scale, photoH);
  }

  let y = (h - 80 - layout.height) / 2 + 16;
  y = Math.max(118, Math.min(y, handleY - layout.height - 36));

  ctx.textBaseline = "top";
  ctx.textAlign = "left";

  let slot = 0;
  const titleAlpha = opacityFor(time, slot++, reel.reveal);
  ctx.globalAlpha = titleAlpha;
  for (const line of layout.titleLines) {
    let x = marginX;
    for (const tok of line) {
      ctx.fillStyle = tok.highlight ? theme.accent : theme.text;
      ctx.font = `800 ${layout.ts}px Montserrat, sans-serif`;
      ctx.fillText(tok.text, x, y);
      x += ctx.measureText(tok.text).width;
    }
    y += layout.tLh;
  }

  if (yearLabel) {
    ctx.globalAlpha = titleAlpha;
    ctx.fillStyle = theme.accent;
    ctx.font = `600 ${layout.ys}px Montserrat, sans-serif`;
    ctx.fillText(yearLabel, marginX, y);
    y += layout.yLh;
  }

  if (showPhoto) {
    y += blockGap * layout.s * 0.45;
    ctx.globalAlpha = opacityFor(time, slot++, reel.reveal);
    const photoY = y;
    ctx.save();
    ctx.shadowColor = "rgba(0, 0, 0, 0.45)";
    ctx.shadowBlur = 36;
    ctx.shadowOffsetY = 16;
    if (image && (image.naturalWidth || image.width)) {
      drawCoverImage(
        ctx,
        image,
        marginX,
        photoY,
        maxW,
        layout.ph,
        photoRadius,
      );
    } else {
      drawPhotoPlaceholder(
        ctx,
        marginX,
        photoY,
        maxW,
        layout.ph,
        photoRadius,
        reel.imageCaption || "Photo",
      );
    }
    ctx.restore();
    y += layout.ph + 14 * layout.s;
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    if (layout.captionLines.length) {
      ctx.fillStyle = theme.text;
      ctx.font = `600 ${layout.cs}px Montserrat, sans-serif`;
      for (const line of layout.captionLines) {
        ctx.fillText(line, marginX, y);
        y += layout.cLh * 0.95;
      }
    }
    if (layout.creditLines.length) {
      ctx.fillStyle = theme.mute;
      ctx.font = `500 ${layout.ds}px Montserrat, sans-serif`;
      for (const line of layout.creditLines) {
        ctx.fillText(line, marginX, y);
        y += layout.cLh * 0.75;
      }
    }
  }

  y += blockGap * layout.s * 0.7;
  ctx.textAlign = "left";

  for (const lines of layout.bulletBlocks) {
    const a = opacityFor(time, slot++, reel.reveal);
    ctx.globalAlpha = a;
    const markX = marginX + 6 * layout.s;
    const markY = y + layout.bs * 0.42;
    ctx.fillStyle = theme.accent;
    ctx.beginPath();
    ctx.arc(markX, markY, 5.5 * layout.s, 0, Math.PI * 2);
    ctx.fill();
    for (const line of lines) {
      ctx.fillStyle = theme.text;
      ctx.font = `500 ${layout.bs}px Montserrat, sans-serif`;
      ctx.fillText(line, marginX + 36 * layout.s, y);
      y += layout.bLh;
    }
    y += bulletGap * layout.s;
  }

  if (layout.tagLines.length) {
    y += blockGap * 0.35 * layout.s;
    ctx.globalAlpha = opacityFor(time, slot++, reel.reveal);
    ctx.fillStyle = theme.accent;
    ctx.font = `600 ${layout.gs}px Montserrat, sans-serif`;
    for (const line of layout.tagLines) {
      ctx.fillText(line, marginX, y);
      y += layout.gLh;
    }
  }

  ctx.globalAlpha = 0.9;
  ctx.fillStyle = theme.mute;
  ctx.font = `600 30px Montserrat, sans-serif`;
  ctx.textAlign = "center";
  ctx.fillText(reel.handle, w / 2, handleY);
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
