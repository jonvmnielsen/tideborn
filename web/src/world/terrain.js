// The island heightfield: shore in the south, forest belt in the middle,
// a terraced ridge in the north. Rendered smooth with the textured ground material.
import * as THREE from 'three';
import { makeNoise, smoothstep } from '../noise.js';

export const SIZE = 520;   // meters, square, centered on 0
export const CELL = 2.5;   // grid spacing
export const SEA = 0;

export class Terrain {
  constructor(seed = 7) {
    this.noise = makeNoise(seed);
    this.N = Math.round(SIZE / CELL);
    this.min = -SIZE / 2;
    const n = this.N + 1;
    this.h = new Float32Array(n * n);
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        this.h[j * n + i] = this.shape(this.min + i * CELL, this.min + j * CELL);
      }
    }
  }

  // --- Bands, used by flora and colors -----------------------------------
  northness(z) { return smoothstep(-35, -125, z); }
  landMask(x, z) {
    const { fbm } = this.noise;
    const wx = x + 28 * fbm(x * 0.006, z * 0.006, 3);
    const wz = z + 28 * fbm(x * 0.006 + 40, z * 0.006 + 40, 3);
    const r = Math.hypot(wx, wz * 0.92);
    return smoothstep(215, 150, r);
  }
  forestMask(x, z) {
    const { fbm } = this.noise;
    const belt = smoothstep(150, 105, z) * smoothstep(-105, -55, z); // middle of the island
    return belt * (0.55 + 0.9 * fbm(x * 0.009 + 100, z * 0.009 - 30, 4));
  }

  shape(x, z) {
    const { fbm, ridged } = this.noise;
    const land = this.landMask(x, z);
    let h = land * (4 + 9 * (fbm(x * 0.011, z * 0.011, 4) * 0.5 + 0.5));

    // Northern ridge with terraced cliffs.
    const nT = this.northness(z) * land;
    if (nT > 0) {
      let r = nT * (16 + 22 * ridged(x * 0.008 + 7, z * 0.008 + 3, 4));
      const step = 6.5;
      const t = r / step, f = t - Math.floor(t);
      const terr = (Math.floor(t) + smoothstep(0.2, 0.8, f)) * step;
      r = r * 0.35 + terr * 0.65;
      h += r;
    }
    // Forest rise in the middle of the island (giant tree sits here).
    const fr = Math.hypot(x - this.riseX, z - this.riseZ);
    h += 7 * Math.exp(-(fr * fr) / (2 * 26 * 26)) * land;
    // The landing cove in the south.
    const cv = Math.hypot((x - 4) * 0.8, z - 168);
    h -= 8 * Math.exp(-(cv * cv) / (2 * 30 * 30));

    h -= 3;
    h += (1 - land) * -7;
    // Flatter beaches around the waterline.
    const beach = smoothstep(-2.5, 0.8, h) * (1 - smoothstep(0.8, 4.2, h));
    h -= beach * 1.1;
    return h;
  }

  get riseX() { return -14; }
  get riseZ() { return 6; }

  // Height on the actual triangulated surface (matches the rendered mesh).
  heightAt(x, z) {
    const n = this.N + 1;
    const fx = (x - this.min) / CELL, fz = (z - this.min) / CELL;
    if (fx < 0 || fz < 0 || fx >= this.N || fz >= this.N) return -12;
    const i = Math.floor(fx), j = Math.floor(fz);
    const u = fx - i, v = fz - j;
    const h = this.h;
    const a = h[j * n + i], b = h[j * n + i + 1], c = h[(j + 1) * n + i], d = h[(j + 1) * n + i + 1];
    // Same diagonal split as the mesh: (a, c, b) and (b, c, d)
    if (u + v <= 1) return a + (b - a) * u + (c - a) * v;
    return d + (c - d) * (1 - u) + (b - d) * (1 - v);
  }

  slopeAt(x, z) {
    const e = 1.0;
    const dx = this.heightAt(x + e, z) - this.heightAt(x - e, z);
    const dz = this.heightAt(x, z + e) - this.heightAt(x, z - e);
    return Math.atan(Math.hypot(dx, dz) / (2 * e));
  }

  biomeAt(x, z) {
    const h = this.heightAt(x, z);
    if (h < 2.2) return 'shore';
    if (this.northness(z) > 0.45 && h > 12) return 'ridge';
    if (this.forestMask(x, z) > 0.62) return 'forest';
    return 'meadow';
  }

  // Smooth indexed heightfield. Each vertex carries "splat" weights for the ground material
  // (world/ground.js): x = sand, y = grass, z = forest floor, w = rock.
  buildMesh(material) {
    const n = this.N + 1;
    const pos = new Float32Array(n * n * 3);
    const splat = new Float32Array(n * n * 4);
    const { noise } = this.noise;
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        const k = j * n + i;
        const x = this.min + i * CELL, z = this.min + j * CELL, h = this.h[k];
        pos[k * 3] = x; pos[k * 3 + 1] = h; pos[k * 3 + 2] = z;
        const hx = this.h[j * n + Math.min(n - 1, i + 1)] - this.h[j * n + Math.max(0, i - 1)];
        const hz = this.h[Math.min(n - 1, j + 1) * n + i] - this.h[Math.max(0, j - 1) * n + i];
        const slope = Math.atan(Math.hypot(hx, hz) / (2 * CELL));
        const n1 = noise(x * 0.05, z * 0.05), n2 = noise(x * 0.23 + 5, z * 0.23 - 3);
        const sand = 1 - smoothstep(1.3, 2.5, h + n1 * 0.8);
        let rock = smoothstep(0.5, 0.78, slope + n2 * 0.08);
        if (this.northness(z) > 0.3 && h > 12) rock = Math.max(rock, 0.3 + 0.35 * (n1 * 0.5 + 0.5));
        const forest = smoothstep(0.45, 0.78, this.forestMask(x, z) + n2 * 0.08);
        const r = rock * (1 - sand);
        const f = forest * (1 - sand) * (1 - r);
        const g = (1 - sand) * (1 - r) * (1 - forest);
        const sum = sand + r + f + g || 1;
        splat.set([sand / sum, g / sum, f / sum, r / sum], k * 4);
      }
    }
    const idx = new Uint32Array(this.N * this.N * 6);
    let o = 0;
    for (let j = 0; j < this.N; j++) {
      for (let i = 0; i < this.N; i++) {
        const a = j * n + i, b = a + 1, c = a + n, d = c + 1;
        // Same diagonal split as heightAt(): (a, c, b) and (b, c, d)
        idx.set([a, c, b, b, c, d], o);
        o += 6;
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('splat', new THREE.BufferAttribute(splat, 4));
    geo.setIndex(new THREE.BufferAttribute(idx, 1));
    geo.computeVertexNormals();
    geo.computeBoundingSphere();
    const mesh = new THREE.Mesh(geo, material);
    mesh.receiveShadow = true;
    mesh.name = 'terrain';
    return mesh;
  }

  // Distance (meters) from each water texel to the nearest land, for the ocean shader.
  distanceField(res = 256, margin = 10) {
    const minX = this.min - margin, size = SIZE + margin * 2, cell = size / res;
    const INF = 1e9;
    const d = new Float32Array(res * res);
    for (let j = 0; j < res; j++) for (let i = 0; i < res; i++) {
      d[j * res + i] = this.heightAt(minX + (i + 0.5) * cell, minX + (j + 0.5) * cell) > SEA ? 0 : INF;
    }
    const a = 1, b = Math.SQRT2;
    for (let j = 0; j < res; j++) for (let i = 0; i < res; i++) {
      let v = d[j * res + i];
      if (i > 0) v = Math.min(v, d[j * res + i - 1] + a);
      if (j > 0) {
        v = Math.min(v, d[(j - 1) * res + i] + a);
        if (i > 0) v = Math.min(v, d[(j - 1) * res + i - 1] + b);
        if (i < res - 1) v = Math.min(v, d[(j - 1) * res + i + 1] + b);
      }
      d[j * res + i] = v;
    }
    for (let j = res - 1; j >= 0; j--) for (let i = res - 1; i >= 0; i--) {
      let v = d[j * res + i];
      if (i < res - 1) v = Math.min(v, d[j * res + i + 1] + a);
      if (j < res - 1) {
        v = Math.min(v, d[(j + 1) * res + i] + a);
        if (i < res - 1) v = Math.min(v, d[(j + 1) * res + i + 1] + b);
        if (i > 0) v = Math.min(v, d[(j + 1) * res + i - 1] + b);
      }
      d[j * res + i] = v;
    }
    const maxD = 24;
    const bytes = new Uint8Array(res * res);
    for (let k = 0; k < bytes.length; k++) bytes[k] = Math.min(255, Math.round(((d[k] * cell) / maxD) * 255));
    const tex = new THREE.DataTexture(bytes, res, res, THREE.RedFormat, THREE.UnsignedByteType);
    tex.magFilter = tex.minFilter = THREE.LinearFilter;
    tex.needsUpdate = true;
    return { tex, minX, size, maxD };
  }
}
