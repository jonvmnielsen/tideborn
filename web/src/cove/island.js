// The test cove: a crescent beach facing south (+z is the sea), a shallow lagoon, jungle rising
// inland to a smoking volcano, and rocky headlands at both ends. Heights in metres, sea level 0.
// Drawn as hard-faceted low poly with per-face colours (D-013); lava glows through an
// emissive vertex attribute.
import * as THREE from 'three';
import { makeNoise, smoothstep } from '../noise.js';

export const SIZE = 760;
export const VOLCANO = { x: 30, z: -215, peak: 150, base: 175, crater: 26, depth: 24 };
// Lava runs: direction from the crater (radians, atan2(dz, dx); +π/2 faces the beach), length in m.
const STREAMS = [[1.3, 105, 3.2], [1.85, 80, 2.6], [2.45, 120, 3.4], [0.55, 70, 2.4], [-2.4, 60, 2.6], [-0.6, 50, 2.2]];
const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));
const smax = (a, b, k) => { const h = Math.max(k - Math.abs(a - b), 0) / k; return Math.max(a, b) + h * h * k * 0.25; };

const COL = {
  sand: new THREE.Color('#efbd5e'), wetSand: new THREE.Color('#bf8c45'), seabed: new THREE.Color('#e2bc72'),
  grass: new THREE.Color('#8cae3e'), grassDry: new THREE.Color('#b3b24c'), jungle: new THREE.Color('#5b8c2c'), jungleDark: new THREE.Color('#4a7428'), litter: new THREE.Color('#8a6a36'), mossFloor: new THREE.Color('#86ad3a'),
  rock: new THREE.Color('#8b8369'), rockDark: new THREE.Color('#615b4b'), moss: new THREE.Color('#7f913a'),
  ash: new THREE.Color('#6d635a'), basalt: new THREE.Color('#3e3936'), crust: new THREE.Color('#2a2422'), lava: new THREE.Color('#ff6a1e'),
};

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
    // The volcano rises out of the jungle behind the cove.
    const v = this.volcano(x, z);
    if (v > 0) h = smax(h, v, 10);
    // It is an island: beyond its coast the land falls away into deep water on every side.
    const ex = x / 255, ez = (z + 60) / 235;
    const rr = Math.hypot(ex, ez) * (1 + 0.12 * fbm(x * 0.008 + 9, z * 0.008, 3));
    h = THREE.MathUtils.lerp(h, -32, smoothstep(0.92, 1.35, rr));
    return h;
  }

  // Stratovolcano: concave flanks scored by radial gullies, a crater bowl at the top.
  volcano(x, z) {
    const V = VOLCANO, dx = x - V.x, dz = z - V.z, d = Math.hypot(dx, dz);
    if (d > V.base) return 0;
    const a = Math.atan2(dz, dx), { fbm, ridged } = this.noise;
    let h;
    if (d < V.crater) h = V.peak - V.depth * (1 - (d / V.crater) ** 2) + 3 * smoothstep(V.crater * 0.7, V.crater, d);
    else h = (V.peak + 3) * Math.pow(1 - (d - V.crater) / (V.base - V.crater), 1.75);
    const out = smoothstep(V.crater + 2, V.crater + 25, d);
    const gully = ridged(a * 5 + 3, d * 0.012, 3);
    h -= out * (1 - d / V.base) * 9 * gully;
    h += out * 2.5 * fbm(x * 0.04, z * 0.04, 3);
    for (const [sa, len] of STREAMS) {
      const perp = d * wrap(a - sa - this.wiggle(d, sa));
      h -= 1.4 * Math.exp(-((perp / 4) ** 2)) * out * (1 - smoothstep(len * 0.8, len, d - V.crater));
    }
    return h;
  }

  wiggle(d, sa) { return 0.14 * Math.sin(d * 0.045 + sa * 3) + 0.06 * Math.sin(d * 0.13 + sa); }

  // 0..1: glowing lava (crater lake and the runs down the flanks); crust = cooled rock beside it.
  lavaAt(x, z) {
    const V = VOLCANO, dx = x - V.x, dz = z - V.z, d = Math.hypot(dx, dz);
    if (d > V.base) return { lava: 0, crust: 0 };
    if (d < V.crater * 0.72) return { lava: 1, crust: 1 };
    const a = Math.atan2(dz, dx);
    let lava = 0, crust = 0;
    for (const [sa, len, w] of STREAMS) {
      const perp = d * wrap(a - sa - this.wiggle(d, sa));
      const along = (d - V.crater * 0.9);
      if (along < 0 || along > len) continue;
      const fade = 1 - smoothstep(len * 0.6, len, along);
      lava = Math.max(lava, Math.exp(-((perp / w) ** 2)) * fade);
      crust = Math.max(crust, Math.exp(-((perp / (w * 3)) ** 2)) * (1 - smoothstep(len * 0.8, len * 1.15, along)));
    }
    return { lava: smoothstep(0.35, 0.8, lava), crust: Math.max(crust, 1 - smoothstep(V.crater * 0.72, V.crater * 1.1, d)) };
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

  colourAt(x, z, h, slope, n1, n2) {
    const d = this.inland(x, z), C = COL;
    const c = new THREE.Color();
    // Ground under water is sand (the sea shader tints it); dry sand above, darker where wet.
    const sandish = Math.max(1 - smoothstep(24, 38, d + n1 * 7), 1 - smoothstep(1.2, 2.6, h + n1 * 0.6));
    c.copy(C.sand).lerp(C.wetSand, 1 - smoothstep(0.1, 0.7, h));
    if (h < -0.4) c.copy(C.seabed).lerp(C.wetSand, smoothstep(-0.4, -6, h) * 0.6);
    const grass = new THREE.Color().copy(C.grass).lerp(C.grassDry, smoothstep(0.2, 0.6, n2 + 0.3) * 0.5);
    // Jungle floor: patches of leaf litter and bright moss between the greens.
    const n3 = this.noise.noise(x * 0.11 + 13, z * 0.11 - 5);
    const jungle = new THREE.Color().copy(C.jungle).lerp(C.jungleDark, smoothstep(-0.2, 0.4, n1))
      .lerp(C.litter, smoothstep(0.0, 0.3, n3) * 0.8).lerp(C.mossFloor, smoothstep(0.05, 0.35, -n3) * 0.7);
    const g = new THREE.Color().copy(grass).lerp(jungle, smoothstep(38, 62, d + n2 * 10));
    c.lerp(g, 1 - sandish);
    // Rock on steep ground and the headlands: olive-grey with moss on the flatter faces.
    let rock = smoothstep(0.62, 0.9, slope + n2 * 0.08);
    rock = Math.max(rock, this.headland(x) * smoothstep(1.8, 4, h) * 0.85);
    const rc = new THREE.Color().copy(C.rockDark).lerp(C.rock, smoothstep(-0.3, 0.5, n1)).lerp(C.moss, (1 - smoothstep(0.7, 1.0, slope)) * 0.5);
    c.lerp(rc, rock * (1 - sandish * 0.7));
    // The volcano: jungle thins into ash, then bare basalt toward the crater.
    const V = VOLCANO, dv = Math.hypot(x - V.x, z - V.z);
    const ash = smoothstep(V.base * 0.62, V.base * 0.38, dv + n1 * 14);
    const bas = smoothstep(V.base * 0.42, V.base * 0.22, dv + n2 * 10);
    c.lerp(C.ash, ash).lerp(C.basalt, bas);
    const { lava, crust } = this.lavaAt(x, z);
    c.lerp(C.crust, crust * 0.8).lerp(C.lava, lava);
    return { c, lava };
  }

  // Hard-faceted mesh: every triangle has its own normal and one flat colour. Triangles hidden
  // under deep (opaque) water are skipped.
  buildMesh(material) {
    const n = this.N + 1, c = this.cell;
    const vc = new Float32Array(n * n * 3), vl = new Float32Array(n * n);
    const { noise } = this.noise;
    for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
      const k = j * n + i;
      const x = this.min + i * c, z = this.min + j * c, h = this.h[k];
      const hx = this.h[j * n + Math.min(n - 1, i + 1)] - this.h[j * n + Math.max(0, i - 1)];
      const hz = this.h[Math.min(n - 1, j + 1) * n + i] - this.h[Math.max(0, j - 1) * n + i];
      const slope = Math.atan(Math.hypot(hx, hz) / (2 * c));
      const { c: col, lava } = this.colourAt(x, z, h, slope, noise(x * 0.06, z * 0.06), noise(x * 0.21 + 7, z * 0.21));
      vc.set([col.r, col.g, col.b], k * 3);
      vl[k] = lava;
    }
    const pos = [], col = [], lav = [];
    const P = (k) => [this.min + (k % n) * c, this.h[k], this.min + Math.floor(k / n) * c];
    const face = (a, b, d) => {
      if (this.h[a] < -9 && this.h[b] < -9 && this.h[d] < -9) return;
      pos.push(...P(a), ...P(b), ...P(d));
      // One colour per face, with a little brightness wobble so the facets read.
      const x = this.min + (a % n) * c, z = this.min + Math.floor(a / n) * c;
      const hs = Math.sin(x * 12.9898 + z * 78.233 + b * 0.37) * 43758.5453;
      const w = 1 + (hs - Math.floor(hs) - 0.5) * 0.08;
      const rgb = [0, 1, 2].map((q) => ((vc[a * 3 + q] + vc[b * 3 + q] + vc[d * 3 + q]) / 3) * w);
      col.push(...rgb, ...rgb, ...rgb);
      const l = (vl[a] + vl[b] + vl[d]) / 3;
      lav.push(l, l, l);
    };
    for (let j = 0; j < this.N; j++) for (let i = 0; i < this.N; i++) {
      const a = j * n + i, b = a + 1, cc = a + n, d = cc + 1;
      face(a, cc, b);
      face(b, cc, d);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    geo.setAttribute('lava', new THREE.Float32BufferAttribute(lav, 1));
    geo.computeVertexNormals();
    geo.computeBoundingSphere();
    const mesh = new THREE.Mesh(geo, material);
    mesh.receiveShadow = true;
    mesh.castShadow = true;
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
