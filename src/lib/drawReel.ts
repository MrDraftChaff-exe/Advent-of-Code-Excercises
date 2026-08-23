import { parseHighlighted, wrapPlain, wrapTokens } from "./text";
import { drawNebula } from "./nebula";
import { THEMES } from "../templates";
import type { Fact, ReelContent, Word } from "../types";
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
  const start = 0.2 + slot * 0.48;
  return easeOut((time - start) / 0.4);
}

function measureFactory(ctx: CanvasRenderingContext2D, font: string) {
  return (text: string) => {
    ctx.font = font;
    return ctx.measureText(text).width;
  };
}

type FactLine = { prefix?: string; text: string };

function layoutFact(
  ctx: CanvasRenderingContext2D,
  index: number,
  fact: Fact,
  maxW: number,
  size: number,
): FactLine[] {
  const prefix = `${index}) ${fact.label} — `;
  const bodyFont = `500 ${size}px Montserrat, sans-serif`;
  const boldFont = `700 ${size}px Montserrat, sans-serif`;
  ctx.font = boldFont;
  const prefixW = ctx.measureText(prefix).width;
  ctx.font = bodyFont;
  const fullW = prefixW + ctx.measureText(fact.text).width;
  if (fullW <= maxW) return [{ prefix, text: fact.text }];

  const words = fact.text.split(/\s+/);
  let first = "";
  let used = 0;
  for (let i = 0; i < words.length; i++) {
    const trial = first ? `${first} ${words[i]}` : words[i];
    ctx.font = bodyFont;
    if (prefixW + ctx.measureText(trial).width > maxW && first) break;
    first = trial;
    used = i + 1;
  }
  const rest = words.slice(used).join(" ");
  const restLines = wrapPlain(rest, maxW, measureFactory(ctx, bodyFont));
  return [{ prefix, text: first }, ...restLines.map((text) => ({ text }))];
}

function layoutTitle(
  ctx: CanvasRenderingContext2D,
  title: string,
  maxW: number,
  size: number,
): Word[][] {
  const font = `800 ${size}px Montserrat, sans-serif`;
  return wrapTokens(parseHighlighted(title), maxW, measureFactory(ctx, font));
}

