# Daily Facts or Whacks reel

One growth post per calendar day for `@FactsOrWhacks`. Same job as asking the cloud agent “new video for today”: pick, build, deliver a 9:16 still + 30s MP4 + paste caption.

This repo does **not** post to TikTok, Reels, or Shorts. Delivery is the download pack. You paste the caption.

## Schedule it in Cursor

1. Open [cursor.com/automations](https://cursor.com/automations).
2. New automation. Trigger: **Scheduled**, every day. Suggested time: **12:00 UTC** (8:00 a.m. Eastern) so the files are waiting when you wake.
3. Repository: this repo. Branch: `cursor/fact-reel-studio-b230` (or `main` after that branch lands).
4. Paste the prompt in the next section. Save and turn it on.

The automation starts a cloud agent. That agent writes the extra episode, exports the still and MP4, and leaves files in `/opt/cursor/artifacts` and on the cloud Desktop. Open that run, download, post.

Do **not** add a second post the same day. One clip per platform per day. Cross-posting the same clip to TikTok, Reels, and Shorts is fine.

## Prompt to paste into the automation

```
Read DAILY_REEL.md and follow it exactly.

Ship today’s @FactsOrWhacks growth reel: one extra studio episode, 9:16 still, 30s MP4 with a unique pad, paste caption. Put the still, mp4, and caption on /opt/cursor/artifacts and /home/ubuntu/Desktop. Commit, push this branch, update the existing draft PR. Do not mention the PR in the user-facing reply. Do not make a screen recording. The user downloads and pastes.

Stay on the current feature branch. Do not replace TEMPLATES[0] (apartheid).
```

## Pick (newsjack > anniversary > catalog)

1. **Newsjack** a still-moving story that HistoryTok will search today (death, verdict, disaster, royal/pop-culture spike). Skip if facts, death tolls, or cause are still moving, or if a licensed photo is messy. Cause of death stays off the still unless it is settled public record and not pending investigation.
2. **On-this-day anniversary** the AP “Today in History” lead, or the date people will actually search. Skip if we posted that subject yesterday.
3. **Catalog** only if 1 and 2 fail. Do not dump the 395 pack. Do not post two similar 12-fact stills in one day.

Already-shipped extras (do not silently replace them):

| n | id | notes |
|---|---|---|
| 396 | `dolly` | Living-legend Jolene post; Dolly died Aug 25, 2026 — do not turn it into a funeral reel |
| 397 | `tim-curry` | Died Aug 25, 2026 |
| 398 | `peter-cullen` | Died Aug 26, 2026 |
| 399 | `hayden-panettiere` | Died Aug 16, 2026; cause/manner pending — keep off the still |
| 400 | `btk` | Floppy-disk metadata |
| 401 | `katrina` | Aug 29 landfall anniversary |
| 402 | `thurgood-marshall` | Senate confirmation Aug 30, 1967 |
| 403 | `princess-diana` | Death Aug 31, 1997 |
| 404 | `tupac` | Keffe D guilty verdict Aug 31, 2026 |

Next extra number is one higher than the current max extra (`404` → `405`, …).

## House style

- Canvas `1080×1920`. Photograph cover-fills the frame.
- **12** full-sentence facts. No terminal periods. Last fact is the money shot.
- On-frame: title, year, facts, image caption, credit, `@FactsOrWhacks`.
- Off-frame: episode numbers, hashtags, follow CTA. Custom `postCaption` is the paste block; include a follow line. **Exactly 5 hashtags**, all specific to this episode. No `*Tok`, `#FYP`, `#Reels`, `#Shorts`, `#DidYouKnow`, `#OnThisDay`, or `#FactsOrWhacks`. Do not reuse the same five tags from yesterday. The `@FactsOrWhacks` handle stays in the caption body, not as a hashtag.
- Unique quiet low sine pad seeded by the still stem. No triangle drone, no chorus detune, no 7ths.
- Photo: Wikimedia Commons **public domain or CC**, downloaded locally. Credit on-frame. Prefer a portrait that cover-fills 9:16.
- Do not copy other reels’ scripts. Do not put conspiracy, pending autopsy, or unverified death-toll numbers on the still.

## Build checklist

1. Add a `TEMPLATES` extra **after** the last extra and **before** `universe`. Do not touch apartheid.
2. `public/catalog/{slug}-post.txt` plus generator `extra_rows()` / `{slug}-post.csv`.
3. App download link next to the other extra caption links.
4. Tests: `src/templates.test.ts`, `src/lib/drawReel.test.ts` (caption phrases stay off-canvas), `src/lib/postCaption.test.ts`, `src/lib/catalogCaptions.test.ts` (header + extras: physical lines = `396 + extras`, body = `395 + extras`).
5. Attribution in `public/images/ATTRIBUTION.md`. Extra row in `public/catalog/VIDEO_CAPTIONS.md`.
6. `npm run catalog:captions`
7. `npx vitest run`
8. Vite on `http://127.0.0.1:5173`. `node scripts/export_template_still.mjs --id <id>`
9. Encode 30s with `encode_one(..., audio=None, seed="<stem>")` from `scripts/stills_to_videos.py`. Delete an existing dest first if it is a stale skip (`size > 50k`).
10. Copy `*_9x16_still.png`, `*_30s.mp4`, `*_post.txt` to `/opt/cursor/artifacts/` and `/home/ubuntu/Desktop/`.
11. Commit, push, update the existing draft PR. User-facing reply: why this pick, paste caption, still/video tags, Desktop filenames.

Run: `npm install && npm run dev` → `http://localhost:5173`. Tests: `npx vitest run`.
