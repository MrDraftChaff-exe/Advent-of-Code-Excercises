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
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioRef = useRef<ReturnType<typeof createAmbient> | null>(null);

  useEffect(() => {
    loadReelFonts()
      .then(() => setFontsReady(true))
      .catch(() => setFontsReady(true));
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

  return (
    <div className="app">
      <aside className="editor">
        <div className="brand">
          <div className="brand-mark">?</div>
          <div>
            <h1>Facts or Whacks</h1>
            <p>Episode, photo, bullets, hashtags.</p>
          </div>
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
            Renders as <code>30. The End of Apartheid (1994)</code>. Wrap a word
            in **asterisks** to paint it green.
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
                ? `Exporting ${Math.round(progress * 100)}%`
                : "Export WebM"}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
