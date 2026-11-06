import {
  formatLastFetched,
  processAffinityStore
} from "../lib/affinities.js";

const SAMPLE_URL = "../fixtures/user-affinities-v2.json";

const state = {
  result: null,
  rank: "dmRank",
  friendsOnly: false,
  query: ""
};

const els = {
  dump: document.querySelector("#dump"),
  parse: document.querySelector("#parse"),
  sample: document.querySelector("#sample"),
  clear: document.querySelector("#clear"),
  status: document.querySelector("#status"),
  meta: document.querySelector("#meta"),
  tabs: document.querySelector("#tabs"),
  search: document.querySelector("#search"),
  friendsOnly: document.querySelector("#friends-only"),
  copy: document.querySelector("#copy"),
  table: document.querySelector("#results")
};

const RANK_LISTS = {
  dmRank: "mostRecentDms",
  communicationRank: "mostLikelyToTalk",
  vcRank: "mostLikelyToVc"
};

function setStatus(message, kind) {
  els.status.textContent = message;
  els.status.className = `status ${kind || ""}`;
}

function activeUsers() {
  if (!state.result) {
    return [];
  }
  const users = state.result[RANK_LISTS[state.rank]] || [];
  const query = state.query.trim().toLowerCase();
  return users.filter((user) => {
    if (state.friendsOnly && !user.isFriend) {
      return false;
    }
    if (!query) {
      return true;
    }
    return (
      user.userId.includes(query) ||
      String(user.isFriend).includes(query) ||
      `<@${user.userId}>`.includes(query)
    );
  });
}

function render() {
  if (!state.result) {
    els.meta.textContent = "";
    els.table.innerHTML = `<div class="empty">Paste a UserAffinitiesStoreV2 dump and parse it to see ranked users.</div>`;
    return;
  }

  const users = activeUsers();
  els.meta.innerHTML = `
    <span>${state.result.count} users in cache</span>
    <span>Last fetched: ${formatLastFetched(state.result.lastFetched)}</span>
    <span>Showing ${users.length}</span>
  `;

  if (!users.length) {
    els.table.innerHTML = `<div class="empty">No users matched this filter.</div>`;
    return;
  }

  const rows = users
    .map(
      (user, index) => `
      <tr>
        <td>${index + 1}</td>
        <td class="mention">&lt;@${user.userId}&gt;</td>
        <td>${user.userId}</td>
        <td>${user[state.rank]}</td>
        <td class="${user.isFriend ? "friend" : ""}">${user.isFriend}</td>
      </tr>`
    )
    .join("");

  els.table.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Mention</th>
            <th>User ID</th>
            <th>${state.rank}</th>
            <th>Friend</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function parseDump(raw) {
  const result = processAffinityStore(raw);
  state.result = result;
  setStatus(`Parsed ${result.count} users.`, "ok");
  render();
  return result;
}

els.parse.addEventListener("click", () => {
  try {
    parseDump(els.dump.value);
  } catch (error) {
    state.result = null;
    setStatus(error.message, "error");
    render();
  }
});

els.sample.addEventListener("click", async () => {
  try {
    const response = await fetch(SAMPLE_URL);
    if (!response.ok) {
      throw new Error("Could not load the sample fixture.");
    }
    const text = await response.text();
    els.dump.value = text;
    parseDump(text);
  } catch (error) {
    setStatus(error.message, "error");
  }
});

els.clear.addEventListener("click", () => {
  els.dump.value = "";
  state.result = null;
  setStatus("Cleared.");
  render();
});

els.tabs.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-rank]");
  if (!button) {
    return;
  }
  state.rank = button.dataset.rank;
  for (const tab of els.tabs.querySelectorAll("button")) {
    tab.classList.toggle("active", tab === button);
  }
  render();
});

els.search.addEventListener("input", () => {
  state.query = els.search.value;
  render();
});

els.friendsOnly.addEventListener("change", () => {
  state.friendsOnly = els.friendsOnly.checked;
  render();
});

els.copy.addEventListener("click", async () => {
  if (!state.result) {
    setStatus("Parse a dump before copying.", "error");
    return;
  }
  const lines = activeUsers().map(
    (user) =>
      `<@${user.userId}> | ${state.rank}: ${user[state.rank]} | isFriend: ${user.isFriend} | userId: ${user.userId}`
  );
  try {
    await navigator.clipboard.writeText(lines.join("\n"));
    setStatus(`Copied ${lines.length} mention lines.`, "ok");
  } catch {
    setStatus("Clipboard permission was denied.", "error");
  }
});

render();
