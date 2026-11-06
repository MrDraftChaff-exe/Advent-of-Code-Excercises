/**
 * Discord Closed Messages Finder — console snippet
 *
 * How to run:
 * 1. Open Discord in a browser (discord.com/app) and sign in.
 * 2. Press Ctrl+Shift+I (Cmd+Option+I on macOS) and open the Console tab.
 * 3. Paste this entire file and press Enter.
 *
 * Then inspect:
 *   mostRecentDms_uidQueryFormat
 *   mostLikelyToTalk_uidQueryFormat
 *   mostLikelyToVc_uidQueryFormat
 *
 * Safer alternative: copy the UserAffinitiesStoreV2 value from
 * DevTools → Application → Local Storage and paste it into index.html.
 */
(function discordClosedMessagesFinder() {
  const STORE_KEYS = ["UserAffinitiesStoreV2", "UserAffinitiesStore"];

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
      data = JSON.parse(data);
    }
    if (typeof data === "string") {
      data = JSON.parse(data);
    }
    if (Array.isArray(data)) {
      return { userAffinities: data, lastFetched: null };
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
    if (!Number.isFinite(rank) || rank <= 0) {
      return Number.POSITIVE_INFINITY;
    }
    return rank;
  }

  function buildRankedLists(users, rankKey) {
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

  function readStoreFromStorage(storage) {
    if (!storage) {
      return null;
    }
    for (const key of STORE_KEYS) {
      const value = storage.getItem(key);
      if (value) {
        return { key, value };
      }
    }
    return null;
  }

  function readLocalStore() {
    const errors = [];

    try {
      const found = readStoreFromStorage(window.localStorage);
      if (found) {
        return found;
      }
      errors.push("page localStorage did not contain an affinity store");
    } catch (error) {
      errors.push(`page localStorage: ${error.message}`);
    }

    let iframe;
    try {
      iframe = document.createElement("iframe");
      iframe.style.display = "none";
      document.body.appendChild(iframe);
      const storage = iframe.contentWindow && iframe.contentWindow.localStorage;
      const found = readStoreFromStorage(storage);
      if (found) {
        return found;
      }
      errors.push("iframe localStorage did not contain an affinity store");
    } catch (error) {
      errors.push(`iframe localStorage: ${error.message}`);
    } finally {
      if (iframe && iframe.parentNode) {
        iframe.parentNode.removeChild(iframe);
      }
    }

    throw new Error(
      "Could not read Discord localStorage from this page.\n" +
        errors.join("\n") +
        "\nCopy UserAffinitiesStoreV2 from DevTools → Application → Local Storage and run:\n" +
        "processAffinityDump(copiedValue)"
    );
  }

  function processAffinityDump(raw) {
    const { userAffinities, lastFetched } = unwrapStore(raw);
    const users = {};
    for (const entry of userAffinities) {
      const normalized = normalizeEntry(entry);
      if (normalized) {
        users[normalized.userId] = normalized;
      }
    }

    const dm = buildRankedLists(users, "dmRank");
    const talk = buildRankedLists(users, "communicationRank");
    const vc = buildRankedLists(users, "vcRank");
    const fetchedLabel = lastFetched == null ? "unknown" : `${new Date(lastFetched).toLocaleString()} | Unix: ${lastFetched}`;

    const result = {
      lastFetched,
      count: Object.keys(users).length,
      formattedUserAffinities: users,
      mostRecentDms: dm.sorted,
      mostRecentDms_uidQueryFormat: dm.formatted,
      mostLikelyToTalk: talk.sorted,
      mostLikelyToTalk_uidQueryFormat: talk.formatted,
      mostLikelyToVc: vc.sorted,
      mostLikelyToVc_uidQueryFormat: vc.formatted
    };

    Object.assign(globalThis, result);

    console.log(`🔎 Parsed cached UserAffinities data...
Cache last updated: ${fetchedLabel}
Users found: ${result.count}

Type one of these in the console:
• mostRecentDms_uidQueryFormat    - Users you DM'd most recently
• mostLikelyToTalk_uidQueryFormat - Users you talked to frequently
• mostLikelyToVc_uidQueryFormat   - Users you VC'd with most frequently

Need a dump instead? processAffinityDump(jsonStringOrObject)
`);

    return result;
  }

  globalThis.processAffinityDump = processAffinityDump;

  try {
    const { key, value } = readLocalStore();
    console.log(`Using localStorage key: ${key}`);
    processAffinityDump(value);
  } catch (error) {
    console.error(error.message || error);
    console.info(
      "You can still paste a copied store value:\nprocessAffinityDump(YOUR_JSON_HERE)"
    );
  }
})();
