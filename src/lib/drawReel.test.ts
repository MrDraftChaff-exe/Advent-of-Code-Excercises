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

  it("keeps the Dolly post caption off the phone frame", () => {
    const dolly = TEMPLATES.find((t) => t.id === "dolly");
    expect(dolly?.postCaption).toMatch(/The blueprint/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, dolly!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Dolly Parton");
    expect(painted).toContain("Jolene");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("The blueprint");
    expect(painted).not.toContain("Whitney");
    expect(painted).not.toMatch(/#DollyParton/);
  });

  it("keeps the Tim Curry post caption off the phone frame", () => {
    const curry = TEMPLATES.find((t) => t.id === "tim-curry");
    expect(curry?.postCaption).toMatch(/villain era/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, curry!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Tim Curry");
    expect(painted).toContain("Rocky Horror");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("villain era");
    expect(painted).not.toContain("Zero repeats");
    expect(painted).not.toMatch(/#TimCurry/);
    expect(painted).not.toMatch(/#RipTimCurry/);
  });

  it("keeps the Peter Cullen post caption off the phone frame", () => {
    const cullen = TEMPLATES.find((t) => t.id === "peter-cullen");
    expect(cullen?.postCaption).toMatch(/quiet hero/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, cullen!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Peter Cullen");
    expect(painted).toContain("Optimus Prime");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("quiet hero");
    expect(painted).not.toContain("thousand living rooms");
    expect(painted).not.toMatch(/#PeterCullen/);
    expect(painted).not.toMatch(/#RipPeterCullen/);
  });

  it("keeps the Hayden Panettiere post caption off the phone frame", () => {
    const hayden = TEMPLATES.find((t) => t.id === "hayden-panettiere");
    expect(hayden?.postCaption).toMatch(/Same fire/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, hayden!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Hayden Panettiere");
    expect(painted).toContain("Claire Bennet");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("Same fire");
    expect(painted).not.toContain("Thirty-six years was not enough");
    expect(painted).not.toMatch(/#HaydenPanettiere/);
    expect(painted).not.toMatch(/#RipHaydenPanettiere/);
  });

  it("keeps the BTK post caption off the phone frame", () => {
    const btk = TEMPLATES.find((t) => t.id === "btk");
    expect(btk?.postCaption).toMatch(/skip in class/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, btk!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("BTK");
    expect(painted).toContain("floppy disk");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("skip in class");
    expect(painted).not.toContain("Also BTK");
    expect(painted).not.toMatch(/#TrueCrimeTok/);
    expect(painted).not.toMatch(/#DennisRader/);
  });

  it("keeps the Katrina post caption off the phone frame", () => {
    const katrina = TEMPLATES.find((t) => t.id === "katrina");
    expect(katrina?.postCaption).toMatch(/21 years ago today/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, katrina!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Hurricane Katrina");
    expect(painted).toContain("80 percent");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("21 years ago today");
    expect(painted).not.toContain("didn’t drown New Orleans");
    expect(painted).not.toMatch(/#HurricaneKatrina/);
    expect(painted).not.toMatch(/#OnThisDay/);
  });

  it("keeps the Thurgood Marshall post caption off the phone frame", () => {
    const marshall = TEMPLATES.find((t) => t.id === "thurgood-marshall");
    expect(marshall?.postCaption).toMatch(/59 years ago today/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, marshall!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Thurgood Marshall");
    expect(painted).toContain("69–11");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("59 years ago today");
    expect(painted).not.toContain("wasn’t allowed");
    expect(painted).not.toMatch(/#ThurgoodMarshall/);
    expect(painted).not.toMatch(/#OnThisDay/);
  });

  it("keeps the Princess Diana post caption off the phone frame", () => {
    const diana = TEMPLATES.find((t) => t.id === "princess-diana");
    expect(diana?.postCaption).toMatch(/29 years ago tonight/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, diana!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Princess Diana");
    expect(painted).toContain("Pitié-Salpêtrière");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("29 years ago tonight");
    expect(painted).not.toContain("most famous woman");
    expect(painted).not.toMatch(/#PrincessDiana/);
    expect(painted).not.toMatch(/#OnThisDay/);
  });

  it("keeps the Tupac post caption off the phone frame", () => {
    const tupac = TEMPLATES.find((t) => t.id === "tupac");
    expect(tupac?.postCaption).toMatch(/hunted this case/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, tupac!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Tupac");
    expect(painted).toContain("Keffe D");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("hunted this case");
    expect(painted).not.toContain("ordered the hit");
    expect(painted).not.toMatch(/#Tupac/);
    expect(painted).not.toMatch(/#KeffeD/);
  });

  it("keeps the Japan surrender post caption off the phone frame", () => {
    const japan = TEMPLATES.find((t) => t.id === "japan-surrender");
    expect(japan?.postCaption).toMatch(/ended in 23 minutes/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, japan!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Japan Surrenders");
    expect(painted).toContain("USS Missouri");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("ended in 23 minutes");
    expect(painted).not.toContain("guns went silent");
    expect(painted).not.toMatch(/#USSMissouri/);
    expect(painted).not.toMatch(/#VJDay/);
  });

  it("keeps the Gloria Steinem post caption off the phone frame", () => {
    const gloria = TEMPLATES.find((t) => t.id === "gloria-steinem");
    expect(gloria?.postCaption).toMatch(/Playboy Bunny/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, gloria!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Gloria Steinem");
    expect(painted).toContain("Ms.");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("feminism on newsstands");
    expect(painted).not.toMatch(/#GloriaSteinem/);
    expect(painted).not.toMatch(/#MsMagazine/);
  });

  it("keeps the Squeaky Fromme post caption off the phone frame", () => {
    const fromme = TEMPLATES.find((t) => t.id === "squeaky-fromme");
    expect(fromme?.postCaption).toMatch(/Manson girl/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, fromme!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Squeaky Fromme");
    expect(painted).toContain("Colt");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("Manson girl");
    expect(painted).not.toContain("Two feet away");
    expect(painted).not.toMatch(/#SqueakyFromme/);
    expect(painted).not.toMatch(/#CharlesManson/);
  });

  it("keeps the Magellan post caption off the phone frame", () => {
    const magellan = TEMPLATES.find((t) => t.id === "magellan");
    expect(magellan?.postCaption).toMatch(/Eighteen walked off/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, magellan!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Magellan");
    expect(painted).toContain("Victoria");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("Eighteen walked off");
    expect(painted).not.toContain("Five ships");
    expect(painted).not.toMatch(/#Magellan/);
    expect(painted).not.toMatch(/#Elcano/);
  });

  it("keeps the Star Trek post caption off the phone frame", () => {
    const trek = TEMPLATES.find((t) => t.id === "star-trek");
    expect(trek?.postCaption).toMatch(/three-season flop/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, trek!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Star Trek");
    expect(painted).toContain("Enterprise");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("three-season flop");
    expect(painted).not.toContain("took over the planet");
    expect(painted).not.toMatch(/#StarTrek/);
    expect(painted).not.toMatch(/#LiveLongAndProsper/);
  });

  it("keeps the Elvis post caption off the phone frame", () => {
    const elvis = TEMPLATES.find((t) => t.id === "elvis");
    expect(elvis?.postCaption).toMatch(/never book him/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, elvis!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Elvis");
    expect(painted).toContain("Sixty million");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("never book him");
    expect(painted).not.toContain("watched anyway");
    expect(painted).not.toMatch(/#Elvis/);
    expect(painted).not.toMatch(/#EdSullivan/);
  });

  it("keeps the LHC post caption off the phone frame", () => {
    const lhc = TEMPLATES.find((t) => t.id === "lhc");
    expect(lhc?.postCaption).toMatch(/17-mile racetrack/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, lhc!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("LHC");
    expect(painted).toContain("Higgs");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("first beam made the lap");
    expect(painted).not.toMatch(/#LHC/);
    expect(painted).not.toMatch(/#ParticlePhysics/);
  });

  it("keeps the 9/11 post caption off the phone frame", () => {
    const nineEleven = TEMPLATES.find((t) => t.id === "september-11");
    expect(nineEleven?.postCaption).toMatch(/seventh silence/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, nineEleven!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("9/11");
    expect(painted).toContain("2,977");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("Three cities");
    expect(painted).not.toContain("One Tuesday");
    expect(painted).not.toMatch(/#September11/);
    expect(painted).not.toMatch(/#GroundZero/);
  });

  it("keeps the Star-Spangled Banner post caption off the phone frame", () => {
    const banner = TEMPLATES.find((t) => t.id === "star-spangled-banner");
    expect(banner?.postCaption).toMatch(/shelled the fort/);
    const { ctx, texts } = stubContext();
    drawFrame(ctx, banner!, 4, null);
    const painted = texts.join("");
    expect(painted).toContain("Fort McHenry");
    expect(painted).toContain("Congreve");
    expect(painted).toContain("@FactsOrWhacks");
    expect(painted).not.toContain("shelled the fort");
    expect(painted).not.toContain("At dawn the flag was still there");
    expect(painted).not.toMatch(/#StarSpangledBanner/);
    expect(painted).not.toMatch(/#FortMcHenry/);
  });

  it("paints only the current collage beat facts in beat mode", () => {
    const elvis = TEMPLATES.find((t) => t.id === "elvis");
    const { ctx, texts } = stubContext();
    drawFrame(ctx, elvis!, 5, null, {
      mode: "beat",
      slide: {
        facts: ["Ed Sullivan said he would never book Elvis", "Then he paid $50,000 for three Sunday nights"],
        imageCaption: "Elvis Presley, June 1958",
        imageCredit: "Photo: Modern Screen, 1958 · Public domain",
      },
    });
    const painted = texts.join(" ");
    expect(painted).toContain("never book Elvis");
    expect(painted).toContain("$50,000");
    expect(painted).not.toContain("Sixty million");
    expect(painted).not.toContain("Hound Dog");
    expect(painted).not.toContain("watched anyway");
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
