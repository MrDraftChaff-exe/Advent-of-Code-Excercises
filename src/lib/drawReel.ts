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

function drawReadScrim(ctx: CanvasRenderingContext2D, w: number, h: number) {
  const side = ctx.createLinearGradient(0, 0, w * 0.78, 0);
  side.addColorStop(0, "rgba(6, 2, 12, 0.78)");
  side.addColorStop(0.42, "rgba(6, 2, 12, 0.55)");
  side.addColorStop(0.72, "rgba(6, 2, 12, 0.18)");
  side.addColorStop(1, "rgba(6, 2, 12, 0)");
  ctx.fillStyle = side;
  ctx.fillRect(0, 0, w, h);

  const bottom = ctx.createLinearGradient(0, h * 0.55, 0, h);
  bottom.addColorStop(0, "rgba(6, 2, 12, 0)");
  bottom.addColorStop(1, "rgba(6, 2, 12, 0.72)");
  ctx.fillStyle = bottom;
  ctx.fillRect(0, 0, w, h);
}

function withTextShadow(ctx: CanvasRenderingContext2D, draw: () => void) {
  ctx.save();
  ctx.shadowColor = "rgba(0, 0, 0, 0.85)";
  ctx.shadowBlur = 14;
  ctx.shadowOffsetY = 2;
  draw();
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

  const pad = 56;
  const copyX = pad;
  const copyW = Math.round(w * 0.58);
  const copyTop = 48;
  const copyBottom = h - 40;
  const handleH = 32;
  const bullets = reel.bullets.filter((b) => b.trim());
  const yearLabel = formatYear(reel.year);
  const hashtags = reel.hashtags.trim();
  const caption = reel.imageCaption.trim();
  const credit = reel.imageCredit.trim();

  const titleSize = 58;
  const yearSize = 30;
  const bodySize = 26;
  const tagSize = 22;
  const captionSize = 20;
  const creditSize = 16;
  const titleLh = 68;
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
    const cs = captionSize * s;
    const ds = creditSize * s;
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
        measureFactory(ctx, `600 ${bs}px Montserrat, sans-serif`),
      ),
    );
    const tagLines = hashtags
      ? wrapPlain(
          hashtags,
          copyW,
          measureFactory(ctx, `600 ${gs}px Montserrat, sans-serif`),
        )
      : [];
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
    const bulletsH = bulletBlocks.reduce(
      (sum, lines) => sum + lines.length * bLh,
      0,
    );
    const tagsH = tagLines.length * gLh;
    const captionH = captionLines.length * 26 * s;
    const creditH = creditLines.length * 22 * s;
    const headerGap = 8 * s;
    const ruleGap = 14 * s;
    const tagsGap = tagLines.length ? 14 * s : 0;
    const captionGap = captionLines.length || creditLines.length ? 12 * s : 0;
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
      captionGap +
      captionH +
      creditH +
      handleH;
    return {
      titleLines,
      bulletBlocks,
      tagLines,
      captionLines,
      creditLines,
      tagsH,
      captionH,
      creditH,
      headerGap,
      ruleGap,
      tagsGap,
      captionGap,
      used,
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
      ? Math.min(18 * layout.s, leftover / layout.bulletBlocks.length)
      : 0;
  const bulletGap = minBulletGap * layout.s + spread;

  ctx.textBaseline = "top";
  ctx.textAlign = "left";

  let y = copyTop;
  ctx.globalAlpha = opacityFor(time, 0, reel.reveal);
  withTextShadow(ctx, () => {
    let ty = y;
    for (const line of layout.titleLines) {
      let x = copyX;
      for (const tok of line) {
        ctx.fillStyle = tok.highlight ? theme.accent : theme.text;
        ctx.font = `800 ${layout.ts}px Montserrat, sans-serif`;
        ctx.fillText(tok.text, x, ty);
        x += ctx.measureText(tok.text).width;
      }
      ty += layout.tLh;
    }
    y = ty;
  });

  if (yearLabel) {
    ctx.globalAlpha = opacityFor(time, 0, reel.reveal);
    withTextShadow(ctx, () => {
      ctx.fillStyle = theme.accent;
      ctx.font = `600 ${layout.ys}px Montserrat, sans-serif`;
      ctx.fillText(yearLabel, copyX, y);
    });
    y += layout.yLh;
  }

  y += layout.headerGap;
  ctx.strokeStyle = "rgba(247, 242, 248, 0.35)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(copyX, y);
  ctx.lineTo(copyX + Math.min(copyW, 280), y);
  ctx.stroke();
  y += layout.ruleGap;

  let slot = 1;
  layout.bulletBlocks.forEach((lines, i) => {
    ctx.globalAlpha = opacityFor(time, slot++, reel.reveal);
    withTextShadow(ctx, () => {
      const markX = copyX + 6 * layout.s;
      const markY = y + layout.bs * 0.42;
      ctx.fillStyle = theme.accent;
      ctx.beginPath();
      ctx.arc(markX, markY, 5.5 * layout.s, 0, Math.PI * 2);
      ctx.fill();
      let ly = y;
      for (const line of lines) {
        ctx.fillStyle = theme.text;
        ctx.font = `600 ${layout.bs}px Montserrat, sans-serif`;
        ctx.fillText(line, copyX + 28 * layout.s, ly);
        ly += layout.bLh;
      }
    });
    y += lines.length * layout.bLh;
    if (i < layout.bulletBlocks.length - 1) y += bulletGap;
  });

  const metaH =
    layout.tagsH +
    layout.captionH +
    layout.creditH +
    (layout.tagLines.length ? layout.tagsGap : 0) +
    layout.captionGap +
    handleH;
  let my = copyBottom - metaH;

  if (layout.tagLines.length) {
    ctx.globalAlpha = opacityFor(time, slot++, reel.reveal);
    withTextShadow(ctx, () => {
      ctx.fillStyle = theme.accent;
      ctx.font = `600 ${layout.gs}px Montserrat, sans-serif`;
      let ty = my;
      for (const line of layout.tagLines) {
        ctx.fillText(line, copyX, ty);
        ty += layout.gLh;
      }
    });
    my += layout.tagsH + layout.tagsGap;
  }

  if (layout.captionLines.length) {
    ctx.globalAlpha = 1;
    withTextShadow(ctx, () => {
      ctx.fillStyle = theme.text;
      ctx.font = `600 ${layout.cs}px Montserrat, sans-serif`;
      for (const line of layout.captionLines) {
        ctx.fillText(line, copyX, my);
        my += 26 * layout.s;
      }
    });
  }

  if (layout.creditLines.length) {
    ctx.globalAlpha = 0.92;
    withTextShadow(ctx, () => {
      ctx.fillStyle = theme.mute;
      ctx.font = `500 ${layout.ds}px Montserrat, sans-serif`;
      for (const line of layout.creditLines) {
        ctx.fillText(line, copyX, my);
        my += 22 * layout.s;
      }
    });
  }

  ctx.globalAlpha = 0.92;
  withTextShadow(ctx, () => {
    ctx.fillStyle = theme.mute;
    ctx.font = "600 22px Montserrat, sans-serif";
    ctx.fillText(reel.handle, copyX, copyBottom - 22);
  });
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
