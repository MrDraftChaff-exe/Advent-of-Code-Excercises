import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import {
  buildRankedLists,
  formatLastFetched,
  parseAffinityStore,
  processAffinityStore
} from "./affinities.js";

const fixturePath = join(dirname(fileURLToPath(import.meta.url)), "..", "fixtures", "user-affinities-v2.json");
const fixture = JSON.parse(readFileSync(fixturePath, "utf8"));

test("parses the persisted UserAffinitiesStoreV2 shape", () => {
  const parsed = parseAffinityStore(fixture);
  assert.equal(parsed.count, 4);
  assert.equal(parsed.lastFetched, 1730000000000);
  assert.equal(parsed.users["111111111111111111"].communicationRank, 1);
  assert.equal(parsed.users["333333333333333333"].vcRank, 1);
  assert.equal(parsed.users["333333333333333333"].isFriend, true);
});

test("accepts a JSON string, raw state, or a bare array", () => {
  const fromString = parseAffinityStore(JSON.stringify(fixture));
  const fromState = parseAffinityStore(fixture._state);
  const fromArray = parseAffinityStore(fixture._state.userAffinities);

  assert.equal(fromString.count, 4);
  assert.equal(fromState.count, 4);
  assert.equal(fromArray.count, 4);
  assert.equal(fromArray.lastFetched, null);
});

test("sorts lower Discord ranks first and sends unranked users last", () => {
  const { users } = parseAffinityStore(fixture);
  const dms = buildRankedLists(users, "dmRank").sorted.map((user) => user.userId);
  const talks = buildRankedLists(users, "communicationRank").sorted.map((user) => user.userId);
  const vcs = buildRankedLists(users, "vcRank").sorted.map((user) => user.userId);

  assert.deepEqual(dms, [
    "222222222222222222",
    "333333333333333333",
    "111111111111111111",
    "444444444444444444"
  ]);
  assert.deepEqual(talks, [
    "111111111111111111",
    "222222222222222222",
    "333333333333333333",
    "444444444444444444"
  ]);
  assert.deepEqual(vcs, [
    "333333333333333333",
    "111111111111111111",
    "222222222222222222",
    "444444444444444444"
  ]);
});

test("builds mention-formatted query lines", () => {
  const result = processAffinityStore(fixture);
  assert.equal(
    result.mostRecentDms_uidQueryFormat[0],
    "<@222222222222222222> | dmRank: 1 | isFriend: false | userId: 222222222222222222"
  );
  assert.match(formatLastFetched(result.lastFetched), /Unix: 1730000000000/);
});

test("rejects missing or invalid stores with a clear error", () => {
  assert.throws(() => parseAffinityStore(null), /empty/i);
  assert.throws(() => parseAffinityStore("{"), /not valid JSON/i);
  assert.throws(() => parseAffinityStore({ hello: true }), /userAffinities array/i);
});
