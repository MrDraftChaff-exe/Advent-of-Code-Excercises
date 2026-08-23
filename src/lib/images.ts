const cache = new Map<string, Promise<HTMLImageElement | null>>();

export function loadReelImage(url: string): Promise<HTMLImageElement | null> {
  const src = url.trim();
  if (!src) return Promise.resolve(null);
  if (typeof Image === "undefined") return Promise.resolve(null);
  const hit = cache.get(src);
  if (hit) return hit;
  const pending = new Promise<HTMLImageElement | null>((resolve) => {
    const img = new Image();
    img.decoding = "async";
    img.onload = () => resolve(img);
    img.onerror = () => resolve(null);
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
