// Ambient sound for the cove: surf made from filtered noise (slow swells), plus the library's
// forest-day and soft-wind loops (Sonniss GDC, via game-assets) kept low under it.
let started = false;

export async function startSound(base) {
  if (started) return;
  started = true;
  const AC = window.AudioContext || window.webkitAudioContext;
  if (!AC) return;
  const ctx = new AC();
  const master = ctx.createGain();
  master.gain.value = 0.8;
  master.connect(ctx.destination);

  // Surf: brown noise → low-pass, with a slow swell envelope and a hiss on each wave.
  const len = ctx.sampleRate * 4;
  const buf = ctx.createBuffer(2, len, ctx.sampleRate);
  for (let ch = 0; ch < 2; ch++) {
    const d = buf.getChannelData(ch);
    let last = 0;
    for (let i = 0; i < len; i++) { last = (last + 0.02 * (Math.random() * 2 - 1)) / 1.02; d[i] = last * 3.5; }
  }
  const noise = ctx.createBufferSource();
  noise.buffer = buf;
  noise.loop = true;
  const lp = ctx.createBiquadFilter();
  lp.type = 'lowpass';
  lp.frequency.value = 700;
  const swell = ctx.createGain();
  swell.gain.value = 0.35;
  noise.connect(lp).connect(swell).connect(master);
  noise.start();
  const lfo = ctx.createOscillator();
  lfo.frequency.value = 0.11;
  const lfoGain = ctx.createGain();
  lfoGain.gain.value = 0.22;
  lfo.connect(lfoGain).connect(swell.gain);
  const lfo2 = ctx.createGain();
  lfo2.gain.value = 500;
  lfo.connect(lfo2).connect(lp.frequency);
  lfo.start();

  for (const [file, vol] of [['jse-forest/forest_day.mp3', 0.22], ['ksl-countryside/wind_soft.mp3', 0.25]]) {
    try {
      const data = await (await fetch(`${base}/${file}`)).arrayBuffer();
      const b = await ctx.decodeAudioData(data);
      const src = ctx.createBufferSource();
      src.buffer = b;
      src.loop = true;
      const g = ctx.createGain();
      g.gain.value = vol;
      src.connect(g).connect(master);
      src.start();
    } catch {
      /* sound is optional */
    }
  }
}
