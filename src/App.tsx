import { useEffect, useMemo, useRef, useState } from "react";
import type { Fact, ReelContent, RevealMode, ThemeId } from "./types";
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

const STORAGE_KEY = "fact-nebula-reel-v1";

function loadSaved(): ReelContent | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as ReelContent;
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
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    drawFrame(ctx, reel, time);
  }, [reel, time, fontsReady]);

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

  const updateFact = (index: number, partial: Partial<Fact>) => {
    setReel((r) => ({
      ...r,
      facts: r.facts.map((f, i) => (i === index ? { ...f, ...partial } : f)),
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
      downloadBlob(blob, `${slugify(reel.name || reel.handle)}.webm`);
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
    downloadBlob(blob, `${slugify(reel.name || reel.handle)}.png`);
  }

  return (
    <div className="app">
      <aside className="editor">
        <div className="brand">
          <div className="brand-mark">✦</div>
          <div>
            <h1>Fact Nebula</h1>
            <p>15-second fact reels in the cosmic list format</p>
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

        <label className="field">
          <span className="field-label">Title</span>
          <textarea
            value={reel.title}
            onChange={(e) => patch({ title: e.target.value, id: "custom" })}
          />
          <span className="hint">
            Wrap a word in **asterisks** to paint it green. Use a line break to
            split the headline.
          </span>
        </label>

        <div className="section">
          <h2>Facts</h2>
          {reel.facts.map((fact, i) => (
            <div className="fact-card" key={i}>
              <div className="fact-top">
                <input
                  value={fact.label}
                  onChange={(e) => updateFact(i, { label: e.target.value })}
                  placeholder="Label"
                />
                <button
                  className="ghost danger"
                  onClick={() =>
                    setReel((r) => ({
                      ...r,
                      facts: r.facts.filter((_, idx) => idx !== i),
                      id: "custom",
                    }))
                  }
                  disabled={reel.facts.length <= 1}
                >
                  Remove
                </button>
              </div>
              <textarea
                value={fact.text}
                onChange={(e) => updateFact(i, { text: e.target.value })}
                placeholder="Statistic"
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
                  facts: [...r.facts, { label: "New", text: "Another fact." }],
                }))
              }
            >
              Add fact
            </button>
          </div>
        </div>

        <label className="field">
          <span className="field-label">Note</span>
          <textarea
            value={reel.note}
            onChange={(e) => patch({ note: e.target.value, id: "custom" })}
          />
        </label>

        <label className="field">
          <span className="field-label">Call to action</span>
          <textarea
            value={reel.cta}
            onChange={(e) => patch({ cta: e.target.value, id: "custom" })}
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
            max={30}
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
            <button className="ghost" onClick={onPng}>
              Save PNG
            </button>
            <button className="primary" onClick={onExport} disabled={exporting}>
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
