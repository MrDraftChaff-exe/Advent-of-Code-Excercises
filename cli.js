#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { formatLastFetched, processAffinityStore } from "./lib/affinities.js";

function usage() {
  console.log(`Usage:
  node cli.js <path-to-UserAffinitiesStoreV2.json>
  node cli.js --rank dm|talk|vc <path-to-json>

Paste the UserAffinitiesStoreV2 value from Discord DevTools → Application → Local Storage.
`);
}

function rankFlagToList(result, rank) {
  switch (rank) {
    case "dm":
      return result.mostRecentDms_uidQueryFormat;
    case "talk":
      return result.mostLikelyToTalk_uidQueryFormat;
    case "vc":
      return result.mostLikelyToVc_uidQueryFormat;
    default:
      throw new Error(`Unknown rank "${rank}". Use dm, talk, or vc.`);
  }
}

function parseArgs(argv) {
  const args = argv.slice(2);
  let rank = "all";
  const files = [];

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === "-h" || arg === "--help") {
      return { help: true };
    }
    if (arg === "--rank") {
      rank = args[i + 1];
      i += 1;
      continue;
    }
    files.push(arg);
  }

  return { help: false, rank, file: files[0] };
}

try {
  const options = parseArgs(process.argv);
  if (options.help || !options.file) {
    usage();
    process.exit(options.help ? 0 : 1);
  }

  const raw = readFileSync(options.file, "utf8");
  const result = processAffinityStore(raw);

  console.log(`Parsed ${result.count} users`);
  console.log(`Cache last updated: ${formatLastFetched(result.lastFetched)}`);
  console.log("");

  if (options.rank === "all") {
    console.log("=== mostRecentDms ===");
    console.log(result.mostRecentDms_uidQueryFormat.join("\n"));
    console.log("\n=== mostLikelyToTalk ===");
    console.log(result.mostLikelyToTalk_uidQueryFormat.join("\n"));
    console.log("\n=== mostLikelyToVc ===");
    console.log(result.mostLikelyToVc_uidQueryFormat.join("\n"));
  } else {
    console.log(rankFlagToList(result, options.rank).join("\n"));
  }
} catch (error) {
  console.error(error.message || error);
  process.exit(1);
}
