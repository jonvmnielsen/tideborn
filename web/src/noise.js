// Seeded 2D value noise + fBm, enough for terrain shaping.
export function makeNoise(seed = 1) {
  const perm = new Uint8Array(512);
  const p = new Uint8Array(256);
  for (let i = 0; i < 256; i++) p[i] = i;
  let s = seed >>> 0 || 1;
  for (let i = 255; i > 0; i--) {
    s = (s * 1664525 + 1013904223) >>> 0;
    const j = s % (i + 1);
    [p[i], p[j]] = [p[j], p[i]];
  }
  for (let i = 0; i < 512; i++) perm[i] = p[i & 255];
  const grad = new Float32Array(256);
  for (let i = 0; i < 256; i++) grad[i] = (perm[i] / 255) * 2 - 1;

  const fade = (t) => t * t * t * (t * (t * 6 - 15) + 10);
  const lerp = (a, b, t) => a + (b - a) * t;
  const h = (x, y) => grad[perm[(perm[x & 255] + y) & 511] & 255];

  function noise(x, y) {
    const xi = Math.floor(x), yi = Math.floor(y);
    const xf = x - xi, yf = y - yi;
    const u = fade(xf), v = fade(yf);
    return lerp(lerp(h(xi, yi), h(xi + 1, yi), u), lerp(h(xi, yi + 1), h(xi + 1, yi + 1), u), v);
  }
  function fbm(x, y, octaves = 4, lac = 2, gain = 0.5) {
    let a = 1, f = 1, sum = 0, norm = 0;
    for (let o = 0; o < octaves; o++) {
      sum += a * noise(x * f, y * f);
      norm += a;
      a *= gain;
      f *= lac;
    }
    return sum / norm;
  }
  function ridged(x, y, octaves = 4) {
    let a = 1, f = 1, sum = 0, norm = 0;
    for (let o = 0; o < octaves; o++) {
      sum += a * (1 - Math.abs(noise(x * f, y * f)));
      norm += a;
      a *= 0.5;
      f *= 2;
    }
    return sum / norm;
  }
  return { noise, fbm, ridged };
}

export const smoothstep = (e0, e1, x) => {
  const t = Math.max(0, Math.min(1, (x - e0) / (e1 - e0)));
  return t * t * (3 - 2 * t);
};
