export type Word = {
  text: string;
  highlight: boolean;
};

export type ThemeId = "cosmic" | "ocean" | "ember";

export type RevealMode = "hold" | "cascade";

export type ReelContent = {
  id: string;
  name: string;
  episode: string;
  title: string;
  year: string;
  imageUrl: string;
  imageCaption: string;
  imageCredit: string;
  bullets: string[];
  hashtags: string;
  /** Full caption to paste under the Reel. Stays off the image. */
  postCaption?: string;
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

/** 9:16 phone canvas used for both preview and export. */
export const CANVAS_W = 1080;
export const CANVAS_H = 1920;
