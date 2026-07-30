import fs from 'node:fs';
import { STATE_PATH } from './catalog.js';

export function loadState() {
  if (!fs.existsSync(STATE_PATH)) {
    return { products: {} };
  }
  return JSON.parse(fs.readFileSync(STATE_PATH, 'utf8'));
}

export function saveState(state) {
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2) + '\n');
}

export function getPlatformRecord(state, productId, platform) {
  state.products ??= {};
  state.products[productId] ??= {};
  state.products[productId][platform] ??= {};
  return state.products[productId][platform];
}
