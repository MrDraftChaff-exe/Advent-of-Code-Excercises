#!/usr/bin/env node
/**
 * Create Pinterest pins for Buckeye Trail Guide products.
 *
 * Requires .env from npm run pinterest-auth:
 *   PINTEREST_ACCESS_TOKEN, PINTEREST_BOARD_ID
 *
 * Images must be publicly reachable URLs. Uses Gumroad CDN covers when available,
 * otherwise skips with a note (host site or use public cover URLs).
 *
 * Usage:
 *   npm run pinterest-pins -- --dry-run
 *   npm run pinterest-pins
 *   npm run pinterest-pins -- --only columbus-supernatural
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from 'dotenv';
import { loadProducts } from './catalog.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
config({ path: path.join(ROOT, '.env') });

const API = 'https://api.pinterest.com/v5';

function parseArgs(argv) {
  const out = { dryRun: false, only: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--dry-run') out.dryRun = true;
    if (a === '--only') out.only = argv[++i];
  }
  return out;
}

async function refreshIfNeeded() {
  // Access tokens expire (~30d). Refresh when we have a refresh token and get 401 later.
  return process.env.PINTEREST_ACCESS_TOKEN;
}

async function refreshToken() {
  const appId = process.env.PINTEREST_APP_ID;
  const appSecret = process.env.PINTEREST_APP_SECRET;
  const refresh = process.env.PINTEREST_REFRESH_TOKEN;
  if (!appId || !appSecret || !refresh) return null;
  const body = new URLSearchParams({
    grant_type: 'refresh_token',
    refresh_token: refresh,
  });
  const res = await fetch(`${API}/oauth/token`, {
    method: 'POST',
    headers: {
      Authorization: `Basic ${Buffer.from(`${appId}:${appSecret}`).toString('base64')}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`Refresh failed: ${res.status} ${JSON.stringify(data)}`);
  const envPath = path.join(ROOT, '.env');
  let text = fs.readFileSync(envPath, 'utf8');
  text = text.replace(/^PINTEREST_ACCESS_TOKEN=.*$/m, `PINTEREST_ACCESS_TOKEN=${data.access_token}`);
  if (data.refresh_token) {
    text = text.replace(/^PINTEREST_REFRESH_TOKEN=.*$/m, `PINTEREST_REFRESH_TOKEN=${data.refresh_token}`);
  }
  fs.writeFileSync(envPath, text);
  return data.access_token;
}

async function api(accessToken, method, pathname, jsonBody) {
  const res = await fetch(`${API}${pathname}`, {
    method,
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: jsonBody ? JSON.stringify(jsonBody) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (res.status === 401) {
    const err = new Error('unauthorized');
    err.code = 401;
    throw err;
  }
  if (!res.ok) throw new Error(`${method} ${pathname}: ${res.status} ${JSON.stringify(data)}`);
  return data;
}

function pinCopy(product) {
  const title = product.title.slice(0, 100);
  const description = [
    product.oneLiner,
    '',
    ...(product.bullets || []).slice(0, 3).map((b) => `• ${b}`),
    '',
    'From Buckeye Trail Guide — Columbus, Ohio.',
    product.meta?.gumroadHint || '',
  ]
    .filter(Boolean)
    .join('\n')
    .slice(0, 500);
  return { title, description };
}

function publicImageUrl(product) {
  // Prefer explicit public URL in meta; else Gumroad CDN won't work for local files.
  // After site deploy, set PINTEREST_IMAGE_BASE=https://yourdomain.com
  const base = (process.env.PINTEREST_IMAGE_BASE || '').replace(/\/$/, '');
  if (base) return `${base}/covers/${product.id}.png`;
  if (product.meta?.pinImageUrl) return product.meta.pinImageUrl;
  return null;
}

function linkUrl(product) {
  const statePath = path.join(ROOT, 'state.json');
  if (fs.existsSync(statePath)) {
    const state = JSON.parse(fs.readFileSync(statePath, 'utf8'));
    const url = state.products?.[product.id]?.gumroad?.url;
    if (url) return url;
  }
  return `https://buckeyetrailguide.gumroad.com/l/${product.permalink}`;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  let accessToken = await refreshIfNeeded();
  const boardId = process.env.PINTEREST_BOARD_ID;
  if (!accessToken) throw new Error('Missing PINTEREST_ACCESS_TOKEN — run npm run pinterest-auth');
  if (!boardId) throw new Error('Missing PINTEREST_BOARD_ID — run auth or set it in .env');

  const products = loadProducts({ only: args.only ? [args.only] : undefined });
  console.log('Buckeye Trail Guide — Pinterest pins');
  console.log(`  products: ${products.map((p) => p.id).join(', ')}`);
  console.log(`  board: ${boardId}`);
  console.log(`  mode: ${args.dryRun ? 'DRY-RUN' : 'LIVE'}\n`);

  for (const product of products) {
    const imageUrl = publicImageUrl(product);
    const link = linkUrl(product);
    const { title, description } = pinCopy(product);
    console.log(`→ ${product.id}`);
    if (!imageUrl) {
      console.log('  skip: no public image URL. Set PINTEREST_IMAGE_BASE to your deployed site origin,');
      console.log('        or meta.pinImageUrl on the product.');
      continue;
    }
    const payload = {
      board_id: boardId,
      title,
      description,
      link,
      media_source: {
        source_type: 'image_url',
        url: imageUrl,
      },
      alt_text: title.slice(0, 500),
    };
    if (args.dryRun) {
      console.log('  dry-run', JSON.stringify({ title, link, imageUrl }));
      continue;
    }
    try {
      const created = await api(accessToken, 'POST', '/pins', payload);
      console.log('  ✓', created.id || created);
    } catch (e) {
      if (e.code === 401) {
        console.log('  refreshing token…');
        accessToken = await refreshToken();
        if (!accessToken) throw e;
        const created = await api(accessToken, 'POST', '/pins', payload);
        console.log('  ✓', created.id || created);
      } else {
        console.error('  ✗', e.message);
      }
    }
  }
  console.log('\nDone.');
}

main().catch((err) => {
  console.error('\nPinterest pins failed:', err.message);
  process.exit(1);
});
