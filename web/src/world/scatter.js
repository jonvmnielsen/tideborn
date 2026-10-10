// Chunked instancing: models placed across the island are batched per 64 m chunk,
// so the camera and shadow frustums can skip whole chunks. Every placement keeps a
// handle, so single trees can be hidden (felled) and shown again (regrown).
//
// Trees have two versions (opts.far = key of the far model): the full tree for the ones
// nearest the player and an 8-triangle card for the rest. LodSet swaps them as you move.
// Small things (opts.maxDist) are only drawn when their chunk is near the player.
import * as THREE from 'three';
import { meshParts } from '../assets.js';

const CHUNK = 64;
const ZERO = new THREE.Matrix4().makeScale(0, 0, 0);

class LodSet {
  constructor(key, farKey, opts) {
    this.key = key;
    this.farKey = farKey;
    this.opts = opts;
    this.base = [];   // original matrices
    this.cur = [];    // current matrices (null = hidden)
    this.px = [];
    this.pz = [];
    this.tmp = new THREE.Matrix4();
  }

  add(matrix, hidden) {
    this.base.push(matrix.clone());
    this.cur.push(hidden ? null : matrix.clone());
    const p = new THREE.Vector3().setFromMatrixPosition(matrix);
    this.px.push(p.x);
    this.pz.push(p.z);
    return this.base.length - 1;
  }

  build(parent, assets, cap) {
    const n = this.base.length;
    this.cap = Math.min(cap, n);
    const make = (key, count, castShadow) => meshParts(assets[key].scene).map((p) => {
      const im = new THREE.InstancedMesh(p.geometry, p.material, count);
      im.castShadow = castShadow;
      im.receiveShadow = true;
      im.frustumCulled = false; // spans the island; the far cards are cheap
      im.name = key;
      parent.add(im);
      return { im, local: p.matrix };
    });
    this.near = make(this.key, this.cap, this.opts.castShadow ?? true);
    for (const p of this.near) p.im.count = 0;
    this.far = make(this.farKey, n, this.opts.castShadow ?? true);
    for (let i = 0; i < n; i++) this.write(this.far, i, this.cur[i]);
    this.nearOf = new Int32Array(n).fill(-1);
    this.owner = [];
    this.nearCount = 0;
  }

  write(parts, slot, m) {
    for (const p of parts) {
      p.im.setMatrixAt(slot, m ? this.tmp.multiplyMatrices(m, p.local) : ZERO);
      p.im.instanceMatrix.needsUpdate = true;
    }
  }

  set(i, m) {
    this.cur[i] = m ? m.clone() : null;
    const s = this.nearOf[i];
    if (s >= 0) this.write(this.near, s, this.cur[i]);
    else this.write(this.far, i, this.cur[i]);
  }

  update(x, z, radius) {
    const r2 = radius * radius;
    let cand = [];
    for (let i = 0; i < this.px.length; i++) {
      const d = (this.px[i] - x) ** 2 + (this.pz[i] - z) ** 2;
      if (d < r2) cand.push([d, i]);
    }
    if (cand.length > this.cap) cand = cand.sort((a, b) => a[0] - b[0]).slice(0, this.cap);
    const want = new Set(cand.map((c) => c[1]));
    for (let s = this.nearCount - 1; s >= 0; s--) {
      const i = this.owner[s];
      if (want.has(i)) continue;
      const last = --this.nearCount;
      if (s !== last) {
        const j = this.owner[last];
        this.owner[s] = j;
        this.nearOf[j] = s;
        this.write(this.near, s, this.cur[j]);
      }
      this.nearOf[i] = -1;
      this.write(this.far, i, this.cur[i]);
    }
    for (const [, i] of cand) {
      if (this.nearOf[i] >= 0 || this.nearCount >= this.cap) continue;
      const s = this.nearCount++;
      this.owner[s] = i;
      this.nearOf[i] = s;
      this.write(this.near, s, this.cur[i]);
      this.write(this.far, i, null);
    }
    for (const p of this.near) p.im.count = this.nearCount;
  }
}

// Things that are usually hidden (stumps of felled trees): only shown instances are drawn,
// so a thousand waiting stumps cost nothing.
class PoolSet {
  constructor(key, opts) {
    this.key = key;
    this.opts = opts;
    this.base = [];
    this.tmp = new THREE.Matrix4();
  }
  add(matrix) {
    this.base.push(matrix.clone());
    return this.base.length - 1;
  }
  build(parent, assets) {
    this.parts = meshParts(assets[this.key].scene).map((p) => {
      const im = new THREE.InstancedMesh(p.geometry, p.material, Math.max(1, this.base.length));
      im.count = 0;
      im.castShadow = this.opts.castShadow ?? true;
      im.receiveShadow = true;
      im.frustumCulled = false;
      im.name = this.key;
      parent.add(im);
      return { im, local: p.matrix };
    });
    this.slotOf = new Int32Array(this.base.length).fill(-1);
    this.owner = [];
    this.count = 0;
    for (const [i, m] of this.pending ?? []) this.set(i, m);
    this.pending = null;
  }
  write(slot, m) {
    for (const p of this.parts) {
      p.im.setMatrixAt(slot, this.tmp.multiplyMatrices(m, p.local));
      p.im.instanceMatrix.needsUpdate = true;
      p.im.count = this.count;
    }
  }
  set(i, m) {
    if (!this.parts) { (this.pending ??= []).push([i, m]); return; }
    let s = this.slotOf[i];
    if (m) {
      if (s < 0) { s = this.count++; this.slotOf[i] = s; this.owner[s] = i; }
      this.write(s, m);
    } else if (s >= 0) {
      const last = --this.count;
      if (s !== last) {
        const j = this.owner[last];
        this.owner[s] = j;
        this.slotOf[j] = s;
        for (const p of this.parts) { p.im.getMatrixAt(last, this.tmp); p.im.setMatrixAt(s, this.tmp); }
      }
      this.slotOf[i] = -1;
      for (const p of this.parts) { p.im.count = this.count; p.im.instanceMatrix.needsUpdate = true; }
    }
  }
}

