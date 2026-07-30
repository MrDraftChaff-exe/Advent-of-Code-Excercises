#!/usr/bin/env node
/**
 * Facebook Page credential setup + verify for Buckeye Trail Guide.
 *
 * Cloud-agent friendly flows:
 *   A) OAuth paste-code (recommended if Graph Explorer UI is confusing)
 *      npm run facebook-auth
 *      open the printed URL → approve → copy the address bar (even if localhost fails)
 *      npm run facebook-auth -- --code 'PASTE_CODE_OR_FULL_REDIRECT_URL'
 *
 *   B) Paste Page id + token directly
 *      npm run facebook-auth -- --page-id '123' --token 'EAAB...'
 *
 *   C) Paste /me/accounts JSON
 *      npm run facebook-auth -- --accounts-json '{"data":[...]}'
 *
 * See FACEBOOK_SETUP.md
 */
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from 'dotenv';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const ENV_PATH = path.join(ROOT, '.env');
config({ path: ENV_PATH });

const GRAPH = 'https://graph.facebook.com/v21.0';
const DIALOG = 'https://www.facebook.com/v21.0/dialog/oauth';
const PAGE_NAME_HINT = 'Buckeye Trail Guide';
const REDIRECT_URI =
  process.env.FACEBOOK_REDIRECT_URI || 'https://localhost:3458/oauth/callback';
const SCOPES = (
  process.env.FACEBOOK_SCOPES ||
  'pages_show_list,pages_manage_posts,pages_read_engagement,business_management'
).trim();
const STATE_FILE = path.join(ROOT, '.facebook-oauth-state');

function parseArgs(argv) {
  const out = {
    pageId: null,
    token: null,
    accountsJson: null,
    code: null,
    help: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') out.help = true;
    else if (a === '--page-id') out.pageId = argv[++i];
    else if (a === '--token') out.token = argv[++i];
    else if (a === '--accounts-json') out.accountsJson = argv[++i];
    else if (a === '--code') out.code = argv[++i];
  }
  return out;
}

function help() {
  console.log(`
Buckeye Trail Guide — Facebook Page auth

OAuth (cloud-agent friendly):
  1) In Meta app: add Facebook Login → Valid OAuth Redirect URIs:
       ${REDIRECT_URI}
  2) npm run facebook-auth
  3) Open the printed URL, approve permissions
  4) Browser may fail on localhost — copy the full address bar
  5) npm run facebook-auth -- --code 'PASTE_CODE_OR_FULL_URL'

Or paste credentials:
  npm run facebook-auth -- --page-id 'PAGE_ID' --token 'PAGE_ACCESS_TOKEN'
  npm run facebook-auth -- --accounts-json '{"data":[...]}'

Graph API Explorer (new UI):
  https://developers.facebook.com/tools/explorer/
  Upper right: Meta App = Buckeye Trail Guide
  Upper right: "User or Page" dropdown → Get User Access Token
  Check pages_show_list, pages_manage_posts, pages_read_engagement
  Query: me/accounts → Submit → copy Page id + access_token
`);
}

