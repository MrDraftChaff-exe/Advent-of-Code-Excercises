#!/usr/bin/env node
/**
 * Verify Facebook Page credentials for Buckeye Trail Guide.
 *
 * Requires in .env:
 *   FACEBOOK_PAGE_ID
 *   FACEBOOK_PAGE_ACCESS_TOKEN
 *
 * See FACEBOOK_SETUP.md
 */
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from 'dotenv';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
config({ path: path.join(ROOT, '.env') });

const GRAPH = 'https://graph.facebook.com/v21.0';

async function main() {
  const pageId = (process.env.FACEBOOK_PAGE_ID || '').trim();
  const token = (process.env.FACEBOOK_PAGE_ACCESS_TOKEN || '').trim();
  if (!pageId || !token) {
    throw new Error(
      [
        'Missing FACEBOOK_PAGE_ID / FACEBOOK_PAGE_ACCESS_TOKEN in publisher/.env',
        '',
        'Create a Facebook Page, then follow publisher/FACEBOOK_SETUP.md',
        '(Graph API Explorer → /me/accounts → copy Page id + access_token).',
      ].join('\n')
    );
  }

  const url = new URL(`${GRAPH}/${pageId}`);
  url.searchParams.set('fields', 'id,name,link,fan_count,access_token');
  url.searchParams.set('access_token', token);
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) {
    throw new Error(
      `Facebook page check failed: ${res.status} ${JSON.stringify(data.error || data)}\n` +
        'Token may be expired, wrong, or missing pages_* permissions.'
    );
  }

  console.log('\nBuckeye Trail Guide — Facebook connected\n');
  console.log(`Page: ${data.name}`);
  console.log(`ID:   ${data.id}`);
  console.log(`URL:  ${data.link || '(n/a)'}`);
  console.log('\nNext: npm run facebook-posts -- --dry-run\n');
}

main().catch((err) => {
  console.error('\nFacebook auth failed:\n' + err.message);
  process.exit(1);
});
