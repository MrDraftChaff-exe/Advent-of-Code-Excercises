import type { Word } from "../types";

/** Split a title into words. `**this**` paints a word in the accent color. */
export function parseHighlighted(input: string): Word[] {
  const out: Word[] = [];
  const re = /\*\*(.+?)\*\*/gs;
  let last = 0;
  let match: RegExpExecArray | null;
  while ((match = re.exec(input))) {
    pushChunk(out, input.slice(last, match.index), false);
    pushChunk(out, match[1], true);
    last = match.index + match[0].length;
  }
  pushChunk(out, input.slice(last), false);
  return out;
}

function pushChunk(out: Word[], chunk: string, highlight: boolean) {
  if (!chunk) return;
  const parts = chunk.split(/(\n|[ \t]+)/);
  for (const part of parts) {
    if (part) out.push({ text: part, highlight });
  }
}

export function wrapTokens(
  tokens: Word[],
  maxWidth: number,
  measure: (text: string) => number,
): Word[][] {
  const lines: Word[][] = [];
  let current: Word[] = [];
  let width = 0;

  const flush = () => {
    while (current.length && /^\s+$/.test(current[0].text)) current.shift();
    while (
      current.length &&
      /^\s+$/.test(current[current.length - 1].text)
    ) {
      current.pop();
    }
    if (current.length) lines.push(current);
    current = [];
    width = 0;
  };

  for (const token of tokens) {
    if (token.text === "\n") {
      flush();
      continue;
    }
    const w = measure(token.text);
    const isSpace = /^\s+$/.test(token.text);
    if (current.length && width + w > maxWidth && !isSpace) {
      flush();
    }
    if (current.length === 0 && isSpace) continue;
    current.push(token);
    width += w;
  }
  flush();
  return lines.length ? lines : [[]];
}

export function wrapPlain(
  text: string,
  maxWidth: number,
  measure: (text: string) => number,
): string[] {
  const words = text.trim().split(/\s+/);
  if (!words[0]) return [];
  const lines: string[] = [];
  let current = "";
  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (current && measure(next) > maxWidth) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  }
  if (current) lines.push(current);
  return lines;
}

export const DEFAULT_DURATION = 15;

export function clampDuration(n: number): number {
  if (!Number.isFinite(n)) return DEFAULT_DURATION;
  return Math.min(60, Math.max(8, Math.round(n)));
}
