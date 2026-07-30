#!/usr/bin/env node
/**
 * Etsy OAuth 2.0 (PKCE) setup for Mile Marker Publisher.
 *
 * Usage:
 *   1. Create an Etsy shop + developer app (see publisher/ETSY_SETUP.md)
 *   2. Put keystring + shared secret in .env as ETSY_API_KEY / ETSY_SHARED_SECRET
 *      (or ETSY_API_KEY=keystring:shared_secret)
 *   3. Register redirect URI exactly: https://localhost:3456/oauth/callback
 *   4. node src/etsy-auth.js
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

const REDIRECT_URI = process.env.ETSY_REDIRECT_URI || 'https://localhost:3456/oauth/callback';
const PORT = Number(new URL(REDIRECT_URI).port || 3456);
const SCOPES = (
  process.env.ETSY_SCOPES ||
  'listings_r listings_w listings_d shops_r shops_w'
).trim();

function parseApiKey() {
  const raw = process.env.ETSY_API_KEY || '';
  const secret = process.env.ETSY_SHARED_SECRET || '';
  if (raw.includes(':')) {
    const [keystring, shared] = raw.split(':');
    return { keystring, sharedSecret: shared, headerValue: raw };
  }
  if (!raw || !secret) {
    throw new Error(
      'Set ETSY_API_KEY (keystring) and ETSY_SHARED_SECRET in .env — from https://www.etsy.com/developers/your-apps'
    );
  }
  return { keystring: raw, sharedSecret: secret, headerValue: `${raw}:${secret}` };
}

function base64url(buf) {
  return Buffer.from(buf)
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/g, '');
}

function pkce() {
  const verifier = base64url(crypto.randomBytes(32));
  const challenge = base64url(crypto.createHash('sha256').update(verifier).digest());
  return { verifier, challenge };
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
  fs.writeFileSync(envPath, out.filter((l, i, a) => !(l === '' && a[i - 1] === '')).join('\n').replace(/\n*$/, '\n'));
  fs.chmodSync(envPath, 0o600);
}

async function exchangeCode({ keystring, code, verifier }) {
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: keystring,
    redirect_uri: REDIRECT_URI,
    code,
    code_verifier: verifier,
  });
  const res = await fetch('https://api.etsy.com/v3/public/oauth/token', {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(`Token exchange failed: ${res.status} ${JSON.stringify(data)}`);
  return data;
}

async function fetchShopId(apiKeyHeader, accessToken) {
  // Prefer shop belonging to the token user
  const me = await fetch('https://openapi.etsy.com/v3/application/users/me', {
    headers: {
      'x-api-key': apiKeyHeader,
      Authorization: `Bearer ${accessToken}`,
      Accept: 'application/json',
    },
  });
  const meData = await me.json().catch(() => ({}));
  if (!me.ok) {
    console.warn('Could not read /users/me:', me.status, JSON.stringify(meData));
  }
  const userId = meData.user_id || String(accessToken).split('.')[0];
  if (!userId) throw new Error('Could not determine Etsy user id from token');

  const shops = await fetch(`https://openapi.etsy.com/v3/application/users/${userId}/shops`, {
    headers: {
      'x-api-key': apiKeyHeader,
      Authorization: `Bearer ${accessToken}`,
      Accept: 'application/json',
    },
  });
  const shopData = await shops.json();
  if (!shops.ok) throw new Error(`Fetch shops failed: ${shops.status} ${JSON.stringify(shopData)}`);

  const shop = shopData.results?.[0] || shopData.shop_id && shopData;
  const shopId = shop?.shop_id || shopData.shop_id;
  if (!shopId) {
    throw new Error(
      'No Etsy shop found on this account. Open https://www.etsy.com/sell and create a shop first.'
    );
  }
  return { shopId, shopName: shop?.shop_name || shopData.shop_name };
}

async function suggestTaxonomy(apiKeyHeader, accessToken) {
  // Seller taxonomy nodes — search for digital/printable-ish
  const res = await fetch('https://openapi.etsy.com/v3/application/seller-taxonomy/nodes', {
    headers: {
      'x-api-key': apiKeyHeader,
      Authorization: `Bearer ${accessToken}`,
      Accept: 'application/json',
    },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    console.warn('Taxonomy lookup failed; set ETSY_TAXONOMY_ID manually later.');
    return null;
  }

  const hits = [];
  const walk = (nodes, trail = []) => {
    for (const n of nodes || []) {
      const name = n.name || '';
      const pathName = [...trail, name].join(' > ');
      const lower = pathName.toLowerCase();
      if (
        /digital|printable|instant download|download|pdf|template/.test(lower) ||
        /prints$|clip art|graphics/.test(lower)
      ) {
        hits.push({ id: n.id, path: pathName });
      }
      if (n.children?.length) walk(n.children, [...trail, name]);
    }
  };
  walk(data.results || data);
  return hits.slice(0, 8);
}

function loadCerts() {
  const key = path.join(ROOT, 'certs/localhost-key.pem');
  const cert = path.join(ROOT, 'certs/localhost-cert.pem');
  if (!fs.existsSync(key) || !fs.existsSync(cert)) {
    throw new Error('Missing certs/localhost-*.pem — regenerate with openssl (see ETSY_SETUP.md)');
  }
  return { key: fs.readFileSync(key), cert: fs.readFileSync(cert) };
}

async function main() {
  const { keystring, headerValue } = parseApiKey();
  const { verifier, challenge } = pkce();
  const state = base64url(crypto.randomBytes(16));

  const authUrl = new URL('https://www.etsy.com/oauth/connect');
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('client_id', keystring);
  authUrl.searchParams.set('redirect_uri', REDIRECT_URI);
  authUrl.searchParams.set('scope', SCOPES);
  authUrl.searchParams.set('state', state);
  authUrl.searchParams.set('code_challenge', challenge);
  authUrl.searchParams.set('code_challenge_method', 'S256');

  console.log('\nMile Marker Publisher — Etsy OAuth\n');
  console.log('1) In your Etsy app, callback URL must be EXACTLY:');
  console.log(`   ${REDIRECT_URI}`);
  console.log('\n2) Open this URL in your browser (accept the localhost cert warning):\n');
  console.log(authUrl.toString());
  console.log('\n3) Approve access. Waiting for callback on port', PORT, '…\n');

  const { key, cert } = loadCerts();

  await new Promise((resolve, reject) => {
    const server = https.createServer({ key, cert }, async (req, res) => {
      try {
        const url = new URL(req.url, REDIRECT_URI);
        if (url.pathname !== new URL(REDIRECT_URI).pathname) {
          res.writeHead(404);
          res.end('Not found');
          return;
        }
        if (url.searchParams.get('error')) {
          res.writeHead(400, { 'Content-Type': 'text/plain' });
          res.end(`Etsy error: ${url.searchParams.get('error_description') || url.searchParams.get('error')}`);
          server.close();
          reject(new Error(url.searchParams.get('error_description') || url.searchParams.get('error')));
          return;
        }
        const code = url.searchParams.get('code');
        const returnedState = url.searchParams.get('state');
        if (!code || returnedState !== state) {
          res.writeHead(400, { 'Content-Type': 'text/plain' });
          res.end('Invalid state or missing code');
          server.close();
          reject(new Error('Invalid OAuth callback'));
          return;
        }

        const tokens = await exchangeCode({ keystring, code, verifier });
        const { shopId, shopName } = await fetchShopId(headerValue, tokens.access_token);
        const taxonomyHits = await suggestTaxonomy(headerValue, tokens.access_token);

        const updates = {
          ETSY_API_KEY: headerValue.includes(':') ? headerValue : `${keystring}:${process.env.ETSY_SHARED_SECRET}`,
          ETSY_ACCESS_TOKEN: tokens.access_token,
          ETSY_REFRESH_TOKEN: tokens.refresh_token || '',
          ETSY_SHOP_ID: String(shopId),
          ETSY_AUTO_PUBLISH: process.env.ETSY_AUTO_PUBLISH || 'true',
        };
        if (taxonomyHits?.[0]?.id && !process.env.ETSY_TAXONOMY_ID) {
          updates.ETSY_TAXONOMY_ID = String(taxonomyHits[0].id);
        }
        upsertEnv(updates);

        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(
          `<html><body style="font-family:sans-serif;padding:2rem">
           <h1>Etsy connected</h1>
           <p>Shop: <strong>${shopName || shopId}</strong> (${shopId})</p>
           <p>Tokens saved to <code>.env</code>. You can close this tab and return to Cursor.</p>
           </body></html>`
        );

        console.log(`✓ Connected shop: ${shopName || ''} (${shopId})`);
        console.log('✓ Access + refresh tokens written to .env (gitignored)');
        if (taxonomyHits?.length) {
          console.log('\nSuggested taxonomy IDs (set ETSY_TAXONOMY_ID):');
          for (const h of taxonomyHits) console.log(`  ${h.id}  ${h.path}`);
          if (updates.ETSY_TAXONOMY_ID) {
            console.log(`\nAuto-selected ETSY_TAXONOMY_ID=${updates.ETSY_TAXONOMY_ID}`);
          }
        }
        console.log('\nNext:\n  npm run publish -- --platforms etsy\n');
        server.close();
        resolve();
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end(String(err.message || err));
        server.close();
        reject(err);
      }
    });

    server.listen(PORT, '127.0.0.1', () => {
      console.log(`Listening on https://127.0.0.1:${PORT}`);
    });
    server.on('error', reject);
  });
}

main().catch((err) => {
  console.error('\n✗', err.message || err);
  process.exit(1);
});
