#!/usr/bin/env node
/**
 * Post from the 30-day Facebook calendar (launch/facebook/schedule-30d.json).
 *
 * Usage:
 *   npm run facebook-schedule -- --dry-run
 *   npm run facebook-schedule -- --date 2026-08-02 --dry-run
 *   npm run facebook-schedule -- --date 2026-08-02
 *   npm run facebook-schedule -- --date 2026-08-02 --slot am
 *   npm run facebook-schedule -- --n 1 --dry-run
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from 'dotenv';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const REPO = path.resolve(ROOT, '..');
const SCHEDULE_PATH = path.join(REPO, 'launch/facebook/schedule-30d.json');
const LOG_PATH = path.join(ROOT, 'facebook-schedule-log.json');
config({ path: path.join(ROOT, '.env') });

const GRAPH = 'https://graph.facebook.com/v21.0';

function parseArgs(argv) {
  const out = { dryRun: false, date: null, slot: null, n: null, help: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--dry-run') out.dryRun = true;
    else if (a === '--help' || a === '-h') out.help = true;
    else if (a === '--date') out.date = argv[++i];
    else if (a === '--slot') out.slot = String(argv[++i] || '').toLowerCase();
    else if (a === '--n') out.n = Number(argv[++i]);
  }
  return out;
}

function todayInTz(tz) {
  // en-CA → YYYY-MM-DD
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: tz,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date());
}

function loadSchedule() {
  if (!fs.existsSync(SCHEDULE_PATH)) {
    throw new Error(`Missing schedule: ${SCHEDULE_PATH}`);
  }
  return JSON.parse(fs.readFileSync(SCHEDULE_PATH, 'utf8'));
}

function loadLog() {
  if (!fs.existsSync(LOG_PATH)) return { posts: {} };
  return JSON.parse(fs.readFileSync(LOG_PATH, 'utf8'));
}

function saveLog(log) {
  fs.writeFileSync(LOG_PATH, JSON.stringify(log, null, 2) + '\n');
}

async function postToPage({ pageId, token, message, link, dryRun }) {
  if (dryRun) {
    return { dryRun: true, id: null };
  }
  const url = new URL(`${GRAPH}/${pageId}/feed`);
  const body = new URLSearchParams({
    message,
    link,
    access_token: token,
  });
  const res = await fetch(url, { method: 'POST', body });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) {
    throw new Error(`${res.status} ${JSON.stringify(data.error || data)}`);
  }
  return data;
}

function help(schedule) {
  console.log(`
Buckeye Trail Guide — Facebook schedule poster

Schedule: ${SCHEDULE_PATH}
Window:   ${schedule.startDate} → ${schedule.endDate} (${schedule.timezone})
Posts:    ${schedule.totalPosts}

  npm run facebook-schedule -- --dry-run
  npm run facebook-schedule -- --date YYYY-MM-DD [--slot am|pm]
  npm run facebook-schedule -- --n 12 --dry-run
`);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const schedule = loadSchedule();
  if (args.help) return help(schedule);

  const pageId = (process.env.FACEBOOK_PAGE_ID || '').trim();
  const token = (process.env.FACEBOOK_PAGE_ACCESS_TOKEN || '').trim();
  if (!pageId || !token) {
    throw new Error('Missing FACEBOOK_PAGE_ID / FACEBOOK_PAGE_ACCESS_TOKEN — see FACEBOOK_SETUP.md');
  }

  const date = args.date || todayInTz(schedule.timezone || 'America/New_York');
  let selected = schedule.posts.filter((p) => p.date === date);
  if (args.slot) {
    if (!['am', 'pm'].includes(args.slot)) throw new Error('--slot must be am or pm');
    selected = selected.filter((p) => p.slot === args.slot);
  }
  if (args.n != null) {
    selected = schedule.posts.filter((p) => p.n === args.n);
  }

  if (!selected.length) {
    throw new Error(
      args.n != null
        ? `No post with n=${args.n}`
        : `No scheduled posts for ${date}${args.slot ? ' / ' + args.slot : ''}`
    );
  }

  const log = loadLog();
  console.log('Buckeye Trail Guide — Facebook schedule');
  console.log(`  page: ${pageId}`);
  console.log(`  date: ${date}`);
  console.log(`  posts: ${selected.map((p) => `#${p.n} ${p.slot}/${p.pillar}`).join(', ')}`);
  console.log(`  mode: ${args.dryRun ? 'DRY-RUN' : 'LIVE'}\n`);

  for (const post of selected) {
    const key = String(post.n);
    if (!args.dryRun && log.posts[key]?.id) {
      console.log(`→ #${post.n} ${post.slot} skipped (already posted ${log.posts[key].id})`);
      continue;
    }
    console.log(`→ #${post.n} ${post.date} ${post.slot} (${post.pillar})`);
    console.log(post.message.slice(0, 140).replace(/\n/g, ' ') + (post.message.length > 140 ? '…' : ''));
    try {
      const result = await postToPage({
        pageId,
        token,
        message: post.message,
        link: post.link,
        dryRun: args.dryRun,
      });
      if (args.dryRun) {
        console.log('  dry-run ok\n');
      } else {
        console.log(`  ✓ ${result.id}\n`);
        log.posts[key] = {
          id: result.id,
          date: post.date,
          slot: post.slot,
          at: new Date().toISOString(),
        };
        saveLog(log);
      }
    } catch (e) {
      console.error('  ✗', e.message, '\n');
    }
  }
  console.log('Done.');
}

main().catch((err) => {
  console.error('\nFacebook schedule failed:\n' + err.message);
  process.exit(1);
});
