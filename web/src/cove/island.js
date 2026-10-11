// The test cove: a crescent beach facing south (+z is the sea), a shallow lagoon, jungle rising
// to a hill inland, and rocky headlands at both ends. Heights in metres, sea level 0.
import * as THREE from 'three';
import { makeNoise, smoothstep } from '../noise.js';

export const SIZE = 760;

export class Island {
  constructor({ cell = 2 } = {}) {
    this.noise = makeNoise(23);
    this.cell = cell;
    this.N = Math.round(SIZE / cell);
    this.min = -SIZE / 2;
    const n = this.N + 1;
    this.h = new Float32Array(n * n);
    for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) this.h[j * n + i] = this.shape(this.min + i * cell, this.min + j * cell);
  }

  // z of the waterline at x: the beach bows inland in the middle, headlands reach out at the ends.
  shoreZ(x) {
    const { fbm } = this.noise;
    return 40 + 75 * smoothstep(55, 175, Math.abs(x)) + 7 * fbm(x * 0.012, 3.1, 3);
  }

  // How far inland from the waterline (negative = out at sea).
  inland(x, z) {
    return this.shoreZ(x) - z;
  }

  headland(x) {
    return smoothstep(95, 165, Math.abs(x));
  }

  shape(x, z) {
    const { fbm, ridged } = this.noise;
    const d = this.inland(x, z);
    const head = this.headland(x);
    let h;
    if (d < 0) {
      // Lagoon floor: very shallow first, then a drop-off to the reef edge and deep water.
      const o = -d;
      h = -0.25 - o * 0.045 - Math.max(0, o - 60) * 0.12 - Math.max(0, o - 110) * 0.25;
      h += 0.35 * fbm(x * 0.05, z * 0.05, 3);
      h = Math.max(h, -24);
    } else {
      // Beach rises gently, then the jungle climbs toward the hill.
      const beach = Math.min(d, 32) * 0.065;
      const climb = Math.max(0, d - 32);
      h = beach + climb * 0.12 + Math.pow(climb / 120, 2) * 14;
      h += (2.5 + climb * 0.04) * fbm(x * 0.018 + 5, z * 0.018, 4) * smoothstep(25, 60, d);
    }
    // Headlands: rocky ridges that stand up out of the water.
    if (head > 0) {
      const r = ridged(x * 0.02 + 3, z * 0.02 - 2, 3);
      h = Math.max(h, head * (4 + 9 * r) * smoothstep(-55, 15, d) - 2);
    }
    // It is an island: beyond its coast the land falls away into deep water on every side.
    const ex = x / 255, ez = (z + 60) / 235;
    const rr = Math.hypot(ex, ez) * (1 + 0.12 * fbm(x * 0.008 + 9, z * 0.008, 3));
    h = THREE.MathUtils.lerp(h, -32, smoothstep(0.92, 1.35, rr));
    return h;
  }

  heightAt(x, z) {
    const n = this.N + 1, c = this.cell;
    const fx = (x - this.min) / c, fz = (z - this.min) / c;
    if (fx < 0 || fz < 0 || fx >= this.N || fz >= this.N) return -20;
    const i = Math.floor(fx), j = Math.floor(fz);
    const u = fx - i, v = fz - j, h = this.h;
    const a = h[j * n + i], b = h[j * n + i + 1], cc = h[(j + 1) * n + i], d = h[(j + 1) * n + i + 1];
    if (u + v <= 1) return a + (b - a) * u + (cc - a) * v;
    return d + (cc - d) * (1 - u) + (b - d) * (1 - v);
  }

  slopeAt(x, z) {
    const e = 1;
    const dx = this.heightAt(x + e, z) - this.heightAt(x - e, z);
    const dz = this.heightAt(x, z + e) - this.heightAt(x, z - e);
    return Math.atan(Math.hypot(dx, dz) / (2 * e));
  }

  // Splat weights: x = sand, y = grass, z = jungle floor, w = rock.
  buildMesh(material) {
    const n = this.N + 1, c = this.cell;
    const pos = new Float32Array(n * n * 3);
    const splat = new Float32Array(n * n * 4);
    const { noise } = this.noise;
    for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
      const k = j * n + i;
      const x = this.min + i * c, z = this.min + j * c, h = this.h[k];
      pos.set([x, h, z], k * 3);
      const hx = this.h[j * n + Math.min(n - 1, i + 1)] - this.h[j * n + Math.max(0, i - 1)];
      const hz = this.h[Math.min(n - 1, j + 1) * n + i] - this.h[Math.max(0, j - 1) * n + i];
      const slope = Math.atan(Math.hypot(hx, hz) / (2 * c));
      const d = this.inland(x, z);
      const n1 = noise(x * 0.06, z * 0.06), n2 = noise(x * 0.21 + 7, z * 0.21);
      // Sand on the cove beach, and on any low ground at the water's edge around the island.
      const sand = Math.max(1 - smoothstep(26, 40, d + n1 * 7), 1 - smoothstep(1.2, 2.6, h + n1 * 0.6));
      let rock = smoothstep(0.55, 0.85, slope + n2 * 0.08);
      rock = Math.max(rock, this.headland(x) * smoothstep(1.5, 4, h) * 0.8);
      const jungle = smoothstep(38, 60, d + n2 * 9);
      const r = rock * (1 - sand * 0.6);
      const sw = sand * (1 - r);
      const f = jungle * (1 - sw) * (1 - r);
      const g = (1 - sw) * (1 - r) * (1 - jungle);
      const sum = sw + r + f + g || 1;
      splat.set([sw / sum, g / sum, f / sum, r / sum], k * 4);
    }
    const idx = new Uint32Array(this.N * this.N * 6);
    let o = 0;
    for (let j = 0; j < this.N; j++) for (let i = 0; i < this.N; i++) {
      const a = j * n + i, b = a + 1, cc = a + n, d = cc + 1;
      idx.set([a, cc, b, b, cc, d], o);
      o += 6;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('splat', new THREE.BufferAttribute(splat, 4));
    geo.setIndex(new THREE.BufferAttribute(idx, 1));
    geo.computeVertexNormals();
    geo.computeBoundingSphere();
    const mesh = new THREE.Mesh(geo, material);
    mesh.receiveShadow = true;
    mesh.name = 'island';
    return mesh;
  }

  // Water depth below sea level for the ocean shader: −landMax..maxDepth m → 0..255, so ground
  // just above the waterline (where the swash runs up) is known too.
  depthTexture(res = 512, maxDepth = 14, landMax = 2) {
    const bytes = new Uint8Array(res * res);
    for (let j = 0; j < res; j++) for (let i = 0; i < res; i++) {
      const x = this.min + (i + 0.5) / res * SIZE, z = this.min + (j + 0.5) / res * SIZE;
      bytes[j * res + i] = Math.round(THREE.MathUtils.clamp((-this.heightAt(x, z) + landMax) / (maxDepth + landMax), 0, 1) * 255);
    }
    const tex = new THREE.DataTexture(bytes, res, res, THREE.RedFormat, THREE.UnsignedByteType);
    tex.magFilter = tex.minFilter = THREE.LinearFilter;
    tex.needsUpdate = true;
    return { tex, min: this.min, size: SIZE, maxDepth, landMax };
  }
}