function upsertEnv(updates) {
  let text = fs.existsSync(ENV_PATH) ? fs.readFileSync(ENV_PATH, 'utf8') : '';
  const lines = text ? text.split(/\r?\n/) : [];
  const keys = setOf(Object.keys(updates));
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

function setOf(arr) {
  return new Set(arr);
}

function requireAppCreds() {
  const appId = (process.env.FACEBOOK_APP_ID || '').trim();
  const appSecret = (process.env.FACEBOOK_APP_SECRET || '').trim();
  if (!appId || !appSecret) {
    throw new Error(
      'Missing FACEBOOK_APP_ID / FACEBOOK_APP_SECRET in publisher/.env\n' +
        'Paste App ID + App Secret from App settings → Basic, then re-run.'
    );
  }
  return { appId, appSecret };
}

function buildAuthorizeUrl(appId) {
  const state = crypto.randomBytes(16).toString('hex');
  fs.writeFileSync(STATE_FILE, state, { mode: 0o600 });
  const url = new URL(DIALOG);
  url.searchParams.set('client_id', appId);
  url.searchParams.set('redirect_uri', REDIRECT_URI);
  url.searchParams.set('state', state);
  url.searchParams.set('response_type', 'code');
  url.searchParams.set('scope', SCOPES);
  return url.toString();
}

function extractCode(input) {
  const raw = String(input || '').trim().replace(/^['"]|['"]$/g, '');
  if (!raw) return null;
  try {
    if (raw.includes('://') || raw.startsWith('?') || raw.includes('code=')) {
      const url = raw.includes('://')
        ? new URL(raw)
        : new URL(raw.startsWith('?') ? `https://localhost/${raw}` : `https://localhost/?${raw}`);
      const err = url.searchParams.get('error_description') || url.searchParams.get('error');
      if (err) throw new Error(`OAuth error from Facebook: ${err}`);
      const state = url.searchParams.get('state');
      if (state && fs.existsSync(STATE_FILE)) {
        const expected = fs.readFileSync(STATE_FILE, 'utf8').trim();
        if (state !== expected) {
          console.warn('Warning: OAuth state mismatch — continuing with code anyway');
        }
      }
      return url.searchParams.get('code');
    }
  } catch (e) {
    if (String(e.message || e).startsWith('OAuth error')) throw e;
  }
  return raw;
}

async function exchangeCode({ appId, appSecret, code }) {
  const url = new URL(`${GRAPH}/oauth/access_token`);
  url.searchParams.set('client_id', appId);
  url.searchParams.set('client_secret', appSecret);
  url.searchParams.set('redirect_uri', REDIRECT_URI);
  url.searchParams.set('code', code);
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error || !data.access_token) {
    throw new Error(`Code exchange failed: ${JSON.stringify(data.error || data)}`);
  }
  return data.access_token;
}

async function extendUserToken({ appId, appSecret, shortToken }) {
  const url = new URL(`${GRAPH}/oauth/access_token`);
  url.searchParams.set('grant_type', 'fb_exchange_token');
  url.searchParams.set('client_id', appId);
  url.searchParams.set('client_secret', appSecret);
  url.searchParams.set('fb_exchange_token', shortToken);
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error || !data.access_token) {
    console.warn('Could not extend user token — using short-lived token:', JSON.stringify(data.error || data));
    return shortToken;
  }
  return data.access_token;
}

async function fetchAccounts(userToken) {
  const url = new URL(`${GRAPH}/me/accounts`);
  url.searchParams.set('fields', 'id,name,access_token,tasks');
  url.searchParams.set('access_token', userToken);
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) {
    throw new Error(`/me/accounts failed: ${JSON.stringify(data.error || data)}`);
  }
  return data;
}

