import type { Theme } from "../types";

function hash(i: number): number {
  const s = Math.sin(i * 127.1 + 311.7) * 43758.5453;
  return s - Math.floor(s);
}

export function drawNebula(
  ctx: CanvasRenderingContext2D,
  w: number,
  h: number,
  time: number,
  theme: Theme,
) {
  ctx.fillStyle = theme.bg;
  ctx.fillRect(0, 0, w, h);

  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  for (let i = 0; i < theme.blobs.length; i++) {
    const b = theme.blobs[i];
    const driftX = Math.sin(time * 0.11 + i * 1.7) * w * 0.04;
    const driftY = Math.cos(time * 0.09 + i * 1.3) * h * 0.03;
    const pulse = 1 + Math.sin(time * 0.17 + i) * 0.06;
    const cx = b.x * w + driftX;
    const cy = b.y * h + driftY;
    const r = b.r * Math.max(w, h) * pulse;
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
    g.addColorStop(0, b.color);
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();

  // Soft bokeh motes
  for (let i = 0; i < 48; i++) {
    const px = (hash(i) + Math.sin(time * 0.07 + i) * 0.02) * w;
    const py = (hash(i + 90) + Math.cos(time * 0.06 + i * 0.4) * 0.015) * h;
    const pr = 6 + hash(i + 21) * 28;
    const a = 0.035 + hash(i + 7) * 0.07;
    const g = ctx.createRadialGradient(px, py, 0, px, py, pr);
    g.addColorStop(0, theme.star.replace(/[\d.]+\)$/, `${a + 0.08})`));
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(px, py, pr, 0, Math.PI * 2);
    ctx.fill();
  }

  // Tiny stars
  ctx.fillStyle = theme.star;
  for (let i = 0; i < 90; i++) {
    const x = hash(i + 200) * w;
    const y = hash(i + 400) * h;
    const s = 0.6 + hash(i + 3) * 1.6;
    const twinkle = 0.25 + 0.75 * (0.5 + 0.5 * Math.sin(time * (0.6 + hash(i) * 1.4) + i));
    ctx.globalAlpha = 0.15 + twinkle * 0.45 * hash(i + 12);
    ctx.fillRect(x, y, s, s);
  }
  ctx.globalAlpha = 1;

  // Vignette over the copy column; the photo panel covers the left side.
  const vig = ctx.createRadialGradient(
    w * 0.74,
    h * 0.48,
    h * 0.12,
    w * 0.74,
    h * 0.5,
    h * 0.82,
  );
  vig.addColorStop(0, "rgba(0,0,0,0)");
  vig.addColorStop(1, "rgba(0,0,0,0.5)");
  ctx.fillStyle = vig;
  ctx.fillRect(0, 0, w, h);
}
