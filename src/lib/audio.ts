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

const PARTIAL_GAIN = [0.24, 0.11, 0.06];
const MASTER = 0.11;
const FADE_SEC = 2.4;

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
  breathHz: number;
  pulseHz: number;
  filterLfo: number;
  prog: number[];
} {
  const h = hashSeed(seed);
  return {
    root: ROOTS[h % ROOTS.length],
    chord: CHORDS[(h >>> 4) % CHORDS.length],
    lfoHz: 0.08 + ((h >>> 8) % 50) / 1000,
    cutoff: 190 + ((h >>> 12) % 90),
    lfoDepth: 0.12 + ((h >>> 20) % 8) / 100,
    breathHz: 0.11 + ((h >>> 16) % 6) / 100,
    pulseHz: 0.48 + ((h >>> 18) % 8) / 100,
    filterLfo: 0.028 + ((h >>> 10) % 12) / 1000,
    prog: [0, 1, 2, 3].map((i) => (h >>> (i * 3)) % CHORDS.length),
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
  const params = padParams(seed);

  const master = ctx.createGain();
  master.gain.setValueAtTime(0, now);
  master.gain.linearRampToValueAtTime(MASTER, now + FADE_SEC);
  master.connect(dest);
  if (preview) master.connect(ctx.destination);

  const filterA = ctx.createBiquadFilter();
  filterA.type = "lowpass";
  filterA.frequency.value = params.cutoff;
  filterA.Q.value = 0.35;
  const filterB = ctx.createBiquadFilter();
  filterB.type = "lowpass";
  filterB.frequency.value = params.cutoff + 40;
  filterB.Q.value = 0.3;
  filterA.connect(filterB);
  filterB.connect(master);

  const oscs: OscillatorNode[] = [];

  const startChord = (ratios: number[], at: number, hold: number) => {
    ratios.forEach((ratio, index) => {
      const osc = ctx.createOscillator();
      osc.type = "sine";
      osc.frequency.value = params.root * ratio;
      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0, at);
      gain.gain.linearRampToValueAtTime(PARTIAL_GAIN[index] ?? 0.05, at + 1.6);
      gain.gain.setValueAtTime(PARTIAL_GAIN[index] ?? 0.05, at + hold - 1.8);
      gain.gain.linearRampToValueAtTime(0, at + hold);
      const pan = ctx.createStereoPanner();
      pan.pan.value = index === 0 ? 0 : index === 1 ? -0.32 : 0.32;
      osc.connect(gain);
      gain.connect(pan);
      pan.connect(filterA);
      osc.start(at);
      osc.stop(at + hold + 0.05);
      oscs.push(osc);
    });
  };

  const seg = 15;
  for (let i = 0; i < 8; i++) {
    const chord = CHORDS[params.prog[i % params.prog.length]];
    startChord(chord, now + i * (seg - 2.2), seg);
  }

  const breath = ctx.createOscillator();
  breath.frequency.value = params.breathHz;
  const breathGain = ctx.createGain();
  breathGain.gain.value = MASTER * 0.22;
  breath.connect(breathGain);
  breathGain.connect(master.gain);
  breath.start();
  oscs.push(breath);

  const lfo = ctx.createOscillator();
  lfo.frequency.value = params.lfoHz;
  const lfoGain = ctx.createGain();
  lfoGain.gain.value = MASTER * params.lfoDepth;
  lfo.connect(lfoGain);
  lfoGain.connect(master.gain);
  lfo.start();
  oscs.push(lfo);

  const filtLfo = ctx.createOscillator();
  filtLfo.frequency.value = params.filterLfo;
  const filtDepth = ctx.createGain();
  filtDepth.gain.value = 70;
  filtLfo.connect(filtDepth);
  filtDepth.connect(filterA.frequency);
  filtLfo.start();
  oscs.push(filtLfo);

  const pulse = ctx.createOscillator();
  pulse.type = "sine";
  pulse.frequency.value = params.root;
  const pulseGain = ctx.createGain();
  pulseGain.gain.value = 0.035;
  const pulseLfo = ctx.createOscillator();
  pulseLfo.frequency.value = params.pulseHz;
  const pulseDepth = ctx.createGain();
  pulseDepth.gain.value = 0.03;
  pulseLfo.connect(pulseDepth);
  pulseDepth.connect(pulseGain.gain);
  pulse.connect(pulseGain);
  pulseGain.connect(filterA);
  pulse.start();
  pulseLfo.start();
  oscs.push(pulse, pulseLfo);

  const shimmer = ctx.createOscillator();
  shimmer.type = "sine";
  shimmer.frequency.value = params.root * 3;
  const shimGain = ctx.createGain();
  shimGain.gain.value = 0.02;
  const shimLfo = ctx.createOscillator();
  shimLfo.frequency.value = 0.19;
  const shimDepth = ctx.createGain();
  shimDepth.gain.value = 0.016;
  shimLfo.connect(shimDepth);
  shimDepth.connect(shimGain.gain);
  const shimPan = ctx.createStereoPanner();
  shimPan.pan.value = 0.28;
  shimmer.connect(shimGain);
  shimGain.connect(shimPan);
  shimPan.connect(filterA);
  shimmer.start();
  shimLfo.start();
  oscs.push(shimmer, shimLfo);

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