export function drawFrame(
  ctx: CanvasRenderingContext2D,
  reel: ReelContent,
  time: number,
) {
  const w = CANVAS_W;
  const h = CANVAS_H;
  const theme = THEMES[reel.theme];
  drawNebula(ctx, w, h, time, theme);

  const marginX = 92;
  const maxW = w - marginX * 2;
  const handleY = h - 88;

  const titleSize = 54;
  const bodySize = 34;
  const noteSize = 30;
  const ctaSize = 32;
  const titleLh = 66;
  const bodyLh = 46;
  const blockGap = 36;
  const factGap = 18;
  let scale = 1;

  const measureLayout = (s: number) => {
    const ts = titleSize * s;
    const bs = bodySize * s;
    const ns = noteSize * s;
    const cs = ctaSize * s;
    const tLh = titleLh * s;
    const bLh = bodyLh * s;
    const titleLines = layoutTitle(ctx, reel.title, maxW, ts);
    const facts = reel.facts.map((f, i) => layoutFact(ctx, i + 1, f, maxW, bs));
    const noteLines = reel.note
      ? wrapPlain(
          reel.note,
          maxW,
          measureFactory(ctx, `500 ${ns}px Montserrat, sans-serif`),
        )
      : [];
    const ctaLines = reel.cta
      ? reel.cta.split("\n").flatMap((line) =>
          wrapPlain(
            line,
            maxW,
            measureFactory(ctx, `700 ${cs}px Montserrat, sans-serif`),
          ),
        )
      : [];
    const titleH = titleLines.length * tLh;
    const factsH = facts.reduce((sum, lines) => sum + lines.length * bLh, 0);
    const factGaps = Math.max(0, facts.length - 1) * factGap * s;
    const noteH = noteLines.length * (bLh * 0.95);
    const ctaH = ctaLines.length * (bLh * 0.95);
    const gaps =
      (facts.length ? blockGap * s : 0) +
      (noteLines.length ? blockGap * 0.7 * s : 0) +
      (ctaLines.length ? blockGap * s : 0);
    const height = titleH + factsH + factGaps + noteH + ctaH + gaps;
    return {
      titleLines,
      facts,
      noteLines,
      ctaLines,
      height,
      ts,
      bs,
      ns,
      cs,
      tLh,
      bLh,
      s,
    };
  };

  let layout = measureLayout(1);
  const available = handleY - 160;
  while (layout.height > available && scale > 0.72) {
    scale *= 0.94;
    layout = measureLayout(scale);
  }

  let y = (h - 80 - layout.height) / 2 + 20;
  y = Math.max(130, Math.min(y, handleY - layout.height - 40));

  ctx.textBaseline = "top";
  ctx.textAlign = "left";

  let slot = 0;
  const titleAlpha = opacityFor(time, slot++, reel.reveal);
  ctx.textAlign = "center";
  for (const line of layout.titleLines) {
    const lineWidth = line.reduce((sum, tok) => {
      ctx.font = `800 ${layout.ts}px Montserrat, sans-serif`;
      return sum + ctx.measureText(tok.text).width;
    }, 0);
    let x = (w - lineWidth) / 2;
    ctx.globalAlpha = titleAlpha;
    for (const tok of line) {
      ctx.fillStyle = tok.highlight ? theme.accent : theme.text;
      ctx.font = `800 ${layout.ts}px Montserrat, sans-serif`;
      ctx.fillText(tok.text, x, y);
      x += ctx.measureText(tok.text).width;
    }
    y += layout.tLh;
  }

  y += blockGap * layout.s;
  ctx.textAlign = "left";

  for (const factLines of layout.facts) {
    const a = opacityFor(time, slot++, reel.reveal);
    ctx.globalAlpha = a;
    for (const line of factLines) {
      let x = marginX;
      if (line.prefix) {
        ctx.fillStyle = theme.text;
        ctx.font = `700 ${layout.bs}px Montserrat, sans-serif`;
        ctx.fillText(line.prefix, x, y);
        x += ctx.measureText(line.prefix).width;
      }
      ctx.fillStyle = theme.text;
      ctx.font = `500 ${layout.bs}px Montserrat, sans-serif`;
      ctx.fillText(line.text, x, y);
      y += layout.bLh;
    }
    y += factGap * layout.s;
  }

  if (layout.noteLines.length) {
    y += blockGap * 0.35 * layout.s;
    ctx.globalAlpha = opacityFor(time, slot++, reel.reveal);
    ctx.fillStyle = theme.text;
    ctx.font = `500 ${layout.ns}px Montserrat, sans-serif`;
    for (const line of layout.noteLines) {
      ctx.fillText(line, marginX, y);
      y += layout.bLh * 0.95;
    }
  }

  if (layout.ctaLines.length) {
    y += blockGap * 0.7 * layout.s;
    ctx.globalAlpha = opacityFor(time, slot++, reel.reveal);
    ctx.fillStyle = theme.accent;
    ctx.font = `700 ${layout.cs}px Montserrat, sans-serif`;
    for (const line of layout.ctaLines) {
      ctx.fillText(line, marginX, y);
      y += layout.bLh * 0.95;
    }
  }

  ctx.globalAlpha = 0.9;
  ctx.fillStyle = theme.mute;
  ctx.font = `600 30px Montserrat, sans-serif`;
  ctx.textAlign = "center";
  ctx.fillText(reel.handle, w / 2, handleY);
  ctx.globalAlpha = 1;
}

export function snapshotPng(reel: ReelContent, time = 4): Promise<Blob> {
  const canvas = document.createElement("canvas");
  canvas.width = CANVAS_W;
  canvas.height = CANVAS_H;
  const ctx = canvas.getContext("2d");
  if (!ctx) return Promise.reject(new Error("No 2D context"));
  drawFrame(ctx, reel, time);
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error("PNG export failed"))),
      "image/png",
    );
  });
}
