export type AmbientHandle = {
  stream: MediaStream;
  stop: () => void;
};

const ROOTS = [
  65.41, 69.3, 73.42, 77.78, 82.41, 87.31, 92.5, 98.0, 103.83, 110.0,
];

const CHORDS: number[][] = [
  [1, 5 / 4, 3 / 2, 15 / 8],
  [1, 9 / 8, 5 / 4, 3 / 2],
  [1, 9 / 8, 4 / 3, 3 / 2],
  [1, 6 / 5, 3 / 2, 5 / 3],
  [1, 5 / 4, 3 / 2, 5 / 3],
  [1, 6 / 5, 3 / 2, 9 / 5],
  [1, 9 / 8, 3 / 2, 2],
  [1, 5 / 4, 3 / 2, 9 / 4],
];

const PARTIAL_GAIN = [0.24, 0.16, 0.12, 0.08];

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
  detune: number;
  lfoDepth: number;
} {
  const h = hashSeed(seed);
  return {
    root: ROOTS[h % ROOTS.length],
    chord: CHORDS[(h >>> 4) % CHORDS.length],
    lfoHz: 0.035 + ((h >>> 8) % 80) / 1000,
    cutoff: 360 + ((h >>> 12) % 220),
    detune: 3 + ((h >>> 16) % 6),
    lfoDepth: 0.1 + ((h >>> 20) % 8) / 100,
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
  const master = ctx.createGain();
  master.gain.value = 0.07;
  master.connect(dest);
  if (preview) master.connect(ctx.destination);

  const params = padParams(seed);
  const filter = ctx.createBiquadFilter();
  filter.type = "lowpass";
  filter.frequency.value = params.cutoff;
  filter.Q.value = 0.5;
  filter.connect(master);

  const oscs: OscillatorNode[] = [];
  params.chord.forEach((ratio, index) => {
    const freq = params.root * ratio;
    const gain = ctx.createGain();
    gain.gain.value = PARTIAL_GAIN[index] ?? 0.08;
    gain.connect(filter);
    for (const detune of [-params.detune, params.detune]) {
      const osc = ctx.createOscillator();
      osc.type = "sine";
      osc.frequency.value = freq;
      osc.detune.value = detune;
      osc.connect(gain);
      osc.start();
      oscs.push(osc);
    }
  });

  const lfo = ctx.createOscillator();
  lfo.frequency.value = params.lfoHz;
  const lfoGain = ctx.createGain();
  lfoGain.gain.value = 0.07 * params.lfoDepth;
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
