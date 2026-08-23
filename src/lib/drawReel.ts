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
  ctx.drawImage(image, src.sx, src.sy, src.sw, src.sh, x, y, w, h);
}

function drawPhotoPlaceholder(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  label: string,
) {
  ctx.fillStyle = "rgba(8, 4, 14, 0.72)";
  ctx.fillRect(x, y, w, h);
  ctx.fillStyle = "rgba(247, 242, 248, 0.55)";
  ctx.font = "600 28px Montserrat, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(label || "Photo", x + w / 2, y + h / 2);
}

/** Darken the whole photo so white type stays readable on any still. */
function drawReadScrim(ctx: CanvasRenderingContext2D, w: number, h: number) {
  ctx.fillStyle = "rgba(4, 0, 10, 0.46)";
  ctx.fillRect(0, 0, w, h);

  const top = ctx.createLinearGradient(0, 0, 0, h * 0.3);
  top.addColorStop(0, "rgba(4, 0, 10, 0.42)");
  top.addColorStop(1, "rgba(4, 0, 10, 0)");
  ctx.fillStyle = top;
  ctx.fillRect(0, 0, w, h);

  const bottom = ctx.createLinearGradient(0, h * 0.58, 0, h);
  bottom.addColorStop(0, "rgba(4, 0, 10, 0)");
  bottom.addColorStop(1, "rgba(4, 0, 10, 0.58)");
  ctx.fillStyle = bottom;
  ctx.fillRect(0, 0, w, h);
}

function fillRoundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  const radius = Math.max(0, Math.min(r, w / 2, h / 2));
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + w - radius, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
  ctx.lineTo(x + w, y + h - radius);
  ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
  ctx.lineTo(x + radius, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
  ctx.fill();
}

