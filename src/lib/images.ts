const cache = new Map<string, Promise<HTMLImageElement | null>>();

/** Wikimedia allows CORS; still proxy in Vite so canvas export is not tainted. */
export function resolveImageUrl(url: string): string {
  const src = url.trim();
  if (!src) return src;
  if (typeof window === "undefined") return src;
  const wiki = "https://upload.wikimedia.org";
  if (!src.startsWith(wiki + "/")) return src;
  const local = window.location.hostname;
  if (local === "localhost" || local === "127.0.0.1" || local === "0.0.0.0") {
    return "/wiki-media" + src.slice(wiki.length);
  }
  return src;
}

export function loadReelImage(url: string): Promise<HTMLImageElement | null> {
  const original = url.trim();
  if (!original) return Promise.resolve(null);
  if (typeof Image === "undefined") return Promise.resolve(null);
  const src = resolveImageUrl(original);
  const hit = cache.get(src);
  if (hit) return hit;
  const pending = new Promise<HTMLImageElement | null>((resolve) => {
    const img = new Image();
    img.decoding = "async";
    if (/^https?:/i.test(src) || src.startsWith("/wiki-media")) {
      img.crossOrigin = "anonymous";
      img.referrerPolicy = "no-referrer";
    }
    img.onload = () => resolve(img);
    img.onerror = () => {
      if (src !== original && original.startsWith("http")) {
        const fallback = new Image();
        fallback.decoding = "async";
        fallback.crossOrigin = "anonymous";
        fallback.referrerPolicy = "no-referrer";
        fallback.onload = () => resolve(fallback);
        fallback.onerror = () => resolve(null);
        fallback.src = original;
        return;
      }
      resolve(null);
    };
    img.src = src;
  });
  cache.set(src, pending);
  return pending;
}

export function readImageFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () =>
      reject(reader.error ?? new Error("Could not read image"));
    reader.readAsDataURL(file);
  });
}
