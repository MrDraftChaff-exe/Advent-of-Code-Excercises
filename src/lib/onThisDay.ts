/** Muse series rules for the daily "on this day" reel. */

export const SERIES_CLOSER = "Fact or whack?";

export const PINNED_COMMENT = "Guess fact or whack before you watch.";

export const POST_WINDOW = "7–9pm ET";

/** Same first line every day. The fact is on screen in the first frame. */
export function seriesIntro(year: string, fact: string): string {
  const clean = fact.trim().replace(/[.?!]+$/g, "");
  return `On this day in ${year.trim()}, ${clean}`;
}

/**
 * #historytok #historyfacts plus one topic tag.
 * #fyp stays off. Other *tok tags stay off.
 */
export function seriesHashtags(topic: string): string {
  const tag = topic.trim().startsWith("#") ? topic.trim() : `#${topic.trim()}`;
  return `#historytok #historyfacts ${tag}`;
}

/** Plain hook: the fact, then one curiosity gap. Not a riddle. */
export function seriesCaption(
  year: string,
  fact: string,
  gap: string,
  topic: string,
): string {
  return [
    seriesIntro(year, fact) + ".",
    "",
    gap.trim().replace(/[.?!]+$/g, "") + ".",
    "",
    "Follow @FactsOrWhacks. A new one drops every night.",
    "",
    seriesHashtags(topic),
  ].join("\n");
}

/** Lines to record over the pad. Same intro shape, same closer, every day. */
export function seriesSpeak(year: string, fact: string): string {
  return [
    "SAY AT THE START:",
    seriesIntro(year, fact) + ".",
    "",
    "SAY AT THE END:",
    SERIES_CLOSER,
    "",
    "PIN THIS COMMENT:",
    PINNED_COMMENT,
  ].join("\n");
}
