# Daily Facts or Whacks reel

One growth post per calendar day for `@FactsOrWhacks`. Delivery is the download pack from this studio. This repo does **not** post to TikTok, Reels, or Shorts. You paste the caption.

Do **not** add a second post the same day. One clip per platform per day. Cross-posting the same clip to TikTok, Reels, and Shorts is fine.

## Use the studio (no cloud-agent tokens)

The cheap daily path is the app you already run:

```bash
npm install
npm run dev
```

Open `http://localhost:5173`.

1. Click **Today’s reel**. That loads the dated extra already in `src/lib/dailyReel.ts` (today: 9/11 on Sep 11).
2. **Save PNG** for the 9:16 poster still. **Download video** for a studio WebM, or run `npm run daily:pack` for the collage MP4 + unique pad. The file must **probe at least 60.0 seconds**. Encode at 62s so players that round down still show a full minute.
3. **Copy post caption** and paste under the post.

If Today’s reel says this date has no extra, **search the 395-episode catalog** in the same sidebar and load one. Still zero tokens.

`npm run daily:pack` is the unattended version of those same studio export scripts (Vite + still snapshot + ffmpeg). It does **not** call an LLM.

```bash
# Studio must already be running on http://127.0.0.1:5173
npm run daily:pack
# optional: npm run daily:pack -- --date 2026-09-11
```

That writes `*_9x16_still.png`, `*_60s.mp4`, and `*_post.txt` to `/opt/cursor/artifacts` and `/home/ubuntu/Desktop` when those folders exist, and always to `dist/template-stills/`.

Schedule that script on your machine, not a Cursor cloud agent:

```
0 8 * * * cd /path/to/facts-or-whacks && npm run daily:pack
```

Keep `npm run dev` running, or start it in the same crontab before the pack command. Use your local timezone so “today” matches the calendar.

## Do not schedule a daily Cursor agent

A Cursor Automation that starts a cloud agent every morning **rewrites an extra with an LLM**. That is the token burn. Use it only when you need a **new newsjack extra** that is not already a template (death, verdict, disaster). Then the agent adds one extra, and after that the studio button / `daily:pack` can ship it again for free.

If you still want an agent for newsjack days only, the prompt is:

```
Read DAILY_REEL.md and follow it exactly.

Ship today’s @FactsOrWhacks growth reel only if it is a newsjack extra that is not already in src/lib/dailyReel.ts. Use the studio: add a TEMPLATES extra, then npm run daily:pack (Vite still + collage MP4 that probes >= 60s). Put the still, mp4, and caption on /opt/cursor/artifacts and /home/ubuntu/Desktop. Commit, push this branch, update the existing draft PR. Do not mention the PR in the user-facing reply. Do not make a screen recording.

Stay on the current feature branch. Do not replace TEMPLATES[0] (apartheid).
```

## Pick (Trends > newsjack > anniversary > catalog)

Run `npm run trends` first (US Google Trends RSS). It does not post anything. It classifies each query as `candidate`, `hold`, `weak`, or `skip`. `daily:pack` stays token-free and does not call Trends.

1. **Google Trends (US)** that can be a Facts or Whacks extra: 12 short facts, a PD/CC photograph, not pending death facts. Skip sports scores, weather, gadget launches, licensed games/film stills, celebrity gossip, and crypto memes. If Trends is **tomorrow’s** bigger anniversary, **hold it** and pick today’s extra instead (example: 9/11 search on Sep 10 waits for Sep 11).
2. **Newsjack** a still-moving story that HistoryTok will search today (death, verdict, disaster, royal/pop-culture spike). Skip if facts, death tolls, or cause are still moving, or if a licensed photo is messy. Cause of death stays off the still unless it is settled public record and not pending investigation.
3. **On-this-day anniversary** the AP “Today in History” lead, or the date people will actually search. Skip if we posted that subject yesterday.
4. **Catalog** only if 1–3 fail. Do not dump the 395 pack. Do not post two similar 12-fact stills in one day.

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
| 405 | `japan-surrender` | V-J Day / USS Missouri, Sep 2, 1945 |
| 406 | `gloria-steinem` | Died Sep 2, 2026, age 92 |
| 407 | `squeaky-fromme` | Ford assassination attempt Sep 5, 1975 |
| 408 | `magellan` | Victoria completes first circumnavigation Sep 6, 1522 |
| 409 | `star-trek` | Original series premiere Sep 8, 1966 — 60th anniversary |
| 410 | `elvis` | Ed Sullivan debut Sep 9, 1956 — 70th anniversary. 60s collage |
| 411 | `lhc` | LHC first beam Sep 10, 2008 — 18 years. Trends held 9/11 for Sep 11 |
| 412 | `september-11` | 9/11 25th anniversary. Seventh moment of silence. 60s collage |

