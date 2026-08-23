/**
 * Lemon Squeezy adapter.
 *
 * LS API can create/update product + variant metadata, but digital file
 * upload is not reliably available via public API (dashboard-hosted files).
 * This adapter syncs name/price/description and prints a clear manual file step
 * unless LEMON_SQUEEZY_SKIP_FILES=false and a future upload endpoint is wired.
 */
export const lemonsqueezy = {
  id: 'lemonsqueezy',
  name: 'Lemon Squeezy',
  requiredEnv: ['LEMON_SQUEEZY_API_KEY', 'LEMON_SQUEEZY_STORE_ID'],

  async publish(product, record, { dryRun }) {
    const apiKey = process.env.LEMON_SQUEEZY_API_KEY;
    const storeId = process.env.LEMON_SQUEEZY_STORE_ID;

    if (dryRun) {
      return {
        dryRun: true,
        would: record.productId ? 'update_metadata' : 'create_product_metadata',
        note: 'File upload must be completed in Lemon Squeezy dashboard (API limitation).',
        files: product.files,
      };
    }

    const headers = {
      Accept: 'application/vnd.api+json',
      'Content-Type': 'application/vnd.api+json',
      Authorization: `Bearer ${apiKey}`,
    };

    let productId = record.productId;
    let variantId = record.variantId;

    if (!productId) {
      console.log('  [lemonsqueezy] creating product…');
      const res = await fetch('https://api.lemonsqueezy.com/v1/products', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          data: {
            type: 'products',
            attributes: {
              name: product.title,
              description: product.descriptionHtml,
              status: 'draft',
              price: product.priceCents,
            },
            relationships: {
              store: { data: { type: 'stores', id: String(storeId) } },
            },
          },
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(`Lemon Squeezy create failed: ${res.status} ${JSON.stringify(data)}`);
      productId = data.data.id;
      // Default variant often created with product — try to read it
      variantId = data.data.attributes?.first_variant_id || data.included?.find((i) => i.type === 'variants')?.id;
    } else {
      console.log(`  [lemonsqueezy] updating product ${productId}…`);
      const res = await fetch(`https://api.lemonsqueezy.com/v1/products/${productId}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({
          data: {
            type: 'products',
            id: String(productId),
            attributes: {
              name: product.title,
              description: product.descriptionHtml,
            },
          },
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(`Lemon Squeezy update failed: ${res.status} ${JSON.stringify(data)}`);
    }

    if (variantId) {
      const res = await fetch(`https://api.lemonsqueezy.com/v1/variants/${variantId}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({
          data: {
            type: 'variants',
            id: String(variantId),
            attributes: {
              price: product.priceCents,
              name: 'Default',
            },
          },
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        console.warn(`  [lemonsqueezy] variant price warn: ${res.status} ${JSON.stringify(data)}`);
      }
    }

    console.warn(
      `  [lemonsqueezy] ACTION REQUIRED: attach files in dashboard for product ${productId}:\n` +
        product.files.map((f) => `    - ${f}`).join('\n')
    );

    return {
      productId,
      variantId: variantId || null,
      url: null,
      manualFilesRequired: true,
      updatedAt: new Date().toISOString(),
    };
  },
};
