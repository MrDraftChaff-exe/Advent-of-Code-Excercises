import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const API = 'https://openapi.etsy.com/v3/application';
const TOKEN_URL = 'https://api.etsy.com/v3/public/oauth/token';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ENV_PATH = path.resolve(__dirname, '../../.env');

/**
 * Etsy digital listings.
 * Requires OAuth access token + API key (keystring:shared_secret) + shop id.
 */
export const etsy = {
  id: 'etsy',
  name: 'Etsy',
  requiredEnv: ['ETSY_API_KEY', 'ETSY_ACCESS_TOKEN', 'ETSY_SHOP_ID'],

  async publish(product, record, { dryRun }) {
    const apiKey = normalizeApiKey(process.env.ETSY_API_KEY, process.env.ETSY_SHARED_SECRET);
    let token = process.env.ETSY_ACCESS_TOKEN;
    const shopId = process.env.ETSY_SHOP_ID;
    const taxonomyId = process.env.ETSY_TAXONOMY_ID;
    const keystring = apiKey.split(':')[0];

    if (dryRun) {
      return {
        dryRun: true,
        would: record.listingId ? 'update' : 'create_draft',
        shopId,
        taxonomyId: taxonomyId || null,
        files: product.files.map((f) => path.basename(f)),
      };
    }

    if (!taxonomyId) {
      throw new Error(
        'ETSY_TAXONOMY_ID missing. Re-run node src/etsy-auth.js or set a seller taxonomy id for digital downloads.'
      );
    }

    token = await ensureFreshToken(token, keystring);

    const headers = {
      'x-api-key': apiKey,
      Authorization: `Bearer ${token}`,
      Accept: 'application/json',
    };

    let listingId = record.listingId;

    if (!listingId) {
      console.log('  [etsy] creating draft listing…');
      const body = new URLSearchParams({
        quantity: '999',
        title: product.title.slice(0, 140),
        description: stripHtml(product.descriptionHtml).slice(0, 100000),
        price: String(product.price),
        who_made: 'i_did',
        when_made: 'made_to_order',
        taxonomy_id: String(taxonomyId),
        type: 'download',
        should_auto_renew: 'true',
        is_taxable: 'true',
      });
      for (const tag of product.tags.slice(0, 13)) {
        const t = tag.replace(/[^\w\s-]/g, '').slice(0, 20);
        if (t) body.append('tags[]', t);
      }

      const res = await fetch(`${API}/shops/${shopId}/listings`, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(`Etsy create listing failed: ${res.status} ${JSON.stringify(data)}`);
      listingId = data.listing_id;
    } else {
      console.log(`  [etsy] updating listing ${listingId}…`);
      const body = new URLSearchParams({
        title: product.title.slice(0, 140),
        description: stripHtml(product.descriptionHtml).slice(0, 100000),
        price: String(product.price),
        taxonomy_id: String(taxonomyId),
        type: 'download',
      });
      const res = await fetch(`${API}/shops/${shopId}/listings/${listingId}`, {
        method: 'PATCH',
        headers: { ...headers, 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(`Etsy update listing failed: ${res.status} ${JSON.stringify(data)}`);
    }

    for (const filePath of product.files) {
      console.log(`  [etsy] uploading ${path.basename(filePath)}…`);
      await uploadListingFile({ headers, shopId, listingId, filePath });
    }

    if (process.env.ETSY_AUTO_PUBLISH === 'true') {
      console.log('  [etsy] activating listing…');
      const res = await fetch(`${API}/shops/${shopId}/listings/${listingId}`, {
        method: 'PATCH',
        headers: { ...headers, 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ state: 'active' }),
      });
      const data = await res.json();
      if (!res.ok) {
        console.warn(`  [etsy] activate warning: ${res.status} ${JSON.stringify(data)}`);
      }
    }

    return {
      listingId,
      url: `https://www.etsy.com/listing/${listingId}`,
      shopId,
      updatedAt: new Date().toISOString(),
    };
  },
};

function normalizeApiKey(apiKey, sharedSecret) {
  if (!apiKey) throw new Error('ETSY_API_KEY missing');
  if (apiKey.includes(':')) return apiKey;
  if (!sharedSecret) {
    throw new Error('ETSY_API_KEY must be keystring:shared_secret (or set ETSY_SHARED_SECRET)');
  }
  return `${apiKey}:${sharedSecret}`;
}

async function ensureFreshToken(accessToken, keystring) {
  // Access tokens last ~1 hour. If refresh token exists, refresh proactively when ETSY_FORCE_REFRESH=true
  // or when a prior call failed — for now refresh if ETSY_REFRESH_TOKEN is set and token looks stale via env flag.
  const refresh = process.env.ETSY_REFRESH_TOKEN;
  if (!refresh) return accessToken;
  if (process.env.ETSY_SKIP_REFRESH === 'true') return accessToken;

  // Always refresh before publish so long-running sessions work
  try {
    const body = new URLSearchParams({
      grant_type: 'refresh_token',
      client_id: keystring,
      refresh_token: refresh,
    });
    const res = await fetch(TOKEN_URL, {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    });
    const data = await res.json();
    if (!res.ok) {
      console.warn(`  [etsy] token refresh failed (${res.status}); using existing access token`);
      return accessToken;
    }
    upsertEnv({
      ETSY_ACCESS_TOKEN: data.access_token,
      ...(data.refresh_token ? { ETSY_REFRESH_TOKEN: data.refresh_token } : {}),
    });
    process.env.ETSY_ACCESS_TOKEN = data.access_token;
    if (data.refresh_token) process.env.ETSY_REFRESH_TOKEN = data.refresh_token;
    console.log('  [etsy] refreshed access token');
    return data.access_token;
  } catch (err) {
    console.warn(`  [etsy] token refresh error: ${err.message}`);
    return accessToken;
  }
}

function upsertEnv(updates) {
  if (!fs.existsSync(ENV_PATH)) return;
  let text = fs.readFileSync(ENV_PATH, 'utf8');
  const lines = text.split(/\r?\n/);
  const keys = new Set(Object.keys(updates));
  const out = [];
  for (const line of lines) {
    const m = line.match(/^([A-Z0-9_]+)=/);
    if (m && keys.has(m[1])) {
      out.push(`${m[1]}=${updates[m[1]]}`);
      keys.delete(m[1]);
    } else {
      out.push(line);
    }
  }
  for (const k of keys) out.push(`${k}=${updates[k]}`);
  fs.writeFileSync(ENV_PATH, out.join('\n').replace(/\n*$/, '\n'));
  fs.chmodSync(ENV_PATH, 0o600);
}

async function uploadListingFile({ headers, shopId, listingId, filePath }) {
  const buf = fs.readFileSync(filePath);
  const name = path.basename(filePath);
  const form = new FormData();
  form.append('name', name);
  form.append('file', new Blob([buf]), name);

  const res = await fetch(`${API}/shops/${shopId}/listings/${listingId}/files`, {
    method: 'POST',
    headers: {
      'x-api-key': headers['x-api-key'],
      Authorization: headers.Authorization,
      Accept: 'application/json',
    },
    body: form,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`Etsy file upload failed: ${res.status} ${JSON.stringify(data)}`);
  return data;
}

function stripHtml(html) {
  return String(html)
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n\n')
    .replace(/<\/li>/gi, '\n')
    .replace(/<li>/gi, '• ')
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .trim();
}
