// Pointy-top hex grid in axial coordinates (q, r), sized from the KayKit tile itself.
import * as THREE from 'three';

export const DIRS = [
  [1, 0], [1, -1], [0, -1], [-1, 0], [-1, 1], [0, 1],
];

export const key = (q, r) => `${q},${r}`;

export class HexGrid {
  // W = flat-to-flat width (x), H = corner-to-corner depth (z)
  constructor(W, H) {
    this.W = W;
    this.H = H;
  }
  toWorld(q, r) {
    return { x: this.W * (q + r / 2), z: 0.75 * this.H * r };
  }
  fromWorld(x, z) {
    const r = z / (0.75 * this.H);
    const q = x / this.W - r / 2;
    return axialRound(q, r);
  }
  dirVector(i) {
    const [dq, dr] = DIRS[i];
    return this.toWorld(dq, dr);
  }
}

export function axialRound(q, r) {
  const s = -q - r;
  let rq = Math.round(q), rr = Math.round(r), rs = Math.round(s);
  const dq = Math.abs(rq - q), dr = Math.abs(rr - r), ds = Math.abs(rs - s);
  if (dq > dr && dq > ds) rq = -rr - rs;
  else if (dr > ds) rr = -rq - rs;
  return { q: rq, r: rr };
}

export function hexDistance(q1, r1, q2 = 0, r2 = 0) {
  const dq = q1 - q2, dr = r1 - r2;
  return (Math.abs(dq) + Math.abs(dr) + Math.abs(dq + dr)) / 2;
}

// Bakes a height lookup for one tile model at one rotation by raycasting it from above.
// Samples a square grid covering the hex; misses are pulled toward the center until they hit.
export class TileHeights {
  constructor(object, extent, n = 15) {
    this.n = n;
    this.extent = extent; // half-size of the sampled square
    this.h = new Float32Array(n * n);
    const ray = new THREE.Raycaster();
    const down = new THREE.Vector3(0, -1, 0);
    const origin = new THREE.Vector3();
    object.updateMatrixWorld(true);
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        const x = (i / (n - 1) * 2 - 1) * extent;
        const z = (j / (n - 1) * 2 - 1) * extent;
        let y = -Infinity;
        for (let shrink = 1; shrink > 0.5 && y === -Infinity; shrink -= 0.05) {
          origin.set(x * shrink, 100, z * shrink);
          ray.set(origin, down);
          const hit = ray.intersectObject(object, true)[0];
          if (hit) y = hit.point.y;
        }
        this.h[j * n + i] = y;
      }
    }
    let lowest = Infinity;
    for (const v of this.h) if (v !== -Infinity) lowest = Math.min(lowest, v);
    for (let k = 0; k < this.h.length; k++) if (this.h[k] === -Infinity) this.h[k] = lowest;
  }
  // Local (tile-centered) coordinates.
  at(x, z) {
    const n = this.n;
    const fx = (x / this.extent * 0.5 + 0.5) * (n - 1);
    const fz = (z / this.extent * 0.5 + 0.5) * (n - 1);
    const i = Math.max(0, Math.min(n - 2, Math.floor(fx)));
    const j = Math.max(0, Math.min(n - 2, Math.floor(fz)));
    const tx = Math.max(0, Math.min(1, fx - i));
    const tz = Math.max(0, Math.min(1, fz - j));
    const h = this.h;
    const a = h[j * n + i], b = h[j * n + i + 1], c = h[(j + 1) * n + i], d = h[(j + 1) * n + i + 1];
    return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz;
  }
}
