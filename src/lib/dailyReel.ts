import type { ReelContent } from "../types";
import { TEMPLATES } from "../templates";

/** Calendar-day extras already in the studio. MM-DD in the viewer's local timezone. */
export const DAILY_TEMPLATE_BY_MD: Record<string, string> = {
  "08-16": "hayden-panettiere",
  "08-25": "tim-curry",
  "08-26": "peter-cullen",
  "08-29": "katrina",
  "08-30": "thurgood-marshall",
  "08-31": "princess-diana",
  "09-01": "tupac",
  "09-02": "japan-surrender",
  "09-03": "gloria-steinem",
};

export function monthDay(date: Date = new Date()): string {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${month}-${day}`;
}

export function parseIsoDate(value: string): Date {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());
  if (!match) throw new Error(`expected YYYY-MM-DD, got ${value}`);
  return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
}

export function pickDailyTemplate(
  date: Date = new Date(),
): ReelContent | undefined {
  const id = DAILY_TEMPLATE_BY_MD[monthDay(date)];
  if (!id) return undefined;
  return TEMPLATES.find((template) => template.id === id);
}

export function dailyArtifactStem(id: string): string {
  return id.replace(/-/g, "_");
}
