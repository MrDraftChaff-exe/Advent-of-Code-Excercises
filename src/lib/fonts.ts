export async function loadReelFonts(): Promise<void> {
  if (typeof document === "undefined") return;
  const faces = [
    { url: "/fonts/Montserrat-Medium.ttf", weight: "500" },
    { url: "/fonts/Montserrat-SemiBold.ttf", weight: "600" },
    { url: "/fonts/Montserrat-Bold.ttf", weight: "700" },
    { url: "/fonts/Montserrat-Bold.ttf", weight: "800" },
  ];
  await Promise.all(
    faces.map(async ({ url, weight }) => {
      const face = new FontFace("Montserrat", `url(${url})`, {
        weight,
        style: "normal",
      });
      const loaded = await face.load();
      document.fonts.add(loaded);
    }),
  );
  await Promise.all([
    document.fonts.load("800 64px Montserrat"),
    document.fonts.load("700 34px Montserrat"),
    document.fonts.load("600 30px Montserrat"),
    document.fonts.load("500 34px Montserrat"),
  ]);
  await document.fonts.ready;
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function slugify(name: string) {
  return (
    name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "")
      .slice(0, 48) || "facts-or-whacks"
  );
}