function paintText(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  fill: string,
  strokeWidth: number,
) {
  ctx.save();
  ctx.shadowColor = "rgba(0, 0, 0, 0.85)";
  ctx.shadowBlur = 8;
  ctx.shadowOffsetY = 1;
  ctx.lineJoin = "round";
  ctx.miterLimit = 2;
  ctx.lineWidth = strokeWidth;
  ctx.strokeStyle = "rgba(0, 0, 0, 0.92)";
  ctx.fillStyle = fill;
  ctx.strokeText(text, x, y);
  ctx.fillText(text, x, y);
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

  if (image && (image.naturalWidth || image.width)) {
    drawCoverImage(ctx, image, 0, 0, w, h);
  } else {
    drawPhotoPlaceholder(ctx, 0, 0, w, h, reel.imageCaption || "Photo");
  }
  drawReadScrim(ctx, w, h);

  const pad = 28;
  const copyX = pad;
  const copyW = w - pad * 2;
  const safeTop = 40;
  const safeBottom = 72;
  const copyBottom = h - safeBottom;
  const handleH = 26;
  const bullets = reel.bullets.filter((b) => b.trim());
  const yearLabel = formatYear(reel.year);
  const caption = reel.imageCaption.trim();
  const credit = reel.imageCredit.trim();

  const titleSize = 80;
  const yearSize = 42;
  const bodySize = 50;
  const captionSize = 20;
  const creditSize = 16;
  const titleLh = 86;
  const yearLh = 48;
  const bodyLh = 60;
  const minBulletGap = 8;
  const platePad = 8;
  const minScale = 0.7;
  const maxScale = 2.2;

  const measureLayout = (s: number) => {
    const ts = titleSize * s;
    const ys = yearSize * s;
    const bs = bodySize * s;
    const cs = captionSize * s;
    const ds = creditSize * s;
    const tLh = titleLh * s;
    const yLh = yearLh * s;
    const bLh = bodyLh * s;
    const titleLines = wrapTokens(
      canvasHeadlineTokens(reel),
      copyW,
      measureFactory(ctx, `800 ${ts}px Montserrat, sans-serif`),
    );
    const bulletBlocks = bullets.map((bullet) =>
      wrapPlain(
        bullet.trim(),
        copyW - 52 * s,
        measureFactory(ctx, `700 ${bs}px Montserrat, sans-serif`),
      ),
    );
    const captionLines = caption
      ? wrapPlain(
          caption,
          copyW,
          measureFactory(ctx, `600 ${cs}px Montserrat, sans-serif`),
        )
      : [];
    const creditLines = credit
      ? wrapPlain(
          credit,
          copyW,
          measureFactory(ctx, `500 ${ds}px Montserrat, sans-serif`),
        )
      : [];
    const titleH = titleLines.length * tLh;
    const yearH = yearLabel ? yLh : 0;
    const plateExtra = platePad * 2 * s * bulletBlocks.length;
    const bulletsH = bulletBlocks.reduce(
      (sum, lines) => sum + lines.length * bLh,
      0,
    );
    const captionH = captionLines.length * 28 * s;
    const creditH = creditLines.length * 22 * s;
    const headerGap = 4 * s;
    const ruleGap = 0;
    const captionGap = captionLines.length || creditLines.length ? 8 * s : 0;
    const minGaps = Math.max(0, bulletBlocks.length - 1) * minBulletGap * s;
    const headerH = titleH + yearH + headerGap + ruleGap;
    const footerH = captionGap + captionH + creditH + handleH;
    const used = headerH + bulletsH + plateExtra + minGaps + footerH;
    return {
      titleLines,
      bulletBlocks,
      captionLines,
      creditLines,
      headerH,
      footerH,
      captionH,
      creditH,
      headerGap,
      ruleGap,
      captionGap,
      used,
      ts,
      ys,
      bs,
      cs,
      ds,
      tLh,
      yLh,
      bLh,
      s,
    };
  };

  const available = copyBottom - safeTop;
  let lo = minScale;
  let hi = maxScale;
  let scale = minScale;
  for (let i = 0; i < 16; i++) {
    const mid = (lo + hi) / 2;
    if (measureLayout(mid).used <= available) {
      scale = mid;
      lo = mid;
    } else {
      hi = mid;
    }
  }
  const layout = measureLayout(scale);

  const leftover = Math.max(0, available - layout.used);
  const spread =
    layout.bulletBlocks.length > 1
      ? leftover / layout.bulletBlocks.length
      : leftover;
  const bulletGap = minBulletGap * layout.s + spread;
  const titleStroke = Math.max(5, layout.ts * 0.14);
  const bodyStroke = Math.max(4.5, layout.bs * 0.16);

  ctx.textBaseline = "top";
  ctx.textAlign = "left";

  let y = safeTop;
  ctx.globalAlpha = opacityFor(time, 0, reel.reveal);
  let ty = y;
  for (const line of layout.titleLines) {
    let x = copyX;
    for (const tok of line) {
      ctx.font = `800 ${layout.ts}px Montserrat, sans-serif`;
      paintText(
        ctx,
        tok.text,
        x,
        ty,
        tok.highlight ? theme.accent : theme.text,
        titleStroke,
      );
      x += ctx.measureText(tok.text).width;
    }
    ty += layout.tLh;
  }
  y = ty;

  if (yearLabel) {
    ctx.globalAlpha = opacityFor(time, 0, reel.reveal);
    ctx.font = `600 ${layout.ys}px Montserrat, sans-serif`;
    paintText(ctx, yearLabel, copyX, y, theme.accent, Math.max(3, layout.ys * 0.18));
    y += layout.yLh;
  }

  y += layout.headerGap;

  let slot = 1;
  layout.bulletBlocks.forEach((lines, i) => {
    ctx.globalAlpha = opacityFor(time, slot++, reel.reveal);
    const blockH = lines.length * layout.bLh;
    ctx.fillStyle = "rgba(0, 0, 0, 0.52)";
    fillRoundRect(
      ctx,
      copyX - 10,
      y - 4,
      copyW + 20,
      blockH + platePad * layout.s,
      12 * layout.s,
    );
    const markX = copyX + 14 * layout.s;
    const markY = y + layout.bs * 0.42;
    ctx.fillStyle = theme.accent;
    ctx.beginPath();
    ctx.arc(markX, markY, 7 * layout.s, 0, Math.PI * 2);
    ctx.fill();
    let ly = y;
    for (const line of lines) {
      ctx.font = `700 ${layout.bs}px Montserrat, sans-serif`;
      paintText(ctx, line, copyX + 36 * layout.s, ly, theme.text, bodyStroke);
      ly += layout.bLh;
    }
    y += blockH + platePad * layout.s;
    if (i < layout.bulletBlocks.length - 1) y += bulletGap;
  });

  let my =
    copyBottom -
    layout.captionH -
    layout.creditH -
    layout.captionGap -
    handleH;

  if (layout.captionLines.length) {
    ctx.globalAlpha = 1;
    ctx.font = `600 ${layout.cs}px Montserrat, sans-serif`;
    for (const line of layout.captionLines) {
      paintText(ctx, line, copyX, my, theme.text, 3.5);
      my += 24 * layout.s;
    }
  }

  if (layout.creditLines.length) {
    ctx.globalAlpha = 0.95;
    ctx.font = `500 ${layout.ds}px Montserrat, sans-serif`;
    for (const line of layout.creditLines) {
      paintText(ctx, line, copyX, my, "#F4EEF6", 3);
      my += 20 * layout.s;
    }
  }

  ctx.globalAlpha = 0.95;
  ctx.font = "700 24px Montserrat, sans-serif";
  paintText(ctx, reel.handle, copyX, copyBottom - 24, "#F4EEF6", 3.5);
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
