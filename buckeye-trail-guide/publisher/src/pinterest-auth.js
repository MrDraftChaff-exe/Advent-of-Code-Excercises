#!/usr/bin/env node
/**
 * Pinterest OAuth 2.0 setup for Buckeye Trail Guide.
 *
 * Usage:
 *   1. Register app at https://developers.pinterest.com/apps/ (see PINTEREST_SETUP.md)
 *   2. Set PINTEREST_APP_ID + PINTEREST_APP_SECRET in .env
 *   3. Redirect URI exactly: https://localhost:3457/oauth/callback
 *   4. npm run pinterest-auth
 */
import crypto from 'node:crypto';
import fs from 'node:fs';
import https from 'node:https';
import path from 'node:path';
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

function requireCreds() {
  const appId = process.env.PINTEREST_APP_ID || '';
  const appSecret = process.env.PINTEREST_APP_SECRET || '';
  if (!appId || !appSecret) {
    throw new Error(
      'Set PINTEREST_APP_ID and PINTEREST_APP_SECRET in .env — from https://developers.pinterest.com/apps/'
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
  if (!res.ok) throw new Error(`Token exchange failed: ${res.status} ${JSON.stringify(data)}`);
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

function loadTls() {
  const key = path.join(ROOT, 'certs/localhost-key.pem');
  const cert = path.join(ROOT, 'certs/localhost-cert.pem');
  if (!fs.existsSync(key) || !fs.existsSync(cert)) {
    throw new Error('Missing certs/localhost-*.pem — see publisher/ETSY_SETUP.md openssl notes or PINTEREST_SETUP.md');
  }
  return {
    key: fs.readFileSync(key),
    cert: fs.readFileSync(cert),
  };
}

async function main() {
  const { appId, appSecret } = requireCreds();
  const state = crypto.randomBytes(16).toString('hex');
  const authUrl = new URL('https://www.pinterest.com/oauth/');
  authUrl.searchParams.set('client_id', appId);
  authUrl.searchParams.set('redirect_uri', REDIRECT_URI);
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('scope', SCOPES);
  authUrl.searchParams.set('state', state);

  console.log('\nBuckeye Trail Guide — Pinterest OAuth\n');
  console.log('1) In your Pinterest app, Redirect URI must be EXACTLY:');
  console.log(`   ${REDIRECT_URI}`);
  console.log('\n2) Open this URL in your browser (accept the localhost cert warning):\n');
  console.log(authUrl.toString());
  console.log('\n3) Approve access. Waiting for callback on port', PORT, '…\n');

  const tls = loadTls();
  const code = await new Promise((resolve, reject) => {
    const server = https.createServer(tls, async (req, res) => {
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
        if (!gotCode || gotState !== state) {
          res.writeHead(400, { 'Content-Type': 'text/html' });
          res.end('<h1>Invalid OAuth callback</h1>');
          reject(new Error('Invalid OAuth callback'));
          server.close();
          return;
        }
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end('<h1>Pinterest connected</h1><p>You can close this tab and return to the agent.</p>');
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

  console.log('Exchanging code for tokens…');
  const token = await exchangeCode({ appId, appSecret, code });
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
  }

  upsertEnv({
    PINTEREST_APP_ID: appId,
    PINTEREST_APP_SECRET: appSecret,
    PINTEREST_REDIRECT_URI: REDIRECT_URI,
    PINTEREST_ACCESS_TOKEN: accessToken,
    PINTEREST_REFRESH_TOKEN: refreshToken,
    ...(boardId ? { PINTEREST_BOARD_ID: boardId } : {}),
  });

  console.log('\nSaved tokens to .env (gitignored).');
  if (!boardId) {
    console.log('Create a board on Pinterest, then set PINTEREST_BOARD_ID in .env');
  }
  console.log('Next: npm run pinterest-pins -- --dry-run\n');
}

main().catch((err) => {
  console.error('\nPinterest auth failed:', err.message);
  process.exit(1);
});
