import { gumroad } from './gumroad.js';
import { lemonsqueezy } from './lemonsqueezy.js';
// Etsy paused — fees too high for now. Code kept in etsy.js / etsy-auth.js for later.

export const platforms = {
  gumroad,
  lemonsqueezy,
};

export function resolvePlatforms(csv) {
  const wanted = (csv || 'gumroad')
    .split(',')
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
  const list = [];
  for (const id of wanted) {
    if (id === 'etsy') {
      throw new Error(
        'Etsy is paused (platform fees). Use Gumroad for now. Code remains in src/platforms/etsy.js when you reopen it.'
      );
    }
    if (!platforms[id]) {
      throw new Error(`Unknown platform "${id}". Available: ${Object.keys(platforms).join(', ')}`);
    }
    list.push(platforms[id]);
  }
  return list;
}

export function missingEnv(platform) {
  return (platform.requiredEnv || []).filter((k) => !process.env[k]);
}
