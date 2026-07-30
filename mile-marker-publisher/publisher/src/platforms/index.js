import { gumroad } from './gumroad.js';
import { etsy } from './etsy.js';
import { lemonsqueezy } from './lemonsqueezy.js';

export const platforms = {
  gumroad,
  etsy,
  lemonsqueezy,
};

export function resolvePlatforms(csv) {
  const wanted = (csv || 'gumroad')
    .split(',')
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
  const list = [];
  for (const id of wanted) {
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
