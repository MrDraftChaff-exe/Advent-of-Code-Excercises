#!/usr/bin/env node
/**
 * Post from the Facebook calendar (launch/facebook/schedule-30d.json).
 *
 * Algorithm defaults:
 *   - Photo + caption (no bare link attachment)
 *   - Product / suite URLs in the first comment
 *
 * Usage:
 *   npm run facebook-schedule -- --dry-run
 *   npm run facebook-schedule -- --date 2026-08-01
 *   npm run facebook-schedule -- --n 0
 *   npm run facebook-schedule -- --date 2026-08-02 --slot am
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

async function postPhoto({ pageId, token, caption, imageUrl, dryRun }) {
  if (dryRun) {
    return { dryRun: true, id: null, post_id: null };
  }
  const url = new URL(`${GRAPH}/${pageId}/photos`);
  const body = new URLSearchParams({
    url: imageUrl,
    caption,
    published: 'true',
    access_token: token,
  });
  const res = await fetch(url, { method: 'POST', body });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) {
    throw new Error(`photo ${res.status} ${JSON.stringify(data.error || data)}`);
  }
  return data;
}

async function postFeedText({ pageId, token, message, dryRun }) {
  if (dryRun) return { dryRun: true, id: null };
  const url = new URL(`${GRAPH}/${pageId}/feed`);
  const body = new URLSearchParams({
    message,
    access_token: token,
  });
  const res = await fetch(url, { method: 'POST', body });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) {
    throw new Error(`feed ${res.status} ${JSON.stringify(data.error || data)}`);
  }
  return data;
}

async function firstComment({ objectId, token, message, dryRun }) {
  if (!message) return null;
  if (dryRun) return { dryRun: true, id: null };
  const url = new URL(`${GRAPH}/${objectId}/comments`);
  const body = new URLSearchParams({
    message,
    access_token: token,
  });
  const res = await fetch(url, { method: 'POST', body });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) {
    throw new Error(`comment ${res.status} ${JSON.stringify(data.error || data)}`);
  }
  return data;
}

function commentTargetId(result) {
  // Photos return { id: photoId, post_id: "PAGE_POSTID" }; feed returns { id: "PAGE_POSTID" }
  return result.post_id || result.id;
}

function help(schedule) {
  console.log(`
Buckeye Trail Guide — Facebook schedule poster

Schedule: ${SCHEDULE_PATH}
Window:   ${schedule.startDate} → ${schedule.endDate} (${schedule.timezone})
Posts:    ${schedule.totalPosts}

  npm run facebook-schedule -- --dry-run
  npm run facebook-schedule -- --date YYYY-MM-DD [--slot am|pm]
  npm run facebook-schedule -- --n 0
`);
}

function captionWithLinkFallback(post) {
  // Prefer clean caption + first comment. If commenting isn't permitted,
  // we append suite links under a short divider (still better than no links).
  if (!post.firstComment) return post.message;
  return `${post.message}\n\n—\n${post.firstComment}`;
}

async function updatePostMessage({ postId, token, message, dryRun }) {
  if (dryRun) return { dryRun: true, success: true };
  const url = new URL(`${GRAPH}/${postId}`);
  const body = new URLSearchParams({ message, access_token: token });
  const res = await fetch(url, { method: 'POST', body });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) {
    throw new Error(`update ${res.status} ${JSON.stringify(data.error || data)}`);
  }
  return data;
}

async function publishOne({ pageId, token, post, dryRun }) {
  let result;
  if (post.imageUrl) {
    result = await postPhoto({
      pageId,
      token,
      caption: post.message,
      imageUrl: post.imageUrl,
      dryRun,
    });
  } else {
    result = await postFeedText({
      pageId,
      token,
      message: post.message,
      dryRun,
    });
  }

  const target = commentTargetId(result);
  let comment = null;
  let linkMode = 'none';
  if (post.firstComment && target) {
    try {
      comment = await firstComment({
        objectId: target,
        token,
        message: post.firstComment,
        dryRun,
      });
      linkMode = 'first_comment';
    } catch (e) {
      // Missing pages_manage_engagement is common in early apps — fall back.
      console.warn(`  ! first comment blocked (${e.message}) — appending suite links to caption`);
      await updatePostMessage({
        postId: target,
        token,
        message: captionWithLinkFallback(post),
        dryRun,
      });
      linkMode = 'caption_footer';
    }
  }

  return { result, comment, target, linkMode };
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
  console.log(`  date filter: ${args.n != null ? 'n=' + args.n : date}`);
  console.log(`  posts: ${selected.map((p) => `#${p.n} ${p.slot}/${p.pillar}`).join(', ')}`);
  console.log(`  mode: ${args.dryRun ? 'DRY-RUN' : 'LIVE'}`);
  console.log('  format: photo+caption, links in first comment\n');

  for (const post of selected) {
    const key = String(post.n);
    if (!args.dryRun && log.posts[key]?.id) {
      console.log(`→ #${post.n} ${post.slot} skipped (already posted ${log.posts[key].id})`);
      continue;
    }
    console.log(`→ #${post.n} ${post.date} ${post.slot} (${post.pillar})`);
    console.log('  caption:', post.message.slice(0, 120).replace(/\n/g, ' ') + '…');
    console.log('  image:', post.imageUrl ? 'yes' : 'no');
    console.log('  firstComment links:', post.link);
    try {
      const { result, comment, target, linkMode } = await publishOne({
        pageId,
        token,
        post,
        dryRun: args.dryRun,
      });
      if (args.dryRun) {
        console.log('  dry-run ok\n');
      } else {
        console.log(`  ✓ post ${target || result.id}`);
        if (comment?.id) console.log(`  ✓ first comment ${comment.id}`);
        console.log(`  ✓ links via ${linkMode}`);
        console.log('');
        log.posts[key] = {
          id: target || result.id,
          photoId: result.id && result.post_id ? result.id : undefined,
          commentId: comment?.id,
          linkMode,
          date: post.date,
          slot: post.slot,
          at: new Date().toISOString(),
        };
        saveLog(log);
      }
    } catch (e) {
      console.error('  ✗', e.message, '\n');
      process.exitCode = 1;
    }
  }
  console.log('Done.');
}

main().catch((err) => {
  console.error('\nFacebook schedule failed:\n' + err.message);
  process.exit(1);
});
