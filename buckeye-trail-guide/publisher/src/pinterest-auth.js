#!/usr/bin/env node
/**
 * Pinterest OAuth 2.0 setup for Buckeye Trail Guide (cloud-agent friendly).
 *
 * Cloud agents can't receive https://localhost redirects in YOUR browser.
 * Flow:
 *   1. Put PINTEREST_APP_ID + PINTEREST_APP_SECRET in .env
 *   2. npm run pinterest-auth          → prints authorize URL
 *   3. Open URL, approve, browser may fail on localhost — copy the address bar
 *   4. npm run pinterest-auth -- --code 'PASTE_CODE_OR_FULL_REDIRECT_URL'
 *
 * Optional local listener (only works if browser runs on the same machine):
 *   npm run pinterest-auth -- --listen
 */
import crypto from 'node:crypto';
import fs from 'node:fs';
import https from 'node:https';
import path from 'node:path';
import readline from 'node:readline';
import { fileURLToPath } from 'node:url';
import { config } from 'dotenv';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
config({ path: path.join(ROOT, '.env') });

const REDIRECT_URI = process.env.PINTEREST_REDIRECT_URI || 'https://localhost:3457/oauth/callback';
const PORT = Number(new URL(REDIRECT_URI).port || 3457);
const SCOPES = (
  process.env.PINTEREST_SCOPES ||
  'boards:read,boards:write,pins:read,pins:write,user_accounts:read'
).trim();
const STATE_FILE = path.join(ROOT, '.pinterest-oauth-state');

function parseArgs(argv) {
  const out = { listen: false, code: null, help: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--listen') out.listen = true;
    if (a === '--help' || a === '-h') out.help = true;
    if (a === '--code') out.code = argv[++i];
  }
  return out;
}

function requireCreds() {
  const appId = (process.env.PINTEREST_APP_ID || '').trim();
  const appSecret = (process.env.PINTEREST_APP_SECRET || '').trim();
  if (!appId || !appSecret) {
    throw new Error(
      [
        'Missing PINTEREST_APP_ID / PINTEREST_APP_SECRET in publisher/.env',
        '',
        'Fix:',
        '  1) https://developers.pinterest.com/apps/  (Business account)',
        '  2) Connect app → wait for Trial access approval email',
        '  3) Copy App ID + App secret into .env',
        '  4) Add Redirect URI exactly: ' + REDIRECT_URI,
        '',
        'Until Trial is approved, App secret is often locked — that looks like “doesn’t work”.',
      ].join('\n')
    );
  }
  return { appId, appSecret };
}

function upsertEnv(updates) {
  const envPath = path.join(ROOT, '.env');
  let text = fs.existsSync(envPath) ? fs.readFileSync(envPath, 'utf8') : '';
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
    envPath,
    out
      .filter((l, i, a) => !(l === '' && a[i - 1] === ''))
      .join('\n')
      .replace(/\n*$/, '\n')
  );
  fs.chmodSync(envPath, 0o600);
}

function basicAuth(appId, appSecret) {
  return Buffer.from(`${appId}:${appSecret}`).toString('base64');
}

function extractCode(input) {
  const raw = String(input || '').trim().replace(/^['"]|['"]$/g, '');
  if (!raw) return null;
  try {
    if (raw.includes('://') || raw.startsWith('?') || raw.includes('code=')) {
      const url = raw.includes('://')
        ? new URL(raw)
        : new URL(raw.startsWith('?') ? `https://localhost/${raw}` : `https://localhost/?${raw}`);
      return url.searchParams.get('code');
    }
  } catch {
    /* fall through */
  }
  return raw;
}

async function exchangeCode({ appId, appSecret, code }) {
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    redirect_uri: REDIRECT_URI,
  });
  const res = await fetch('https://api.pinterest.com/v5/oauth/token', {
    method: 'POST',
    headers: {
      Authorization: `Basic ${basicAuth(appId, appSecret)}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(
      `Token exchange failed: ${res.status} ${JSON.stringify(data)}\n` +
        `Check Redirect URI is exactly ${REDIRECT_URI} and Trial access is approved.`
    );
  }
  return data;
}

async function pinterestGet(pathname, accessToken) {
  const res = await fetch(`https://api.pinterest.com/v5${pathname}`, {
    headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`GET ${pathname}: ${res.status} ${JSON.stringify(data)}`);
  return data;
}

function buildAuthUrl(appId, state) {
  const authUrl = new URL('https://www.pinterest.com/oauth/');
  authUrl.searchParams.set('client_id', appId);
  authUrl.searchParams.set('redirect_uri', REDIRECT_URI);
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('scope', SCOPES);
  authUrl.searchParams.set('state', state);
  return authUrl.toString();
}

function ask(question) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer);
    });
  });
}

