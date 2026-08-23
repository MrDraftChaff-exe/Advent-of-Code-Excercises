import fs from 'node:fs';
import path from 'node:path';

const API = 'https://api.gumroad.com/v2';

export const gumroad = {
  id: 'gumroad',
  name: 'Gumroad',
  requiredEnv: ['GUMROAD_ACCESS_TOKEN'],

  async publish(product, record, { dryRun, token }) {
    token = token || process.env.GUMROAD_ACCESS_TOKEN;

    if (dryRun) {
      return {
        dryRun: true,
        would: record.id ? 'update' : 'create',
        files: product.files.map((f) => path.basename(f)),
        priceCents: product.priceCents,
        needsToken: !token,
      };
    }

    if (!token) throw new Error('GUMROAD_ACCESS_TOKEN missing');

    const fileUrls = [];
    for (const filePath of product.files) {
      console.log(`  [gumroad] uploading ${path.basename(filePath)}…`);
      fileUrls.push(await uploadFile(token, filePath));
    }

    const payload = {
      name: product.title,
      description: product.descriptionHtml,
      price: String(product.priceCents),
      price_currency_type: 'usd',
      custom_permalink: product.permalink,
      custom_summary: product.oneLiner,
      native_type: 'digital',
      tags: product.tags,
      files: fileUrls.map((url) => ({ url })),
    };

    let productId = record.id;
    let result;

    if (productId) {
      result = await api(token, 'PUT', `/products/${productId}`, payload);
    } else {
      result = await api(token, 'POST', '/products', payload);
      productId = result.product?.id;
    }

    if (!result.success) {
      throw new Error(`Gumroad product save failed: ${JSON.stringify(result)}`);
    }

    // Publish if draft (requires payout method connected on Gumroad)
    if (result.product && result.product.published === false) {
      console.log('  [gumroad] enabling (publish)…');
      try {
        const enabled = await api(token, 'PUT', `/products/${productId}/enable`, {});
        if (!enabled.success) {
          console.warn(`  [gumroad] not published yet: ${enabled.message || JSON.stringify(enabled)}`);
        }
      } catch (err) {
        console.warn(`  [gumroad] enable skipped: ${err.message}`);
      }
    }

    const media = await syncProductMedia(token, productId, product);
    if (media.thumbnailUrl) console.log(`  [gumroad] thumbnail ✓`);
    if (media.coverOk) console.log(`  [gumroad] cover ✓`);

    const fresh = await api(token, 'GET', `/products/${productId}`);
    const p = fresh.product || result.product;

    return {
      id: p.id,
      url: p.short_url || p.url,
      permalink: p.custom_permalink,
      published: p.published,
      price: p.price,
      files: (p.files || []).map((f) => f.name || f.file_name || f),
      thumbnailUrl: p.thumbnail_url || media.thumbnailUrl || null,
      updatedAt: new Date().toISOString(),
    };
  },
};

async function syncProductMedia(token, productId, product) {
  const out = { thumbnailUrl: null, coverOk: false };
  const thumbPath = path.join(product.dir, '..', '..', 'brand', 'thumbnails', `${product.id}.png`);
  const coverPath = path.join(product.dir, '..', '..', 'brand', 'covers', `${product.id}.png`);
  // Prefer explicit public base; else GitHub raw for this repo/branch
  const base =
    (process.env.GUMROAD_MEDIA_BASE || '').replace(/\/$/, '') ||
    githubRawBase();
  if (!base) return out;

  const thumbUrl = `${base}/buckeye-trail-guide/brand/thumbnails/${product.id}.png`;
  const coverUrl = `${base}/buckeye-trail-guide/brand/covers/${product.id}.png`;

  if (fs.existsSync(path.resolve(product.dir, '..', '..', 'brand', 'thumbnails', `${product.id}.png`)) || true) {
    try {
      const res = await api(token, 'POST', `/products/${productId}/thumbnail`, { url: thumbUrl });
      if (res.success) out.thumbnailUrl = res.thumbnail?.url || thumbUrl;
      else console.warn(`  [gumroad] thumbnail warn: ${res.message || JSON.stringify(res)}`);
    } catch (err) {
      console.warn(`  [gumroad] thumbnail skipped: ${err.message}`);
    }
    try {
      const res = await api(token, 'POST', `/products/${productId}/covers`, { url: coverUrl });
      out.coverOk = !!res.success;
      if (!res.success) console.warn(`  [gumroad] cover warn: ${res.message || JSON.stringify(res)}`);
    } catch (err) {
      console.warn(`  [gumroad] cover skipped: ${err.message}`);
    }
  }
  return out;
}