Next extra number is one higher than the current max extra (`412` → `413`, …). Add a new extra to `DAILY_TEMPLATE_BY_MD` in `src/lib/dailyReel.ts` so **Today’s reel** can load it.

## House style

- Canvas `1080×1920`. Photograph cover-fills the frame.
- **12** full-sentence facts. No terminal periods. Last fact is the money shot.
- Daily **growth video is at least 60 seconds** (platform monetization). Encode the collage at **62 seconds** so `ffprobe` reports >= 60.0 after xfade. The poster PNG still shows all 12 facts. The MP4 is a collage: six beats, two facts each, Ken Burns zoom, crossfade between public-domain photographs. Prefer 4–6 local Commons photos; a single photo still gets fact beats and zoom.
- On-frame: title, year, facts, image caption, credit, `@FactsOrWhacks`.
- Off-frame: episode numbers, hashtags, follow CTA. Custom `postCaption` is the paste block; include a follow line. **Exactly 5 hashtags**, all specific to this episode. No `*Tok`, `#FYP`, `#Reels`, `#Shorts`, `#DidYouKnow`, `#OnThisDay`, or `#FactsOrWhacks`. Do not reuse the same five tags from yesterday. The `@FactsOrWhacks` handle stays in the caption body, not as a hashtag.
- Unique quiet sine pad seeded by the still stem. It should breathe, change chords, and pulse. No triangle drone, no chorus detune, no 7ths.
- Photo: Wikimedia Commons **public domain or CC**, downloaded locally. Credit on-frame. Prefer a portrait that cover-fills 9:16.
- Do not copy other reels’ scripts. Do not put conspiracy, pending autopsy, or unverified death-toll numbers on the still.

## Build checklist (newsjack extra only)

1. Add a `TEMPLATES` extra **after** the last extra and **before** `universe`. Do not touch apartheid.
2. `public/catalog/{slug}-post.txt` plus generator `extra_rows()` / `{slug}-post.csv`.
3. App download link next to the other extra caption links. Map the date in `src/lib/dailyReel.ts`.
4. Tests: `src/templates.test.ts`, `src/lib/drawReel.test.ts` (caption phrases stay off-canvas), `src/lib/postCaption.test.ts`, `src/lib/catalogCaptions.test.ts` (header + extras: physical lines = `396 + extras`, body = `395 + extras`), `src/lib/dailyReel.test.ts`.
5. Attribution in `public/images/ATTRIBUTION.md`. Extra row in `public/catalog/VIDEO_CAPTIONS.md`.
6. `npm run catalog:captions`
7. `npx vitest run`
8. Vite on `http://127.0.0.1:5173`. `npm run daily:pack` (or `node scripts/export_template_still.mjs --id <id>` then encode).
9. Encode the collage with `encode_collage(..., seconds=62, seed="<stem>")` from `scripts/stills_to_videos.py` if you are not using `daily:pack`. Confirm `ffprobe` duration is **>= 60**. Delete an existing dest first if it is a stale skip (`size > 50k`).
10. Copy `*_9x16_still.png`, `*_60s.mp4`, and `*_post.txt` to `/opt/cursor/artifacts/` and `/home/ubuntu/Desktop/`.
11. Commit, push, update the existing draft PR. User-facing reply: why this pick, paste caption, still/video tags, Desktop filenames.

Run: `npm install && npm run dev` → `http://localhost:5173`. Tests: `npx vitest run`.