async function finishWithCode({ appId, appSecret, code, expectedState }) {
  const cleaned = extractCode(code);
  if (!cleaned) throw new Error('No authorization code found. Paste the code or full redirect URL.');

  // If they pasted a full URL, optionally check state
  if (String(code).includes('state=') && expectedState) {
    try {
      const url = new URL(String(code).trim());
      const got = url.searchParams.get('state');
      if (got && got !== expectedState) {
        console.warn('Warning: state mismatch — continuing with code anyway.');
      }
    } catch {
      /* ignore */
    }
  }

  console.log('Exchanging code for tokens…');
  const token = await exchangeCode({ appId, appSecret, code: cleaned });
  const accessToken = token.access_token;
  const refreshToken = token.refresh_token || '';

  const me = await pinterestGet('/user_account', accessToken);
  console.log('Connected as:', me.username || me.business_name || me.id || '(user)');

  let boardId = process.env.PINTEREST_BOARD_ID || '';
  try {
    const boards = await pinterestGet('/boards?page_size=25', accessToken);
    const items = boards.items || [];
    console.log('\nBoards:');
    for (const b of items) console.log(`  - ${b.name} (${b.id})`);
    if (!boardId && items.length) {
      const preferred =
        items.find((b) => /buckeye|trail|columbus|guide/i.test(b.name || '')) || items[0];
      boardId = preferred.id;
      console.log(`\nUsing board: ${preferred.name} (${boardId})`);
    }
  } catch (e) {
    console.warn('Could not list boards yet:', e.message);
    console.warn('If this is Trial/consumer-type error, wait for Trial approval or request Standard access.');
  }

  upsertEnv({
    PINTEREST_APP_ID: appId,
    PINTEREST_APP_SECRET: appSecret,
    PINTEREST_REDIRECT_URI: REDIRECT_URI,
    PINTEREST_ACCESS_TOKEN: accessToken,
    PINTEREST_REFRESH_TOKEN: refreshToken,
    ...(boardId ? { PINTEREST_BOARD_ID: boardId } : {}),
  });

  try {
    fs.unlinkSync(STATE_FILE);
  } catch {
    /* ignore */
  }

  console.log('\nSaved tokens to .env (gitignored).');
  if (!boardId) console.log('Create a board on Pinterest, then set PINTEREST_BOARD_ID in .env');
  console.log('Next: npm run pinterest-pins -- --dry-run\n');
}

async function listenForCode(expectedState) {
  const key = path.join(ROOT, 'certs/localhost-key.pem');
  const cert = path.join(ROOT, 'certs/localhost-cert.pem');
  if (!fs.existsSync(key) || !fs.existsSync(cert)) {
    throw new Error('Missing certs/localhost-*.pem');
  }
  const tls = { key: fs.readFileSync(key), cert: fs.readFileSync(cert) };
  return new Promise((resolve, reject) => {
    const server = https.createServer(tls, (req, res) => {
      try {
        const url = new URL(req.url, REDIRECT_URI);
        if (url.pathname !== new URL(REDIRECT_URI).pathname) {
          res.writeHead(404);
          res.end('Not found');
          return;
        }
        const err = url.searchParams.get('error');
        if (err) {
          res.writeHead(400, { 'Content-Type': 'text/html' });
          res.end(`<h1>OAuth error</h1><pre>${err}</pre>`);
          reject(new Error(err));
          server.close();
          return;
        }
        const gotState = url.searchParams.get('state');
        const gotCode = url.searchParams.get('code');
        if (!gotCode || gotState !== expectedState) {
          res.writeHead(400, { 'Content-Type': 'text/html' });
          res.end('<h1>Invalid OAuth callback</h1>');
          reject(new Error('Invalid OAuth callback'));
          server.close();
          return;
        }
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end('<h1>Pinterest connected</h1><p>You can close this tab.</p>');
        resolve(gotCode);
        server.close();
      } catch (e) {
        reject(e);
        try {
          server.close();
        } catch {
          /* ignore */
        }
      }
    });
    server.listen(PORT, '127.0.0.1');
    server.on('error', reject);
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(`Usage:
  npm run pinterest-auth
  npm run pinterest-auth -- --code 'AUTH_CODE_OR_FULL_REDIRECT_URL'
  npm run pinterest-auth -- --listen   # only if browser is on this same machine
`);
    return;
  }

  const { appId, appSecret } = requireCreds();

  // Completing a prior authorize step
  if (args.code) {
    let expectedState = null;
    try {
      expectedState = fs.readFileSync(STATE_FILE, 'utf8').trim();
    } catch {
      /* optional */
    }
    await finishWithCode({ appId, appSecret, code: args.code, expectedState });
    return;
  }

  const state = crypto.randomBytes(16).toString('hex');
  fs.writeFileSync(STATE_FILE, state, { mode: 0o600 });
  const authUrl = buildAuthUrl(appId, state);

  console.log('\nBuckeye Trail Guide — Pinterest OAuth\n');
  console.log('Redirect URI must be EXACTLY:');
  console.log(`  ${REDIRECT_URI}`);
  console.log('\nOpen this URL, approve access:\n');
  console.log(authUrl);
  console.log('\nThen the browser will go to localhost and may show an error — that is OK.');
  console.log('Copy the FULL address bar URL (includes ?code=...) and run:\n');
  console.log(`  npm run pinterest-auth -- --code 'PASTE_URL_HERE'\n`);

  if (args.listen) {
    console.log(`Also listening on ${REDIRECT_URI} (same-machine browsers only)…\n`);
    const code = await listenForCode(state);
    await finishWithCode({ appId, appSecret, code, expectedState: state });
    return;
  }

  // Interactive paste if stdin is a TTY
  if (process.stdin.isTTY) {
    const pasted = await ask('Paste redirect URL or code here (or Ctrl+C to finish later with --code):\n> ');
    if (pasted.trim()) {
      await finishWithCode({ appId, appSecret, code: pasted, expectedState: state });
    }
  }
}

main().catch((err) => {
  console.error('\nPinterest auth failed:\n' + err.message);
  process.exit(1);
});
