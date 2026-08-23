import { useEffect, useMemo, useRef, useState } from "react";
import type { ReelContent, RevealMode, ThemeId } from "./types";
import { CANVAS_H, CANVAS_W } from "./types";
import {
  THEMES,
  TEMPLATES,
  blankReel,
  cloneTemplate,
} from "./templates";
import { clampDuration } from "./lib/text";
import { drawFrame, snapshotPng } from "./lib/drawReel";
import { loadReelFonts, downloadBlob, slugify } from "./lib/fonts";
import { exportReelVideo } from "./lib/exportVideo";
import { createAmbient } from "./lib/audio";
import { loadReelImage, readImageFile } from "./lib/images";
import {
  type CatalogEpisode,
  episodeToReel,
  loadBundledCatalog,
  parseCatalogCsv,
} from "./lib/catalog";
import { zipReelExports } from "./lib/batchExport";

const STORAGE_KEY = "facts-or-whacks-reel-v2";

function loadSaved(): ReelContent | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<ReelContent>;
    if (!Array.isArray(parsed.bullets) || typeof parsed.title !== "string") {
      return null;
    }
    return parsed as ReelContent;
  } catch {
    return null;
  }
}

export default function App() {
  const [reel, setReel] = useState<ReelContent>(
    () => loadSaved() ?? cloneTemplate(TEMPLATES[0]),
  );
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [fontsReady, setFontsReady] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [photo, setPhoto] = useState<HTMLImageElement | null>(null);
  const [catalog, setCatalog] = useState<CatalogEpisode[]>([]);
  const [query, setQuery] = useState("");
  const [batchFrom, setBatchFrom] = useState(1);
  const [batchTo, setBatchTo] = useState(1);
  const [batching, setBatching] = useState(false);
  const [batchNote, setBatchNote] = useState("");
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioRef = useRef<ReturnType<typeof createAmbient> | null>(null);

  useEffect(() => {
    loadReelFonts()
      .then(() => setFontsReady(true))
      .catch(() => setFontsReady(true));
  }, []);

  useEffect(() => {
    loadBundledCatalog()
      .then((rows) => {
        setCatalog(rows);
        if (rows.length) {
          setBatchFrom(rows[0].n);
          setBatchTo(rows[0].n);
        }
      })
      .catch(() => setCatalog([]));
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reel));
  }, [reel]);

  useEffect(() => {
    let live = true;
    if (!reel.imageUrl) {
      setPhoto(null);
      return;
    }
    loadReelImage(reel.imageUrl).then((img) => {
      if (live) setPhoto(img);
    });
    return () => {
      live = false;
    };
  }, [reel.imageUrl]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    drawFrame(ctx, reel, time, photo);
  }, [reel, time, fontsReady, photo]);

  useEffect(() => {
    if (!playing) {
      audioRef.current?.stop();
      audioRef.current = null;
      return;
    }
    audioRef.current = createAmbient(true);
    let frame = 0;
    let last = performance.now();
    const tick = (now: number) => {
      const dt = (now - last) / 1000;
      last = now;
      setTime((t) => {
        const next = t + dt;
        return next >= reel.durationSec ? 0 : next;
      });
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(frame);
      audioRef.current?.stop();
      audioRef.current = null;
    };
  }, [playing, reel.durationSec]);

  const patch = (partial: Partial<ReelContent>) =>
    setReel((r) => ({ ...r, ...partial }));

  const updateBullet = (index: number, text: string) => {
    setReel((r) => ({
      ...r,
      id: "custom",
      bullets: r.bullets.map((b, i) => (i === index ? text : b)),
    }));
  };

  const clock = useMemo(() => {
    const t = Math.min(time, reel.durationSec);
    return `${t.toFixed(1)}s / ${reel.durationSec}s`;
  }, [time, reel.durationSec]);

  async function onExport() {
    setExporting(true);
    setProgress(0);
    setPlaying(false);
    try {
      const blob = await exportReelVideo(reel, setProgress);
      downloadBlob(blob, `${slugify(reel.name || reel.title)}.webm`);
    } catch (err) {
      console.error(err);
      window.alert(
        "Could not export video in this browser. Try Chrome/Edge, or save a PNG instead.",
      );
    } finally {
      setExporting(false);
      setProgress(0);
    }
  }

  async function onPng() {
    const blob = await snapshotPng(reel, Math.max(time, 3));
    downloadBlob(blob, `${slugify(reel.name || reel.title)}.png`);
  }

  async function onPickImage(file: File | undefined) {
    if (!file) return;
    const url = await readImageFile(file);
    patch({ imageUrl: url });
  }

  const filteredCatalog = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return catalog;
    return catalog.filter(
      (ep) =>
        String(ep.n).includes(q) ||
        ep.title.toLowerCase().includes(q) ||
        ep.hook.toLowerCase().includes(q) ||
        ep.tags.toLowerCase().includes(q),
    );
  }, [catalog, query]);

  function loadEpisode(ep: CatalogEpisode) {
    setReel(episodeToReel(ep));
    setTime(0);
    setPlaying(false);
  }

  async function onImportCsv(file: File | undefined) {
    if (!file) return;
    const text = await file.text();
    const rows = parseCatalogCsv(text);
    if (!rows.length) {
      window.alert("No episodes found in that CSV.");
      return;
    }
    setCatalog(rows);
    setBatchFrom(rows[0].n);
    setBatchTo(rows[0].n);
    loadEpisode(rows[0]);
  }

  async function onBatch(kind: "webm" | "png") {
    const lo = Math.min(batchFrom, batchTo);
    const hi = Math.max(batchFrom, batchTo);
    const slice = catalog.filter((ep) => ep.n >= lo && ep.n <= hi);
    if (!slice.length) {
      window.alert("No catalog episodes in that range.");
      return;
    }
    if (kind === "webm" && slice.length > 10) {
      const ok = window.confirm(
        `WebM encodes in real time (~${slice[0] ? 20 : 20}s each). ${slice.length} videos ≈ ${Math.round((slice.length * 20) / 60)} min. Continue?`,
      );
      if (!ok) return;
    }
    setBatching(true);
    setPlaying(false);
    setBatchNote(`0 / ${slice.length}`);
    try {
      const blob = await zipReelExports(
        slice.map(episodeToReel),
        kind,
        (done, total, name) =>
          setBatchNote(`${done} / ${total}  ${name}`),
      );
      downloadBlob(blob, `facts-or-whacks-${lo}-${hi}.${kind}.zip`);
      setBatchNote(`Saved ${slice.length} ${kind === "webm" ? "videos" : "stills"}`);
    } catch (err) {
      console.error(err);
      window.alert(
        "Batch export failed. Try a smaller range, Chrome/Edge, or PNG stills.",
      );
      setBatchNote("Failed");
    } finally {
      setBatching(false);
    }
  }

  return (
    <div className="app">
      <aside className="editor">
        <div className="brand">
          <div className="brand-mark">?</div>
          <div>
            <h1>Facts or Whacks</h1>
            <p>9:16 phone videos — photo with facts overlaid.</p>
          </div>
        </div>

        <div className="section">
          <h2>395-episode catalog</h2>
          <p className="hint">
            The CSV is scripts + Wikimedia stills, not hosted video files. Load
            an episode, then one-click download a WebM. A range ZIP encodes in
            real time (~20s per video).
          </p>
          <label className="field">
            <span className="field-label">Search</span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="30 or apartheid"
            />
          </label>
          <div className="catalog-list">
            {filteredCatalog.slice(0, 80).map((ep) => (
              <button
                key={ep.n}
                className={`catalog-item ${reel.id === `catalog-${ep.n}` ? "active" : ""}`}
                onClick={() => loadEpisode(ep)}
              >
                <span>{ep.n}.</span> {ep.title}
              </button>
            ))}
          </div>
          {filteredCatalog.length > 80 ? (
            <p className="hint">Showing 80 of {filteredCatalog.length}. Narrow the search.</p>
          ) : null}
          <div className="row-actions">
            <label className="ghost file-chip">
              Import CSV
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={(e) => {
                  void onImportCsv(e.target.files?.[0]);
                  e.target.value = "";
                }}
              />
            </label>
            <button
              className="primary"
              onClick={() => void onExport()}
              disabled={exporting || batching}
            >
              {exporting
                ? `Rendering ${Math.round(progress * 100)}%`
                : "Download this video"}
            </button>
          </div>
          <div className="pair">
            <label className="field">
              <span className="field-label">From</span>
              <input
                type="number"
                min={1}
                max={999}
                value={batchFrom}
                onChange={(e) => setBatchFrom(Number(e.target.value) || 1)}
              />
            </label>
            <label className="field">
              <span className="field-label">To</span>
              <input
                type="number"
                min={1}
                max={999}
                value={batchTo}
                onChange={(e) => setBatchTo(Number(e.target.value) || 1)}
              />
            </label>
          </div>
          <div className="row-actions">
            <button
              className="ghost"
              disabled={batching || exporting || !catalog.length}
              onClick={() => void onBatch("png")}
            >
              ZIP stills
            </button>
            <button
              className="ghost"
              disabled={batching || exporting || !catalog.length}
              onClick={() => void onBatch("webm")}
            >
              ZIP videos
            </button>
          </div>
          {batchNote ? <p className="hint">{batchNote}</p> : null}
        </div>

        <div className="section">
          <h2>Templates</h2>
          <div className="template-row">
            {TEMPLATES.map((t) => (
              <button
                key={t.id}
                className={`chip ${reel.id === t.id ? "active" : ""}`}
                onClick={() => {
                  setReel(cloneTemplate(t));
                  setTime(0);
                }}
              >
                {t.name}
              </button>
            ))}
            <button
              className={`chip ${reel.id === "custom" ? "active" : ""}`}
              onClick={() => {
                setReel(blankReel());
                setTime(0);
              }}
            >
              Blank
            </button>
          </div>
        </div>

        <div className="pair">
          <label className="field">
            <span className="field-label">Episode</span>
            <input
              value={reel.episode}
              onChange={(e) => patch({ episode: e.target.value, id: "custom" })}
              placeholder="30"
            />
            <span className="hint">Catalog and filenames only — not drawn on the video.</span>
          </label>
          <label className="field">
            <span className="field-label">Year</span>
            <input
              value={reel.year}
              onChange={(e) => patch({ year: e.target.value, id: "custom" })}
              placeholder="1994"
            />
          </label>
        </div>

        <label className="field">
          <span className="field-label">Title</span>
          <input
            value={reel.title}
            onChange={(e) => patch({ title: e.target.value, id: "custom" })}
            placeholder="The End of Apartheid"
          />
          <span className="hint">
            Title and facts overlay the 9:16 photo. No episode number and no
            hashtags on the video. Wrap a word in **asterisks** to paint it
            green. Save PNG to edit locally.
          </span>
        </label>

        <div className="section">
          <h2>Image</h2>
          {reel.imageUrl ? (
            <img className="thumb" src={reel.imageUrl} alt={reel.imageCaption} />
          ) : null}
          <label className="field">
            <span className="field-label">Image URL</span>
            <input
              value={reel.imageUrl}
              onChange={(e) => patch({ imageUrl: e.target.value, id: "custom" })}
              placeholder="/images/photo.jpg"
            />
          </label>
          <div className="row-actions">
            <label className="ghost file-chip">
              Upload photo
              <input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  void onPickImage(e.target.files?.[0]);
                  e.target.value = "";
                }}
              />
            </label>
            <button
              className="ghost"
              onClick={() =>
                patch({ imageUrl: "", imageCaption: reel.imageCaption })
              }
              disabled={!reel.imageUrl}
            >
              Clear photo
            </button>
          </div>
          <label className="field">
            <span className="field-label">Caption</span>
            <input
              value={reel.imageCaption}
              onChange={(e) =>
                patch({ imageCaption: e.target.value, id: "custom" })
              }
              placeholder="Nelson Mandela voting, 1994"
            />
          </label>
          <label className="field">
            <span className="field-label">Credit</span>
            <input
              value={reel.imageCredit}
              onChange={(e) =>
                patch({ imageCredit: e.target.value, id: "custom" })
              }
              placeholder="Photo: Name, year · license"
            />
          </label>
        </div>

        <div className="section">
          <h2>Facts</h2>
          {reel.bullets.map((bullet, i) => (
            <div className="fact-card" key={i}>
              <div className="fact-top">
                <span className="bullet-index">{i + 1}</span>
                <button
                  className="ghost danger"
                  onClick={() =>
                    setReel((r) => ({
                      ...r,
                      id: "custom",
                      bullets: r.bullets.filter((_, idx) => idx !== i),
                    }))
                  }
                  disabled={reel.bullets.length <= 1}
                >
                  Remove
                </button>
              </div>
              <textarea
                value={bullet}
                onChange={(e) => updateBullet(i, e.target.value)}
                placeholder="One full-sentence fact"
              />
            </div>
          ))}
          <div className="row-actions">
            <button
              className="ghost"
              onClick={() =>
                setReel((r) => ({
                  ...r,
                  id: "custom",
                  bullets: [...r.bullets, "Another sentence fact."],
                }))
              }
            >
              Add sentence
            </button>
          </div>
        </div>

        <label className="field">
          <span className="field-label">Hashtags</span>
          <textarea
            value={reel.hashtags}
            onChange={(e) => patch({ hashtags: e.target.value, id: "custom" })}
            placeholder="#NelsonMandela #Apartheid #SouthAfrica #HistoryTok"
          />
          <span className="hint">
            Kept for your post caption. Not drawn on the image.
          </span>
        </label>

        <label className="field">
          <span className="field-label">Handle</span>
          <input
            value={reel.handle}
            onChange={(e) => patch({ handle: e.target.value, id: "custom" })}
          />
        </label>

        <label className="field">
          <span className="field-label">Duration ({reel.durationSec}s)</span>
          <input
            type="range"
            min={8}
            max={45}
            value={reel.durationSec}
            onChange={(e) =>
              patch({ durationSec: clampDuration(Number(e.target.value)) })
            }
          />
        </label>

        <div className="section">
          <h2>Theme</h2>
          <div className="theme-row">
            {(Object.keys(THEMES) as ThemeId[]).map((id) => (
              <button
                key={id}
                className={`chip ${reel.theme === id ? "active" : ""}`}
                onClick={() => patch({ theme: id })}
              >
                {THEMES[id].name}
              </button>
            ))}
          </div>
        </div>

        <div className="section">
          <h2>Reveal</h2>
          <div className="reveal-row">
            {(["hold", "cascade"] as RevealMode[]).map((mode) => (
              <button
                key={mode}
                className={`chip ${reel.reveal === mode ? "active" : ""}`}
                onClick={() => patch({ reveal: mode })}
              >
                {mode === "hold" ? "All at once" : "Line by line"}
              </button>
            ))}
          </div>
        </div>
      </aside>

      <main className="stage">
        <div className="phone">
          <div className="bezel">
            <canvas
              ref={canvasRef}
              width={CANVAS_W}
              height={CANVAS_H}
              aria-label="Reel preview"
            />
          </div>
          <div className="progress" aria-hidden="true">
            <span
              style={{
                width: `${(Math.min(time, reel.durationSec) / reel.durationSec) * 100}%`,
              }}
            />
          </div>
          <div className="time">{clock}</div>
          <div className="controls">
            <button className="primary" onClick={() => setPlaying((p) => !p)}>
              {playing ? "Pause" : "Play"}
            </button>
            <button
              className="ghost"
              onClick={() => {
                setPlaying(false);
                setTime(0);
              }}
            >
              Restart
            </button>
            <button className="ghost" onClick={() => void onPng()}>
              Save PNG
            </button>
            <button
              className="primary"
              onClick={() => void onExport()}
              disabled={exporting}
            >
              {exporting
                ? `Rendering ${Math.round(progress * 100)}%`
                : "Download video"}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
