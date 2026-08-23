import { describe, expect, it } from "vitest";
import {
  canvasHeadlineText,
  canvasHeadlineTokens,
  drawFrame,
} from "./drawReel";
import { TEMPLATES } from "../templates";
import { CANVAS_H, CANVAS_W } from "../types";

function stubContext() {
  const texts: string[] = [];
  const fonts: string[] = [];
  const gradient = { addColorStop() {} };
  const ctx: Record<string, unknown> = {
    canvas: { width: CANVAS_W, height: CANVAS_H },
    fillStyle: "",
    strokeStyle: "",
    font: "16px sans-serif",
    textAlign: "left",
    textBaseline: "top",
    globalAlpha: 1,
    globalCompositeOperation: "source-over",
    lineJoin: "round",
    miterLimit: 2,
    lineWidth: 1,
    shadowColor: "",
    shadowBlur: 0,
    shadowOffsetY: 0,
    fillRect() {},
    stroke() {},
    strokeText() {},
    beginPath() {},
    moveTo() {},
    lineTo() {},
    quadraticCurveTo() {},
    closePath() {},
    arc() {},
    fill() {},
    save() {},
    restore() {},
    drawImage() {},
    createLinearGradient() {
      return gradient;
    },
    createRadialGradient() {
      return gradient;
    },
    measureText(text: string) {
      const size = Number.parseFloat(
        String(ctx.font).match(/(\d+(?:\.\d+)?)px/)?.[1] ?? "16",
      );
      return { width: text.length * size * 0.55 };
    },
    fillText(text: string) {
      texts.push(text);
      fonts.push(String(ctx.font));
    },
  };
  return { ctx: ctx as unknown as CanvasRenderingContext2D, texts, fonts };
}

describe("canvas layout rules", () => {
  it("exports 9:16 phone frames", () => {
    expect(CANVAS_W).toBe(1080);
    expect(CANVAS_H).toBe(1920);
    expect(CANVAS_H / CANVAS_W).toBeCloseTo(16 / 9);
  });

  it("never paints hashtags onto the phone frame", () => {
    const reel = TEMPLATES[0];
    expect(reel.hashtags).toContain("#");
    expect(canvasHeadlineText(reel)).not.toContain("#");

    const { ctx, texts } = stubContext();
    drawFrame(ctx, reel, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("The End of Apartheid");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).toContain("Nobel");
    expect(painted).not.toMatch(/#\w/);
    for (const tag of reel.hashtags.split(/\s+/).filter(Boolean)) {
      expect(painted).not.toContain(tag);
    }
  });

  it("sizes fact type large enough to fill the phone frame", () => {
    const { ctx, fonts } = stubContext();
    drawFrame(ctx, TEMPLATES[0], 4, null);
    const bodySizes = fonts
      .filter((font) => font.includes("700"))
      .map((font) => Number.parseFloat(font.match(/(\d+(?:\.\d+)?)px/)?.[1] ?? "0"));
    expect(Math.max(0, ...bodySizes)).toBeGreaterThanOrEqual(36);
  });

  it("omits the episode number from the on-canvas title", () => {
    const reel = TEMPLATES[0];
    expect(reel.episode).toBe("30");
    expect(canvasHeadlineText(reel)).toBe("The End of Apartheid");
    const joined = canvasHeadlineTokens(reel)
      .map((t) => t.text)
      .join("");
    expect(joined).not.toMatch(/^\s*30\./);
    expect(joined).not.toContain("30.");
  });
});
