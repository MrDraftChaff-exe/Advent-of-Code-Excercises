# Discord Closed Messages Finder

Recover forgotten Discord DM partners from **your own** browser cache. Discord stores interaction ranks in `UserAffinitiesStoreV2`; this tool parses that dump and sorts people by:

- recent DMs (`dmRank`)
- frequent conversation (`communicationRank`)
- frequent voice chat (`vcRank`)

Lower rank numbers are stronger matches (1 is best). Unranked `0` values are sorted last. Nothing is uploaded; the dump stays on your machine.

## Run it

### Local web UI (recommended)

```bash
npm start
```

Open [http://localhost:8080/web/](http://localhost:8080/web/). Use **Load sample** to see the fixture, or paste a real `UserAffinitiesStoreV2` value from Discord DevTools.

### CLI

```bash
node cli.js fixtures/user-affinities-v2.json
node cli.js --rank dm fixtures/user-affinities-v2.json
```

### Discord console snippet

1. Open Discord in a browser and sign in.
2. Open DevTools (`Ctrl+Shift+I` / `Cmd+Option+I`) → **Console**.
3. Paste `main.js` and press Enter.
4. Inspect `mostRecentDms_uidQueryFormat`, `mostLikelyToTalk_uidQueryFormat`, or `mostLikelyToVc_uidQueryFormat`.

If the page blocks `localStorage`, copy the store value from **Application → Local Storage** and run:

```js
processAffinityDump(PASTED_JSON)
```

## Copy the cache without the console script

1. `https://discord.com/app`
2. DevTools → **Application** → **Local Storage** → `https://discord.com`
3. Select `UserAffinitiesStoreV2` and copy the value
4. Paste it into the web UI or save it as JSON for `node cli.js`

## Tests

```bash
npm test
```

## Notes

- This only reads affinity ranks already stored in your client. It does not fetch message history or look up usernames.
- `@unknown-user` mentions mean Discord has not cached that profile. Look the ID up with a public Discord ID lookup tool, or request your data from **Settings → Data & Privacy**.
- Discord’s client changes over time. If the store key or shape changes, the parser still accepts a raw `userAffinities` array and both camelCase and snake_case fields.
