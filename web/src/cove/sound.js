// Ambient sound for the cove: surf made from filtered noise (slow swells), the library's
// forest-day and soft-wind loops (Sonniss GDC, via game-assets) kept low under it, and
// synthesized tropical birds — whistles, trills, parrot squawks and gull cries — at random.
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
  birds(ctx, master);
}

function birds(ctx, out) {
  const bus = ctx.createGain();
  bus.gain.value = 0.5;
  bus.connect(out);
  const voice = (pan, gain) => {
    const g = ctx.createGain();
    g.gain.value = 0;
    const p = ctx.createStereoPanner ? ctx.createStereoPanner() : null;
    if (p) { p.pan.value = pan; g.connect(p).connect(bus); } else g.connect(bus);
    return g;
  };
  const tone = (t0, dur, f0, f1, vol, pan, type = 'sine', vib = 0) => {
    const o = ctx.createOscillator();
    o.type = type;
    o.frequency.setValueAtTime(f0, t0);
    o.frequency.exponentialRampToValueAtTime(f1, t0 + dur);
    if (vib) {
      const l = ctx.createOscillator(), lg = ctx.createGain();
      l.frequency.value = vib; lg.gain.value = f0 * 0.04;
      l.connect(lg).connect(o.frequency); l.start(t0); l.stop(t0 + dur);
    }
    const g = voice(pan, 0);
    g.gain.setValueAtTime(0, t0);
    g.gain.linearRampToValueAtTime(vol, t0 + Math.min(0.03, dur * 0.3));
    g.gain.exponentialRampToValueAtTime(0.0005, t0 + dur);
    if (type !== 'sine') { const bp = ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = f0 * 1.5; bp.Q.value = 2; o.connect(bp).connect(g); } else o.connect(g);
    o.start(t0); o.stop(t0 + dur + 0.05);
  };
  const calls = [
    // Rising whistle, answered.
    (t, pan) => { tone(t, 0.35, 1100, 1900, 0.05, pan); tone(t + 0.5, 0.35, 1150, 2000, 0.04, pan); },
    // Fast trill.
    (t, pan) => { const f = 2600 + Math.random() * 1200; for (let i = 0; i < 6 + Math.random() * 6; i++) tone(t + i * 0.07, 0.05, f, f * 1.25, 0.03, pan); },
    // Falling coo-whoop.
    (t, pan) => { tone(t, 0.45, 900, 520, 0.05, pan); tone(t + 0.55, 0.3, 700, 1100, 0.04, pan); },
    // Parrot squawk.
    (t, pan) => { tone(t, 0.22, 700, 520, 0.06, pan, 'sawtooth', 35); tone(t + 0.3, 0.18, 760, 600, 0.05, pan, 'sawtooth', 40); },
    // Gull cry: a few descending calls.
    (t, pan) => { for (let i = 0; i < 3; i++) tone(t + i * 0.32, 0.26, 1500 - i * 60, 950, 0.035, pan, 'triangle', 9); },
    // Two-note hoot.
    (t, pan) => { tone(t, 0.25, 620, 600, 0.05, pan); tone(t + 0.35, 0.4, 520, 500, 0.05, pan); },
  ];
  const next = () => {
    const pan = Math.random() * 1.6 - 0.8;
    calls[Math.floor(Math.random() * calls.length)](ctx.currentTime + 0.05, pan);
    setTimeout(next, 900 + Math.random() * 3200);
  };
  next();
}
