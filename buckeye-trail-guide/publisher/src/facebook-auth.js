#!/usr/bin/env node
/**
 * Facebook Page credential setup + verify for Buckeye Trail Guide.
 *
 * Cloud-agent friendly: you create the Page / token in your browser,
 * then paste values here so we can write .env and verify.
 *
 * Usage:
 *   npm run facebook-auth
 *   npm run facebook-auth -- --page-id '123' --token 'EAAB...'
 *   npm run facebook-auth -- --accounts-json '{"data":[...]}'
 *
 * See FACEBOOK_SETUP.md
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from 'dotenv';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const ENV_PATH = path.join(ROOT, '.env');
config({ path: ENV_PATH });

const GRAPH = 'https://graph.facebook.com/v21.0';
const PAGE_NAME_HINT = 'Buckeye Trail Guide';

function parseArgs(argv) {
  const out = {
    pageId: null,
    token: null,
    accountsJson: null,
    help: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') out.help = true;
    else if (a === '--page-id') out.pageId = argv[++i];
    else if (a === '--token') out.token = argv[++i];
    else if (a === '--accounts-json') out.accountsJson = argv[++i];
  }
  return out;
}

function help() {
  console.log(`
Buckeye Trail Guide — Facebook Page auth

1) Create Page + Meta app (see FACEBOOK_SETUP.md)
2) Graph API Explorer → Generate Access Token (pages_show_list, pages_manage_posts, pages_read_engagement)
3) GET /me/accounts → Submit
4) Paste here:

   npm run facebook-auth -- --page-id 'PAGE_ID' --token 'PAGE_ACCESS_TOKEN'

   # or paste the whole /me/accounts JSON:
   npm run facebook-auth -- --accounts-json '{"data":[...]}'

Then:
   npm run facebook-posts -- --dry-run
   npm run facebook-posts
`);
}

function upsertEnv(updates) {
  let text = fs.existsSync(ENV_PATH) ? fs.readFileSync(ENV_PATH, 'utf8') : '';
  const lines = text ? text.split(/\r?\n/) : [];
  const keys = new Set(Object.keys(updates));
  const out = [];
  for (const line of lines) {
    const m = line.match(/^([A-Z0-9_]+)=/);
    if (m && keys.has(m[1])) {
      out.push(`${m[1]}=${updates[m[1]]}`);
      keys.delete(m[1]);
    } else if (line.length || out.length) {
      out.push(line);
    }
  }
  for (const k of keys) out.push(`${k}=${updates[k]}`);
  fs.writeFileSync(
    ENV_PATH,
    out
      .filter((l, i, a) => !(l === '' && a[i - 1] === ''))
      .join('\n')
      .replace(/\n*$/, '\n')
  );
  fs.chmodSync(ENV_PATH, 0o600);
}

function pickPageFromAccounts(payload) {
  let data = payload;
  if (typeof payload === 'string') {
    const raw = payload.trim().replace(/^['"]|['"]$/g, '');
    data = JSON.parse(raw);
  }
  const rows = data.data || data.accounts || (Array.isArray(data) ? data : null);
  if (!rows?.length) {
    throw new Error('No pages in /me/accounts JSON. Expected { "data": [ { id, name, access_token } ] }');
  }

  const exact = rows.find(
    (p) => String(p.name || '').toLowerCase() === PAGE_NAME_HINT.toLowerCase()
  );
  const fuzzy = rows.find((p) =>
    String(p.name || '').toLowerCase().includes('buckeye')
  );
  const page = exact || fuzzy || (rows.length === 1 ? rows[0] : null);
  if (!page) {
    const list = rows.map((p) => `  - ${p.name} (${p.id})`).join('\n');
    throw new Error(
      `Multiple pages found — pass --page-id explicitly:\n${list}`
    );
  }
  if (!page.id || !page.access_token) {
    throw new Error('Selected page is missing id or access_token fields');
  }
  return {
    pageId: String(page.id),
    token: String(page.access_token),
    name: page.name,
  };
}

async function debugToken(token) {
  const appId = (process.env.FACEBOOK_APP_ID || '').trim();
  const appSecret = (process.env.FACEBOOK_APP_SECRET || '').trim();
  if (!appId || !appSecret) return null;
  const url = new URL(`${GRAPH}/debug_token`);
  url.searchParams.set('input_token', token);
  url.searchParams.set('access_token', `${appId}|${appSecret}`);
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) return { error: data.error || data };
  return data.data || data;
}

async function verifyPage(pageId, token) {
  const url = new URL(`${GRAPH}/${pageId}`);
  url.searchParams.set('fields', 'id,name,link,fan_count,category');
  url.searchParams.set('access_token', token);
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) {
    throw new Error(
      `Facebook page check failed: ${res.status} ${JSON.stringify(data.error || data)}\n` +
        'Token may be expired, wrong Page, or missing pages_* permissions.'
    );
  }
  return data;
}

async function probePostPermission(pageId, token) {
  // Dry capability check: fetch feed metadata (does not create a post)
  const url = new URL(`${GRAPH}/${pageId}/feed`);
  url.searchParams.set('limit', '1');
  url.searchParams.set('fields', 'id');
  url.searchParams.set('access_token', token);
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) {
    return { ok: false, error: data.error || data };
  }
  return { ok: true };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) return help();

  let pageId = (args.pageId || process.env.FACEBOOK_PAGE_ID || '').trim();
  let token = (args.token || process.env.FACEBOOK_PAGE_ACCESS_TOKEN || '').trim();
  let pickedName = null;

  if (args.accountsJson) {
    const picked = pickPageFromAccounts(args.accountsJson);
    pageId = picked.pageId;
    token = picked.token;
    pickedName = picked.name;
    console.log(`Picked page from /me/accounts: ${pickedName} (${pageId})`);
  }

  if (args.pageId || args.token || args.accountsJson) {
    if (!pageId || !token) {
      throw new Error('Need both Page ID and Page access token');
    }
    upsertEnv({
      FACEBOOK_PAGE_ID: pageId,
      FACEBOOK_PAGE_ACCESS_TOKEN: token,
    });
    console.log(`Wrote FACEBOOK_PAGE_ID + FACEBOOK_PAGE_ACCESS_TOKEN → ${ENV_PATH}`);
  }

  if (!pageId || !token) {
    help();
    throw new Error(
      'Missing FACEBOOK_PAGE_ID / FACEBOOK_PAGE_ACCESS_TOKEN in publisher/.env\n' +
        'Create the Page, then paste credentials with --page-id / --token (or --accounts-json).'
    );
  }

  const page = await verifyPage(pageId, token);
  const feed = await probePostPermission(pageId, token);
  const dbg = await debugToken(token);

  console.log('\nBuckeye Trail Guide — Facebook connected\n');
  console.log(`Page: ${page.name}`);
  console.log(`ID:   ${page.id}`);
  console.log(`URL:  ${page.link || '(n/a)'}`);
  if (page.category) console.log(`Cat:  ${page.category}`);
  console.log(`Feed: ${feed.ok ? 'readable ✓' : 'check failed — ' + JSON.stringify(feed.error)}`);
  if (dbg?.scopes) console.log(`Scopes (debug): ${dbg.scopes.join(', ')}`);
  if (dbg?.error) console.log(`Token debug: ${JSON.stringify(dbg.error)}`);
  if (dbg?.expires_at) {
    const exp = dbg.expires_at === 0 ? 'never (Page token)' : new Date(dbg.expires_at * 1000).toISOString();
    console.log(`Expires: ${exp}`);
  }

  console.log('\nNext:');
  console.log('  npm run facebook-posts -- --dry-run');
  console.log('  npm run facebook-posts\n');
}

main().catch((err) => {
  console.error('\nFacebook auth failed:\n' + err.message);
  process.exit(1);
});