export class Scatter {
  constructor(parent, assets, { nearRadius = 45, nearCap = 90 } = {}) {
    this.parent = parent;
    this.assets = assets;
    this.groups = new Map(); // `${chunk}|${key}` → { key, matrices: [], opts, meshes }
    this.lods = new Map();   // key → LodSet
    this.pools = new Map();  // key → PoolSet
    this.nearRadius = nearRadius;
    this.nearCap = nearCap;
    this.built = false;
    this.tmp = new THREE.Matrix4();
    this.last = { x: Infinity, z: Infinity, t: 0 };
  }

  chunkOf(x, z) {
    return `${Math.floor(x / CHUNK)},${Math.floor(z / CHUNK)}`;
  }

  // Returns a handle for later set().
  add(key, matrix, opts = {}, hidden = false) {
    if (opts.pool) {
      let pool = this.pools.get(key);
      if (!pool) this.pools.set(key, (pool = new PoolSet(key, opts)));
      const i = pool.add(matrix);
      if (!hidden) pool.set(i, matrix);
      return { pool, i };
    }
    if (opts.far) {
      let lod = this.lods.get(key);
      if (!lod) this.lods.set(key, (lod = new LodSet(key, opts.far, opts)));
      return { lod, i: lod.add(matrix, hidden) };
    }
    const e = new THREE.Vector3().setFromMatrixPosition(matrix);
    const chunk = this.chunkOf(e.x, e.z);
    const gk = `${chunk}|${key}`;
    let g = this.groups.get(gk);
    if (!g) {
      const [cx, cz] = chunk.split(',').map(Number);
      g = { key, opts, matrices: [], hidden: new Set(), meshes: null, cx: (cx + 0.5) * CHUNK, cz: (cz + 0.5) * CHUNK };
      this.groups.set(gk, g);
    }
    g.matrices.push(matrix.clone());
    if (hidden) g.hidden.add(g.matrices.length - 1);
    return { g, i: g.matrices.length - 1 };
  }

  build() {
    for (const g of this.groups.values()) {
      const parts = meshParts(this.assets[g.key].scene);
      g.meshes = parts.map((p) => {
        const im = new THREE.InstancedMesh(p.geometry, p.material, g.matrices.length);
        g.matrices.forEach((m, i) => im.setMatrixAt(i, this.tmp.multiplyMatrices(g.hidden.has(i) ? this.hiddenMatrix(m) : m, p.matrix)));
        im.instanceMatrix.needsUpdate = true;
        im.castShadow = g.opts.castShadow ?? true;
        im.receiveShadow = g.opts.receiveShadow ?? true;
        im.computeBoundingSphere();
        // Leave room for things shaking or falling within the chunk.
        im.boundingSphere.radius += 6;
        im.name = g.key;
        this.parent.add(im);
        return { im, local: p.matrix };
      });
    }
    for (const lod of this.lods.values()) lod.build(this.parent, this.assets, this.nearCap);
    for (const pool of this.pools.values()) pool.build(this.parent, this.assets);
    this.built = true;
  }

  // Swap tree versions and hide small things far from the player. Cheap; throttled.
  update(x, z, now) {
    if (Math.hypot(x - this.last.x, z - this.last.z) < 2.5 && now - this.last.t < 1) return;
    this.last = { x, z, t: now };
    for (const lod of this.lods.values()) lod.update(x, z, this.nearRadius);
    for (const g of this.groups.values()) {
      if (!g.opts.maxDist) continue;
      const vis = Math.hypot(g.cx - x, g.cz - z) < g.opts.maxDist + CHUNK * 0.71;
      for (const p of g.meshes) p.im.visible = vis;
    }
  }

  // matrix = null hides the instance (shrinks it in place, keeping chunk bounds intact).
  set(handle, matrix) {
    if (handle.lod) return handle.lod.set(handle.i, matrix);
    if (handle.pool) return handle.pool.set(handle.i, matrix);
    const { g, i } = handle;
    const m = matrix ?? this.hiddenMatrix(g.matrices[i]);
    for (const p of g.meshes) {
      p.im.setMatrixAt(i, this.tmp.multiplyMatrices(m, p.local));
      p.im.instanceMatrix.needsUpdate = true;
    }
  }

  original(handle) {
    return (handle.lod ?? handle.pool)?.base[handle.i] ?? handle.g.matrices[handle.i];
  }

  hiddenMatrix(m) {
    const p = new THREE.Vector3().setFromMatrixPosition(m);
    return new THREE.Matrix4().compose(p, new THREE.Quaternion(), new THREE.Vector3(1e-4, 1e-4, 1e-4));
  }
}

export function placement(x, y, z, rotY, scale) {
  return new THREE.Matrix4().compose(
    new THREE.Vector3(x, y, z),
    new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), rotY),
    new THREE.Vector3(scale, scale, scale),
  );
}
