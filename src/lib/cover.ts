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
