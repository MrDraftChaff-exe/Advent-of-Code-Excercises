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
    title: "THE SIZE **OF** THE **OBSERVABLE** UNIVERSE",
    facts: [
      {
        label: "Age",
        text: "~13.8 billion years since the Big Bang.",
      },
      {
        label: "Span",
        text: "~93 billion light-years from edge to edge.",
      },
      {
        label: "Galaxies",
        text: "~2 trillion galaxies, each packed with stars.",
      },
      {
        label: "Stars",
        text: "~200 billion trillion suns in the observable cosmos.",
      },
      {
        label: "Us",
        text: "Earth is a pale pixel on one ordinary spiral arm.",
      },
    ],
    note: "And that is only the light that has had time to reach us.",
    cta: "REMINDER: 90% of people will scroll.\nBe the 10% who Like and Follow.",
    handle: "@FactNebula",
    durationSec: 15,
    theme: "cosmic",
    reveal: "hold",
  },
  {
    id: "oceans",
    name: "Earth's oceans",
    title: "HOW **DEEP** EARTH'S **OCEANS** REALLY GO",
    facts: [
      {
        label: "Coverage",
        text: "Water hides ~71% of the planet's surface.",
      },
      {
        label: "Average",
        text: "The typical seafloor sits ~3.7 km down.",
      },
      {
        label: "Challenger",
        text: "The Marianas trench plunges ~10.9 km.",
      },
      {
        label: "Mapped",
        text: "Less than 30% of the seafloor is mapped in high detail.",
      },
      {
        label: "Life",
        text: "Most of Earth's living space is in the dark water column.",
      },
    ],
    note: "We have better maps of Mars than of our own ocean floor.",
    cta: "REMINDER: 90% of people will scroll.\nBe the 10% who Like and Follow.",
    handle: "@FactNebula",
    durationSec: 15,
    theme: "ocean",
    reveal: "hold",
  },
  {
    id: "internet",
    name: "Internet in a day",
    title: "WHAT THE INTERNET **MOVES** IN A **SINGLE** DAY",
    facts: [
      {
        label: "Email",
        text: "~361 billion messages sent worldwide.",
      },
      {
        label: "Search",
        text: "~8.5 billion Google queries typed.",
      },
      {
        label: "Video",
        text: "Hundreds of millions of hours of video watched.",
      },
      {
        label: "Photos",
        text: "Billions of new images uploaded across apps.",
      },
      {
        label: "Traffic",
        text: "Exabytes of data — more than every book ever printed.",
      },
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
    title: "THE **STRANGE** SCALE **OF** A HUMAN BODY",
    facts: [
      {
        label: "Cells",
        text: "~30 trillion human cells, plus even more microbes.",
      },
      {
        label: "Blood",
        text: "Your heart pumps ~7,500 liters every day.",
      },
      {
        label: "Nerves",
        text: "Signals race up to ~120 meters per second.",
      },
      {
        label: "DNA",
        text: "Stretched out, one body's DNA would reach the sun and back.",
      },
      {
        label: "Brain",
        text: "~86 billion neurons, using ~20% of your energy.",
      },
    ],
    note: "You replace most of your body — but keep the same story.",
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
    title: "YOUR **HEADLINE** GOES **HERE**",
    facts: [
      { label: "One", text: "A short, punchy statistic." },
      { label: "Two", text: "Another fact people will read twice." },
      { label: "Three", text: "Keep each line under ~90 characters." },
      { label: "Four", text: "Numbers beat adjectives." },
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
