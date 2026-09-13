/** Source rectangle that cover-crops an image into a destination box. */
export function coverSourceRect(
  imgW: number,
  imgH: number,
  destW: number,
  destH: number,
  focusY = 0.3,
): { sx: number; sy: number; sw: number; sh: number } {
  if (imgW <= 0 || imgH <= 0 || destW <= 0 || destH <= 0) {
    return {
      sx: 0,
      sy: 0,
      sw: Math.max(1, imgW),
      sh: Math.max(1, imgH),
    };
  }
  const imageRatio = imgW / imgH;
  const cropRatio = destW / destH;
  if (imageRatio > cropRatio) {
    const sw = imgH * cropRatio;
    return { sx: (imgW - sw) / 2, sy: 0, sw, sh: imgH };
  }
  const sh = imgW / cropRatio;
  const maxSy = Math.max(0, imgH - sh);
  const sy = Math.max(0, Math.min(maxSy, imgH * focusY - sh / 2));
  return { sx: 0, sy, sw: imgW, sh };
}

/** Zoom into an already-computed cover crop without sampling outside the image. */
export function kenBurnsRect(
  src: { sx: number; sy: number; sw: number; sh: number },
  scale: number,
  focusX: number,
  focusY: number,
): { sx: number; sy: number; sw: number; sh: number } {
  const zoom = Math.max(1, scale);
  const sw = src.sw / zoom;
  const sh = src.sh / zoom;
  const fx = Math.max(0, Math.min(1, focusX));
  const fy = Math.max(0, Math.min(1, focusY));
  const sx = src.sx + (src.sw - sw) * fx;
  const sy = src.sy + (src.sh - sh) * fy;
  return { sx, sy, sw, sh };
}
