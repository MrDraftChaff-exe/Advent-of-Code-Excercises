const RANK_KEYS = ["dmRank", "communicationRank", "vcRank"];

function asNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function unwrapStore(raw) {
  if (raw == null) {
    throw new Error("Affinity store is empty.");
  }

  let data = raw;
  if (typeof data === "string") {
    const trimmed = data.trim();
    if (!trimmed) {
      throw new Error("Affinity store JSON is empty.");
    }
    try {
      data = JSON.parse(trimmed);
    } catch {
      throw new Error("Affinity store is not valid JSON.");
    }
  }

  if (typeof data === "string") {
    try {
      data = JSON.parse(data);
    } catch {
      throw new Error("Affinity store JSON is double-encoded and could not be parsed.");
    }
  }

  if (Array.isArray(data)) {
    return { userAffinities: data, lastFetched: null };
  }

  if (typeof data !== "object") {
    throw new Error("Affinity store has an unexpected shape.");
  }

  const state = data._state && typeof data._state === "object" ? data._state : data;
  const userAffinities = state.userAffinities ?? state.user_affinities;

  if (!Array.isArray(userAffinities)) {
    throw new Error("Could not find a userAffinities array in the store.");
  }

  return {
    userAffinities,
    lastFetched: state.lastFetched ?? state.last_fetched ?? null
  };
}

function normalizeEntry(entry) {
  if (!entry || typeof entry !== "object") {
    return null;
  }

  const userId = entry.otherUserId ?? entry.other_user_id ?? entry.userId ?? entry.user_id;
  if (userId == null || userId === "") {
    return null;
  }

  return {
    userId: String(userId),
    communicationRank: asNumber(entry.communicationRank ?? entry.communication_rank),
    dmRank: asNumber(entry.dmRank ?? entry.dm_rank),
    vcRank: asNumber(entry.vcRank ?? entry.vc_rank),
    isFriend: Boolean(entry.isFriend ?? entry.is_friend)
  };
}

function rankSortValue(rank) {
  // Discord ranks are 1-based: 1 is strongest. 0 / missing means unranked.
  if (!Number.isFinite(rank) || rank <= 0) {
    return Number.POSITIVE_INFINITY;
  }
  return rank;
}

export function parseAffinityStore(raw) {
  const { userAffinities, lastFetched } = unwrapStore(raw);
  const users = {};

  for (const entry of userAffinities) {
    const normalized = normalizeEntry(entry);
    if (!normalized) {
      continue;
    }
    users[normalized.userId] = normalized;
  }

  return {
    users,
    lastFetched: lastFetched == null ? null : asNumber(lastFetched) || lastFetched,
    count: Object.keys(users).length
  };
}

export function buildRankedLists(users, rankKey) {
  if (!RANK_KEYS.includes(rankKey)) {
    throw new Error(`Unknown rank key: ${rankKey}`);
  }

  const sorted = Object.values(users)
    .slice()
    .sort((a, b) => {
      const byRank = rankSortValue(a[rankKey]) - rankSortValue(b[rankKey]);
      if (byRank !== 0) {
        return byRank;
      }
      return a.userId.localeCompare(b.userId);
    });

  const formatted = sorted.map(
    (user) =>
      `<@${user.userId}> | ${rankKey}: ${user[rankKey]} | isFriend: ${user.isFriend} | userId: ${user.userId}`
  );

  return { sorted, formatted };
}

export function processAffinityStore(raw) {
  const parsed = parseAffinityStore(raw);
  const dm = buildRankedLists(parsed.users, "dmRank");
  const talk = buildRankedLists(parsed.users, "communicationRank");
  const vc = buildRankedLists(parsed.users, "vcRank");

  return {
    lastFetched: parsed.lastFetched,
    count: parsed.count,
    users: parsed.users,
    mostRecentDms: dm.sorted,
    mostRecentDms_uidQueryFormat: dm.formatted,
    mostLikelyToTalk: talk.sorted,
    mostLikelyToTalk_uidQueryFormat: talk.formatted,
    mostLikelyToVc: vc.sorted,
    mostLikelyToVc_uidQueryFormat: vc.formatted
  };
}

export function formatLastFetched(lastFetched) {
  if (lastFetched == null || lastFetched === "") {
    return "unknown";
  }
  const date = new Date(lastFetched);
  if (Number.isNaN(date.getTime())) {
    return String(lastFetched);
  }
  return `${date.toLocaleString()} (Unix: ${lastFetched})`;
}

export const RANK_LABELS = {
  dmRank: "Recent DMs",
  communicationRank: "Most likely to talk",
  vcRank: "Most likely to VC"
};
