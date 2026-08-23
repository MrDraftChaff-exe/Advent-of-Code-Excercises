#!/usr/bin/env node
/**
 * Post Buckeye Trail Guide products to a Facebook Page feed.
 *
 * Requires:
 *   FACEBOOK_PAGE_ID
 *   FACEBOOK_PAGE_ACCESS_TOKEN
 *
 * Usage:
 *   npm run facebook-posts -- --dry-run
 *   npm run facebook-posts
 *   npm run facebook-posts -- --only columbus-supernatural
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from 'dotenv';
import { loadProducts } from './catalog.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
config({ path: path.join(ROOT, '.env') });

const GRAPH = 'https://graph.facebook.com/v21.0';

function parseArgs(argv) {
  const out = { dryRun: false, only: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--dry-run') out.dryRun = true;
    if (a === '--only') out.only = argv[++i];
  }
  return out;
}

function gumroadUrl(product) {
  const statePath = path.join(ROOT, 'state.json');
  if (fs.existsSync(statePath)) {
    const state = JSON.parse(fs.readFileSync(statePath, 'utf8'));
    const url = state.products?.[product.id]?.gumroad?.url;
    if (url) return url;
  }
  return `https://buckeyetrailguide.gumroad.com/l/${product.permalink}`;
}

function messageFor(product) {
  const bullets = (product.bullets || []).slice(0, 3).map((b) => `• ${b}`).join('\n');
  return [
    `${product.title}`,
    product.oneLiner,
    '',
    bullets,
    '',
    `$${product.price} digital download — Buckeye Trail Guide`,
    gumroadUrl(product),
  ]
    .filter(Boolean)
    .join('\n');
}

async function postToPage({ pageId, token, message, link, dryRun }) {
  if (dryRun) {
    return { dryRun: true, message: message.slice(0, 120) + '…', link };
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

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const pageId = (process.env.FACEBOOK_PAGE_ID || '').trim();
  const token = (process.env.FACEBOOK_PAGE_ACCESS_TOKEN || '').trim();
  if (!pageId || !token) {
    throw new Error('Missing FACEBOOK_PAGE_ID / FACEBOOK_PAGE_ACCESS_TOKEN — see FACEBOOK_SETUP.md');
  }

  const products = loadProducts({ only: args.only ? [args.only] : undefined });
  console.log('Buckeye Trail Guide — Facebook Page posts');
  console.log(`  page: ${pageId}`);
  console.log(`  products: ${products.map((p) => p.id).join(', ')}`);
  console.log(`  mode: ${args.dryRun ? 'DRY-RUN' : 'LIVE'}\n`);

  for (const product of products) {
    const link = gumroadUrl(product);
    const message = messageFor(product);
    console.log(`→ ${product.id}`);
    try {
      const result = await postToPage({
        pageId,
        token,
        message,
        link,
        dryRun: args.dryRun,
      });
      if (args.dryRun) console.log('  dry-run', result);
      else console.log('  ✓ post', result.id);
    } catch (e) {
      console.error('  ✗', e.message);
    }
  }
  console.log('\nDone.');
}

main().catch((err) => {
  console.error('\nFacebook posts failed:\n' + err.message);
  process.exit(1);
});
