import fs from 'node:fs';
import { SITE_CATALOG } from './catalog.js';

/**
 * Rewrite gumroad URLs in site/src/catalog.js from deploy state.
 */
export function syncSiteCatalog(state) {
  if (!fs.existsSync(SITE_CATALOG)) {
    throw new Error(`Site catalog not found: ${SITE_CATALOG}`);
  }
  let src = fs.readFileSync(SITE_CATALOG, 'utf8');

  for (const [productId, platforms] of Object.entries(state.products || {})) {
    const url = platforms.gumroad?.url;
    if (!url) continue;
    // Match gumroad: '...' or gumroad: "..." inside the product object that has id: 'productId'
    const blockRe = new RegExp(
      `(id:\\s*'${escapeReg(productId)}'[\\s\\S]*?gumroad:\\s*)(['"])(.*?)\\2`,
      'm'
    );
    if (!blockRe.test(src)) {
      console.warn(`Could not find gumroad field for ${productId} in catalog.js`);
      continue;
    }
    src = src.replace(blockRe, `$1$2${url}$2`);
  }

  fs.writeFileSync(SITE_CATALOG, src);
  return SITE_CATALOG;
}

function escapeReg(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
