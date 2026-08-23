export type AmbientHandle = {
  stream: MediaStream;
  stop: () => void;
};

export function createAmbient(preview: boolean): AmbientHandle {
  const ctx = new AudioContext();
  const dest = ctx.createMediaStreamDestination();
  const master = ctx.createGain();
  master.gain.value = 0.09;
  master.connect(dest);
  if (preview) master.connect(ctx.destination);

  const makePad = (freq: number, gain: number, type: OscillatorType) => {
    const osc = ctx.createOscillator();
    osc.type = type;
    osc.frequency.value = freq;
    const g = ctx.createGain();
    g.gain.value = gain;
    const filter = ctx.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.value = 680;
    osc.connect(g);
    g.connect(filter);
    filter.connect(master);
    osc.start();
    return osc;
  };

  const a = makePad(110, 0.28, "sine");
  const b = makePad(164.81, 0.16, "sine");
  const c = makePad(246.94, 0.07, "triangle");

  const lfo = ctx.createOscillator();
  lfo.frequency.value = 0.11;
  lfo.start();

  void ctx.resume();

  return {
    stream: dest.stream,
    stop: () => {
      try {
        a.stop();
        b.stop();
        c.stop();
        lfo.stop();
      } catch {
        /* already stopped */
      }
      void ctx.close();
    },
  };
}
