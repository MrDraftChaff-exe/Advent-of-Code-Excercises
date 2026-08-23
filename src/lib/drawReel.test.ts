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
    lineWidth: 1,
    shadowColor: "",
    shadowBlur: 0,
    shadowOffsetY: 0,
    fillRect() {},
    stroke() {},
    beginPath() {},
    moveTo() {},
    lineTo() {},
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
    },
  };
  return { ctx: ctx as unknown as CanvasRenderingContext2D, texts };
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
    expect(painted).not.toMatch(/#\w/);
    for (const tag of reel.hashtags.split(/\s+/).filter(Boolean)) {
      expect(painted).not.toContain(tag);
    }
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
