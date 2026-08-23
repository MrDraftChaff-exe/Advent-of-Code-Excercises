export type Word = {
  text: string;
  highlight: boolean;
};

export type Fact = {
  label: string;
  text: string;
};

export type ThemeId = "cosmic" | "ocean" | "ember";

export type RevealMode = "hold" | "cascade";

export type ReelContent = {
  id: string;
  name: string;
  title: string;
  facts: Fact[];
  note: string;
  cta: string;
  handle: string;
  durationSec: number;
  theme: ThemeId;
  reveal: RevealMode;
};

export type Theme = {
  id: ThemeId;
  name: string;
  bg: string;
  blobs: Array<{ color: string; x: number; y: number; r: number }>;
  accent: string;
  text: string;
  mute: string;
  star: string;
};

export const CANVAS_W = 1080;
export const CANVAS_H = 1920;