function pickPageFromAccounts(payload) {
  let data = payload;
  if (typeof payload === 'string') {
    const raw = payload.trim().replace(/^['"]|['"]$/g, '');
    data = JSON.parse(raw);
  }
  const rows = data.data || data.accounts || (Array.isArray(data) ? data : null);
  if (!rows?.length) {
    throw new Error(
      'No Pages returned from /me/accounts.\n' +
        'Create a Facebook Page first (facebook.com/pages/create) and make sure this Facebook account is a Page admin.'
    );
  }

  const exact = rows.find(
    (p) => String(p.name || '').toLowerCase() === PAGE_NAME_HINT.toLowerCase()
  );
  const fuzzy = rows.find((p) => String(p.name || '').toLowerCase().includes('buckeye'));
  const page = exact || fuzzy || (rows.length === 1 ? rows[0] : null);
  if (!page) {
    const list = rows.map((p) => `  - ${p.name} (${p.id})`).join('\n');
    throw new Error(`Multiple pages found — pass --page-id explicitly:\n${list}`);
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

async function probeFeed(pageId, token) {
  const url = new URL(`${GRAPH}/${pageId}/feed`);
  url.searchParams.set('limit', '1');
  url.searchParams.set('fields', 'id');
  url.searchParams.set('access_token', token);
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) return { ok: false, error: data.error || data };
  return { ok: true };
}

async function saveAndVerify(pageId, token, label) {
  upsertEnv({
    FACEBOOK_PAGE_ID: pageId,
    FACEBOOK_PAGE_ACCESS_TOKEN: token,
  });
  console.log(`Wrote FACEBOOK_PAGE_ID + FACEBOOK_PAGE_ACCESS_TOKEN → ${ENV_PATH}`);
  if (label) console.log(`Page: ${label} (${pageId})`);

  const page = await verifyPage(pageId, token);
  const feed = await probeFeed(pageId, token);
  const dbg = await debugToken(token);

  console.log('\nBuckeye Trail Guide — Facebook connected\n');
  console.log(`Page: ${page.name}`);
  console.log(`ID:   ${page.id}`);
  console.log(`URL:  ${page.link || '(n/a)'}`);
  if (page.category) console.log(`Cat:  ${page.category}`);
  console.log(`Feed: ${feed.ok ? 'readable ✓' : 'check failed — ' + JSON.stringify(feed.error)}`);
  if (dbg?.scopes) console.log(`Scopes (debug): ${Array.isArray(dbg.scopes) ? dbg.scopes.join(', ') : dbg.scopes}`);
  if (dbg?.error) console.log(`Token debug: ${JSON.stringify(dbg.error)}`);
  if (dbg && 'expires_at' in dbg) {
    const exp = !dbg.expires_at ? 'never / unknown' : new Date(dbg.expires_at * 1000).toISOString();
    console.log(`Expires: ${exp}`);
  }
  console.log('\nNext:');
  console.log('  npm run facebook-posts -- --dry-run');
  console.log('  npm run facebook-posts\n');
}

function printAuthorizeInstructions(appId) {
  const url = buildAuthorizeUrl(appId);
  console.log(`
Buckeye Trail Guide — Facebook OAuth

1) In your Meta app dashboard:
   - Add product: Facebook Login (or Facebook Login for Business)
   - Facebook Login → Settings → Valid OAuth Redirect URIs:
     ${REDIRECT_URI}
   - Save changes

2) Open this URL while logged into the Facebook account that owns the Page:

${url}

3) Approve the permissions (Pages list + manage posts).

4) Facebook will redirect to localhost — the page may fail to load.
   Copy the FULL address bar (it contains ?code=...).

5) Paste it back:

   npm run facebook-auth -- --code 'PASTE_FULL_URL_OR_CODE'

Also required: a Facebook Page that this account admins
  https://www.facebook.com/pages/create
`);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) return help();

  // OAuth code exchange path
  if (args.code) {
    const { appId, appSecret } = requireAppCreds();
    const code = extractCode(args.code);
    if (!code) throw new Error('Could not find OAuth code in --code value');
    console.log('Exchanging OAuth code…');
    const shortUser = await exchangeCode({ appId, appSecret, code });
    console.log('Extending to long-lived user token…');
    const userToken = await extendUserToken({ appId, appSecret, shortToken: shortUser });
    upsertEnv({ FACEBOOK_USER_ACCESS_TOKEN: userToken });
    console.log('Fetching Pages via /me/accounts…');
    const accounts = await fetchAccounts(userToken);
    const picked = pickPageFromAccounts(accounts);
    await saveAndVerify(picked.pageId, picked.token, picked.name);
    try {
      fs.unlinkSync(STATE_FILE);
    } catch {
      /* ignore */
    }
    return;
  }

  let pageId = (args.pageId || process.env.FACEBOOK_PAGE_ID || '').trim();
  let token = (args.token || process.env.FACEBOOK_PAGE_ACCESS_TOKEN || '').trim();

  if (args.accountsJson) {
    const picked = pickPageFromAccounts(args.accountsJson);
    pageId = picked.pageId;
    token = picked.token;
    console.log(`Picked page from /me/accounts: ${picked.name} (${pageId})`);
  }

  if (args.pageId || args.token || args.accountsJson) {
    if (!pageId || !token) throw new Error('Need both Page ID and Page access token');
    await saveAndVerify(pageId, token);
    return;
  }

  if (pageId && token) {
    await saveAndVerify(pageId, token);
    return;
  }

  // No page creds yet — print OAuth URL if app creds exist
  const appId = (process.env.FACEBOOK_APP_ID || '').trim();
  const appSecret = (process.env.FACEBOOK_APP_SECRET || '').trim();
  if (appId && appSecret) {
    printAuthorizeInstructions(appId);
    return;
  }

  help();
  throw new Error('Missing Facebook credentials — see instructions above.');
}

main().catch((err) => {
  console.error('\nFacebook auth failed:\n' + err.message);
  process.exit(1);
});