function githubRawBase() {
  const repo = process.env.GITHUB_REPOSITORY || 'MrDraftChaff-exe/Advent-of-Code-Excercises';
  const branch =
    process.env.GUMROAD_MEDIA_BRANCH ||
    process.env.GITHUB_REF_NAME ||
    process.env.GITHUB_HEAD_REF ||
    'cursor/buckeye-trail-guide-090f';
  return `https://raw.githubusercontent.com/${repo}/${branch}`;
}

async function uploadFile(token, filePath) {
  const buf = fs.readFileSync(filePath);
  const filename = path.basename(filePath);

  const presign = await api(token, 'POST', '/files/presign', {
    filename,
    file_size: String(buf.length),
  });
  if (!presign.success) throw new Error(`presign failed: ${JSON.stringify(presign)}`);

  const completedParts = [];
  for (const part of presign.parts) {
    const start = (part.part_number - 1) * 100 * 1024 * 1024;
    const end = Math.min(start + 100 * 1024 * 1024, buf.length);
    const chunk = buf.subarray(start, end);
    const put = await fetch(part.presigned_url, {
      method: 'PUT',
      body: chunk,
      headers: {
        'Content-Type': 'application/octet-stream',
        'Content-Length': String(chunk.length),
      },
    });
    if (!put.ok) {
      const text = await put.text();
      throw new Error(`S3 upload part ${part.part_number} failed: ${put.status} ${text}`);
    }
    const etag = put.headers.get('etag') || put.headers.get('ETag');
    if (!etag) throw new Error(`Missing ETag for part ${part.part_number}`);
    // Gumroad expects the S3 ETag including quotes, e.g. "abc123"
    const etagValue = etag.includes('"') ? etag : `"${etag}"`;
    completedParts.push({ part_number: Number(part.part_number), etag: etagValue });
  }

  const body = new URLSearchParams();
  body.set('access_token', token);
  body.set('upload_id', presign.upload_id);
  body.set('key', presign.key);
  for (const p of completedParts) {
    body.append('parts[][part_number]', String(p.part_number));
    body.append('parts[][etag]', p.etag);
  }

  const res = await fetch(`${API}/files/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  const complete = await res.json().catch(() => ({}));
  if (!res.ok || !complete.success || !complete.file_url) {
    throw new Error(`complete failed: ${res.status} ${JSON.stringify(complete)}`);
  }
  return complete.file_url;
}

async function api(token, method, pathname, fields = {}) {
  if (method === 'GET') {
    const url = new URL(API + pathname);
    url.searchParams.set('access_token', token);
    const res = await fetch(url);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(`Gumroad GET ${pathname}: ${res.status} ${JSON.stringify(data)}`);
    return data;
  }

  const body = new URLSearchParams();
  body.set('access_token', token);

  for (const [key, value] of Object.entries(fields)) {
    if (value === undefined || value === null) continue;
    if (key.startsWith('parts[')) {
      body.set(key, String(value));
      continue;
    }
    if (key === 'tags' && Array.isArray(value)) {
      value.forEach((t) => body.append('tags[]', String(t)));
      continue;
    }
    if (key === 'files' && Array.isArray(value)) {
      value.forEach((f) => {
        if (f.id) body.append('files[][id]', String(f.id));
        if (f.url) body.append('files[][url]', String(f.url));
      });
      continue;
    }
    if (typeof value === 'object') continue;
    body.set(key, String(value));
  }

  const res = await fetch(API + pathname, {
    method,
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`Gumroad ${method} ${pathname}: ${res.status} ${JSON.stringify(data)}`);
  return data;
}
