export type AmbientHandle = {
  stream: MediaStream;
  stop: () => void;
};

/** Low roots, A1 through E2. */
const ROOTS = [55.0, 58.27, 61.74, 65.41, 69.3, 73.42, 77.78, 82.41];

/** Soft triads and open fifths only. No 7ths, no high 9ths. */
const CHORDS: number[][] = [
  [1, 3 / 2],
  [1, 6 / 5, 3 / 2],
  [1, 5 / 4, 3 / 2],
  [1, 4 / 3],
  [1, 5 / 3],
  [1, 6 / 5, 8 / 5],
];

const PARTIAL_GAIN = [0.22, 0.09, 0.05];
const MASTER = 0.08;
const FADE_SEC = 2.8;

export function hashSeed(seed: string): number {
  let h = 2166136261;
  const text = seed || "facts-or-whacks";
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h >>> 0;
}

export function padParams(seed: string): {
  root: number;
  chord: number[];
  lfoHz: number;
  cutoff: number;
  lfoDepth: number;
} {
  const h = hashSeed(seed);
  return {
    root: ROOTS[h % ROOTS.length],
    chord: CHORDS[(h >>> 4) % CHORDS.length],
    lfoHz: 0.02 + ((h >>> 8) % 40) / 1000,
    cutoff: 150 + ((h >>> 12) % 70),
    lfoDepth: 0.03 + ((h >>> 20) % 4) / 100,
  };
}

export function ambientSeed(reel: {
  episode?: string;
  id?: string;
  title?: string;
}): string {
  return [reel.episode, reel.id, reel.title].filter(Boolean).join("-") || "custom";
}

export function createAmbient(preview: boolean, seed = "preview"): AmbientHandle {
  const ctx = new AudioContext();
  const dest = ctx.createMediaStreamDestination();
  const now = ctx.currentTime;

  const master = ctx.createGain();
  master.gain.setValueAtTime(0, now);
  master.gain.linearRampToValueAtTime(MASTER, now + FADE_SEC);
  master.connect(dest);
  if (preview) master.connect(ctx.destination);

  const params = padParams(seed);
  const filterA = ctx.createBiquadFilter();
  filterA.type = "lowpass";
  filterA.frequency.value = params.cutoff;
  filterA.Q.value = 0.3;
  const filterB = ctx.createBiquadFilter();
  filterB.type = "lowpass";
  filterB.frequency.value = params.cutoff;
  filterB.Q.value = 0.3;
  filterA.connect(filterB);
  filterB.connect(master);

  const oscs: OscillatorNode[] = [];
  params.chord.forEach((ratio, index) => {
    const gain = ctx.createGain();
    gain.gain.value = PARTIAL_GAIN[index] ?? 0.05;
    const pan = ctx.createStereoPanner();
    pan.pan.value = index === 0 ? 0 : index === 1 ? -0.25 : 0.25;
    gain.connect(pan);
    pan.connect(filterA);
    const osc = ctx.createOscillator();
    osc.type = "sine";
    osc.frequency.value = params.root * ratio;
    osc.connect(gain);
    osc.start();
    oscs.push(osc);
  });

  const lfo = ctx.createOscillator();
  lfo.frequency.value = params.lfoHz;
  const lfoGain = ctx.createGain();
  lfoGain.gain.value = MASTER * params.lfoDepth;
  lfo.connect(lfoGain);
  lfoGain.connect(master.gain);
  lfo.start();
  oscs.push(lfo);

  void ctx.resume();

  return {
    stream: dest.stream,
    stop: () => {
      for (const osc of oscs) {
        try {
          osc.stop();
        } catch {
          /* already stopped */
        }
      }
      void ctx.close();
    },
  };
}
