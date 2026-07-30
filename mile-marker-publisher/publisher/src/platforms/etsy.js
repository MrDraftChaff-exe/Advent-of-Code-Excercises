import fs from 'node:fs';
import path from 'node:path';

const API = 'https://openapi.etsy.com/v3/application';

/**
 * Etsy digital listings.
 * Requires OAuth access token + API key string (keystring) + shop id.
 * Creates/updates draft listings and uploads digital files.
 */
export const etsy = {
  id: 'etsy',
  name: 'Etsy',
  requiredEnv: ['ETSY_API_KEY', 'ETSY_ACCESS_TOKEN', 'ETSY_SHOP_ID'],

  async publish(product, record, { dryRun }) {
    const apiKey = process.env.ETSY_API_KEY;
    const token = process.env.ETSY_ACCESS_TOKEN;
    const shopId = process.env.ETSY_SHOP_ID;
    const taxonomyId = process.env.ETSY_TAXONOMY_ID || '1'; // override with a digital download taxonomy

    if (dryRun) {
      return {
        dryRun: true,
        would: record.listingId ? 'update' : 'create_draft',
        shopId,
        files: product.files.map((f) => path.basename(f)),
      };
    }

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
      for (const tag of product.tags.slice(0, 13)) body.append('tags[]', tag.slice(0, 20));

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

    // Upload / replace digital files
    for (const filePath of product.files) {
      console.log(`  [etsy] uploading ${path.basename(filePath)}…`);
      await uploadListingFile({ headers, shopId, listingId, filePath });
    }

    // Activate if still draft (requires file present)
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
      // let fetch set multipart boundary
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
