// The island heightfield: shore in the south, forest belt in the middle,
// a terraced ridge in the north. Low-poly flat-shaded to sit with the KayKit art.
import * as THREE from 'three';
import { makeNoise, smoothstep } from '../noise.js';

export const SIZE = 520;   // meters, square, centered on 0
export const CELL = 2.5;   // grid spacing
export const SEA = 0;

const C = {
  sandWet: new THREE.Color('#cdb27a'),
  sand: new THREE.Color('#ead39b'),
  meadow: new THREE.Color('#9cbd4c'),
  meadow2: new THREE.Color('#a9c556'),
  forest: new THREE.Color('#6c9a3a'),
  forest2: new THREE.Color('#5f8d36'),
  scrub: new THREE.Color('#b5b46c'),
  rock: new THREE.Color('#948d80'),
  rockDark: new THREE.Color('#7d776c'),
  rockPale: new THREE.Color('#b2ab9b'),
  seabed: new THREE.Color('#c7b27e'),
};

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

  buildMesh() {
    const n = this.N + 1;
    const pos = [], col = [];
    const tri = new THREE.Triangle();
    const nrm = new THREE.Vector3();
    const color = new THREE.Color();
    const A = new THREE.Vector3(), B = new THREE.Vector3(), Cc = new THREE.Vector3();
    const { noise } = this.noise;
    const pushTri = (ax, az, bx, bz, cx, cz, ha, hb, hc) => {
      if (ha < -6 && hb < -6 && hc < -6) return; // deep water is covered by the ocean
      A.set(ax, ha, az); B.set(bx, hb, bz); Cc.set(cx, hc, cz);
      tri.set(A, B, Cc).getNormal(nrm);
      const mx = (ax + bx + cx) / 3, mz = (az + bz + cz) / 3, mh = (ha + hb + hc) / 3;
      const slope = Math.acos(Math.min(1, Math.abs(nrm.y)));
      const jitter = noise(mx * 0.35, mz * 0.35) * 0.5 + noise(mx * 2.1, mz * 2.1) * 0.5;
      if (mh < -0.4) color.copy(C.seabed);
      else if (mh < 0.9) color.copy(C.sandWet).lerp(C.sand, smoothstep(-0.4, 0.9, mh));
      else if (mh < 2.4 && slope < 0.5) color.copy(C.sand).lerp(C.meadow, smoothstep(1.8, 2.4, mh));
      else if (slope > 0.62) color.copy(this.northness(mz) > 0.3 ? C.rockPale : C.rock).lerp(C.rockDark, jitter * 0.5 + 0.25);
      else if (this.northness(mz) > 0.45 && mh > 12) color.copy(C.scrub).lerp(C.rockPale, smoothstep(0.35, 0.6, slope));
      else {
        const f = smoothstep(0.45, 0.75, this.forestMask(mx, mz));
        color.copy(jitter > 0 ? C.meadow : C.meadow2).lerp(jitter > 0 ? C.forest : C.forest2, f);
        if (slope > 0.42) color.lerp(C.rock, smoothstep(0.42, 0.62, slope) * 0.7);
      }
      color.offsetHSL(0, 0, jitter * 0.025);
      pos.push(A.x, A.y, A.z, B.x, B.y, B.z, Cc.x, Cc.y, Cc.z);
      for (let k = 0; k < 3; k++) col.push(color.r, color.g, color.b);
    };
    for (let j = 0; j < this.N; j++) {
      for (let i = 0; i < this.N; i++) {
        const x0 = this.min + i * CELL, z0 = this.min + j * CELL, x1 = x0 + CELL, z1 = z0 + CELL;
        const a = this.h[j * n + i], b = this.h[j * n + i + 1], c = this.h[(j + 1) * n + i], d = this.h[(j + 1) * n + i + 1];
        pushTri(x0, z0, x0, z1, x1, z0, a, c, b);
        pushTri(x1, z0, x0, z1, x1, z1, b, c, d);
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    geo.computeVertexNormals();
    geo.computeBoundingSphere();
    const mat = new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true, roughness: 0.95, metalness: 0 });
    const mesh = new THREE.Mesh(geo, mat);
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
