#!/usr/bin/env node
import path from 'node:path';
import { config } from 'dotenv';
import { fileURLToPath } from 'node:url';
import { loadProducts, ROOT } from './catalog.js';
import { loadState, saveState, getPlatformRecord } from './state.js';
import { resolvePlatforms, missingEnv } from './platforms/index.js';
import { syncSiteCatalog } from './sync-site.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
config({ path: path.join(__dirname, '../.env') });
config({ path: path.join(ROOT, '.env') });

function parseArgs(argv) {
  const args = {
    dryRun: false,
    platforms: 'gumroad',
    product: null,
    syncSite: true,
    help: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--dry-run') args.dryRun = true;
    else if (a === '--help' || a === '-h') args.help = true;
    else if (a === '--no-sync-site') args.syncSite = false;
    else if (a === '--sync-site-only') args.syncSiteOnly = true;
    else if (a === '--platforms') args.platforms = argv[++i];
    else if (a === '--product') args.product = argv[++i];
  }
  return args;
}

function help() {
  console.log(`
Buckeye Trail Guide — deploy kits to sales platforms

Usage:
  npm run publish -- [options]
  node src/cli.js [options]

Options:
  --dry-run              Show what would happen (no API writes)
  --platforms a,b        gumroad,lemonsqueezy (default: gumroad; etsy paused)
  --product <id>         Only sync one product folder id
  --no-sync-site         Do not rewrite site/src/catalog.js Gumroad URLs
  --sync-site-only       Only rewrite site catalog from state.json
  -h, --help             Show help

Env (see .env.example):
  GUMROAD_ACCESS_TOKEN
  ETSY_*                 (paused — not in active pipeline)
  LEMON_SQUEEZY_API_KEY LEMON_SQUEEZY_STORE_ID
`);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) return help();

  const state = loadState();

  if (args.syncSiteOnly) {
    const out = syncSiteCatalog(state);
    console.log(`Synced site catalog → ${out}`);
    return;
  }

  const only = args.product ? [args.product] : null;
  const products = loadProducts({ only });
  const selected = resolvePlatforms(args.platforms);

  console.log(`Buckeye Trail Guide`);
  console.log(`  products: ${products.map((p) => p.id).join(', ')}`);
  console.log(`  platforms: ${selected.map((p) => p.id).join(', ')}`);
  console.log(`  mode: ${args.dryRun ? 'DRY RUN' : 'LIVE'}`);
  console.log('');

  for (const platform of selected) {
    const missing = missingEnv(platform);
    if (missing.length && !args.dryRun) {
      console.error(`Skipping ${platform.id}: missing env ${missing.join(', ')}`);
      continue;
    }
    if (missing.length && args.dryRun) {
      console.warn(`[dry-run] ${platform.id} would need env: ${missing.join(', ')}`);
    }

    for (const product of products) {
      console.log(`→ ${product.id} @ ${platform.id}`);
      const record = getPlatformRecord(state, product.id, platform.id);
      try {
        const result = await platform.publish(product, record, { dryRun: args.dryRun });
        console.log(`  ✓ ${JSON.stringify(result)}`);
        if (!args.dryRun && result && !result.dryRun) {
          Object.assign(record, result);
          saveState(state);
        }
      } catch (err) {
        console.error(`  ✗ ${err.message}`);
        process.exitCode = 1;
      }
    }
  }

  if (!args.dryRun && args.syncSite && selected.some((p) => p.id === 'gumroad')) {
    const out = syncSiteCatalog(state);
    console.log(`\nSite catalog updated → ${out}`);
  }

  console.log(`\nState file: ${path.join(ROOT, 'publisher', 'state.json')}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
