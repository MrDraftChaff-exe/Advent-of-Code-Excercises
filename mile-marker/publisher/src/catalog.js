/**
 * Load Mile Marker products from products/<id>/meta.json
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(__dirname, '../..');
export const PRODUCTS_DIR = path.join(ROOT, 'products');
export const STATE_PATH = path.join(ROOT, 'publisher', 'state.json');
export const SITE_CATALOG = path.join(ROOT, 'site', 'src', 'catalog.js');

export function loadProducts({ only } = {}) {
  const dirs = fs
    .readdirSync(PRODUCTS_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .filter((id) => !only || only.includes(id));

  return dirs.map((id) => {
    const dir = path.join(PRODUCTS_DIR, id);
    const metaPath = path.join(dir, 'meta.json');
    if (!fs.existsSync(metaPath)) {
      throw new Error(`Missing meta.json for product ${id}`);
    }
    const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
    const files = collectFiles(dir, meta);
    const descriptionHtml = buildDescriptionHtml(meta, dir);
    return {
      id: meta.id || id,
      dir,
      title: meta.title,
      price: meta.price,
      priceCents: Math.round(Number(meta.price) * 100),
      oneLiner: meta.oneLiner || '',
      bullets: meta.bullets || [],
      tags: meta.tags || [],
      permalink: meta.permalink || meta.id || id,
      files,
      descriptionHtml,
      meta,
    };
  });
}

function collectFiles(dir, meta) {
  const explicit = meta.files?.map((f) => path.join(dir, f)) || [];
  if (explicit.length) {
    for (const f of explicit) {
      if (!fs.existsSync(f)) throw new Error(`Missing file listed in meta.files: ${f}`);
    }
    return explicit;
  }
  const found = [];
  for (const name of fs.readdirSync(dir)) {
    if (/\.(pdf|xlsx|zip|png|jpg|jpeg|webp)$/i.test(name)) {
      found.push(path.join(dir, name));
    }
  }
  found.sort();
  if (!found.length) throw new Error(`No downloadable files in ${dir}`);
  return found;
}

function buildDescriptionHtml(meta, dir) {
  if (meta.descriptionHtml) return meta.descriptionHtml;
  const mdPath = path.join(dir, 'product.md');
  const bullets = (meta.bullets || []).map((b) => `<li>${escapeHtml(b)}</li>`).join('');
  let body = `<p>${escapeHtml(meta.oneLiner || '')}</p>`;
  if (bullets) body += `<p><strong>Includes:</strong></p><ul>${bullets}</ul>`;
  body += `<p>Instant digital download from Mile Marker (Columbus / Central Ohio field kits).</p>`;
  body += `<p><em>Personal use. Not affiliated with the City of Columbus or any university.</em></p>`;
  if (fs.existsSync(mdPath)) {
    // Keep HTML lean for marketplaces; full content is in the PDF.
    body += `<p>Full printable guide included in the download.</p>`;
  }
  return body;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}
