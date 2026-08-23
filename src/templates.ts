import type { ReelContent, Theme, ThemeId } from "./types";

export const THEMES: Record<ThemeId, Theme> = {
  cosmic: {
    id: "cosmic",
    name: "Cosmic",
    bg: "#13071B",
    blobs: [
      { color: "rgba(118, 28, 96, 0.55)", x: 0.28, y: 0.18, r: 0.62 },
      { color: "rgba(58, 12, 78, 0.62)", x: 0.78, y: 0.12, r: 0.5 },
      { color: "rgba(86, 18, 110, 0.48)", x: 0.55, y: 0.55, r: 0.7 },
      { color: "rgba(42, 8, 64, 0.7)", x: 0.18, y: 0.82, r: 0.58 },
      { color: "rgba(150, 42, 92, 0.32)", x: 0.82, y: 0.78, r: 0.52 },
      { color: "rgba(28, 6, 48, 0.55)", x: 0.5, y: 0.92, r: 0.46 },
    ],
    accent: "#54E86B",
    text: "#F7F2F8",
    mute: "rgba(247, 242, 248, 0.42)",
    star: "rgba(255, 210, 255, 0.55)",
  },
  ocean: {
    id: "ocean",
    name: "Ocean",
    bg: "#04121C",
    blobs: [
      { color: "rgba(12, 70, 92, 0.6)", x: 0.3, y: 0.2, r: 0.6 },
      { color: "rgba(8, 40, 80, 0.55)", x: 0.75, y: 0.35, r: 0.5 },
      { color: "rgba(20, 90, 110, 0.4)", x: 0.5, y: 0.75, r: 0.65 },
      { color: "rgba(6, 30, 50, 0.7)", x: 0.15, y: 0.85, r: 0.5 },
    ],
    accent: "#5EE0C8",
    text: "#F2FBFF",
    mute: "rgba(242, 251, 255, 0.42)",
    star: "rgba(180, 240, 255, 0.5)",
  },
  ember: {
    id: "ember",
    name: "Ember",
    bg: "#16080A",
    blobs: [
      { color: "rgba(120, 36, 24, 0.5)", x: 0.3, y: 0.22, r: 0.58 },
      { color: "rgba(80, 18, 30, 0.55)", x: 0.78, y: 0.18, r: 0.48 },
      { color: "rgba(90, 30, 18, 0.4)", x: 0.55, y: 0.7, r: 0.6 },
      { color: "rgba(40, 10, 12, 0.7)", x: 0.2, y: 0.88, r: 0.5 },
    ],
    accent: "#FFB25A",
    text: "#FFF6EE",
    mute: "rgba(255, 246, 238, 0.42)",
    star: "rgba(255, 210, 160, 0.5)",
  },
};

export const TEMPLATES: ReelContent[] = [
  {
    id: "universe",
    name: "Observable universe",
    title: "THE SIZE **OF** THE\n**OBSERVABLE** UNIVERSE",
    facts: [
      { label: "Age", text: "13.8 billion years since the Big Bang." },
      { label: "Width", text: "93 billion light-years across." },
      { label: "Galaxies", text: "About 2 trillion, each packed with stars." },
      { label: "Stars", text: "More than all the sand on Earth." },
      { label: "Us", text: "One planet, on one arm, of one galaxy." },
    ],
    note: "And that's only the light that has had time to reach us.",
    cta: "REMINDER: 90% of people will scroll.\nBe the 10% who Like and Follow.",
    handle: "@FactNebula",
    durationSec: 15,
    theme: "cosmic",
    reveal: "hold",
  },
  {
    id: "oceans",
    name: "Earth's oceans",
    title: "HOW **DEEP** EARTH'S\n**OCEANS** REALLY GO",
    facts: [
      { label: "Coverage", text: "Water covers ~71% of Earth." },
      { label: "Average", text: "The seafloor sits ~3.7 km down." },
      { label: "Deepest", text: "Mariana Trench: about 11 km." },
      { label: "Mapped", text: "Less than 25% in high detail." },
      { label: "Life", text: "Most of Earth's habitat is ocean." },
    ],
    note: "We have better maps of Mars than of our own seafloor.",
    cta: "REMINDER: 90% of people will scroll.\nBe the 10% who Like and Follow.",
    handle: "@FactNebula",
    durationSec: 15,
    theme: "ocean",
    reveal: "hold",
  },
  {
    id: "internet",
    name: "Internet in a day",
    title: "WHAT THE INTERNET\n**MOVES** IN ONE **DAY**",
    facts: [
      { label: "Email", text: "~361 billion messages sent." },
      { label: "Search", text: "~8.5 billion Google queries." },
      { label: "Video", text: "Hundreds of millions of hours watched." },
      { label: "Photos", text: "Billions of new images uploaded." },
      { label: "Data", text: "More than every book ever printed." },
    ],
    note: "Most of that traffic is machines talking to machines.",
    cta: "REMINDER: 90% of people will scroll.\nBe the 10% who Like and Follow.",
    handle: "@FactNebula",
    durationSec: 15,
    theme: "cosmic",
    reveal: "hold",
  },
  {
    id: "body",
    name: "Human body",
    title: "THE **STRANGE** SCALE\n**OF** A HUMAN BODY",
    facts: [
      { label: "Cells", text: "~30 trillion of yours, plus more microbes." },
      { label: "Heart", text: "Pumps ~7,500 liters of blood a day." },
      { label: "Nerves", text: "Signals fire at up to 120 m/s." },
      { label: "DNA", text: "Uncoiled, it would reach the Sun." },
      { label: "Brain", text: "~86 billion neurons, ~20% of your energy." },
    ],
    note: "You replace most of your body. The story stays.",
    cta: "REMINDER: 90% of people will scroll.\nBe the 10% who Like and Follow.",
    handle: "@FactNebula",
    durationSec: 15,
    theme: "ember",
    reveal: "hold",
  },
];

export function cloneTemplate(template: ReelContent): ReelContent {
  return {
    ...template,
    facts: template.facts.map((f) => ({ ...f })),
  };
}

export function blankReel(): ReelContent {
  return {
    id: "custom",
    name: "Custom",
    title: "YOUR **HEADLINE**\nGOES **HERE**",
    facts: [
      { label: "One", text: "A short, punchy statistic." },
      { label: "Two", text: "A second fact people will reread." },
      { label: "Three", text: "Keep each line to one breath." },
      { label: "Four", text: "Lead with the number." },
      { label: "Five", text: "End on the biggest scale." },
    ],
    note: "One extra kicker line under the list.",
    cta: "REMINDER: 90% of people will scroll.\nBe the 10% who Like and Follow.",
    handle: "@YourHandle",
    durationSec: 15,
    theme: "cosmic",
    reveal: "hold",
  };
}
