// Ground cover around the player: grass, ferns, flowers, bromeliads and seedlings, generated
// cell by cell from a seeded hash (the same spot always grows the same plants) and drawn as one
// instanced mesh per kind. Only cells within `radius` are filled; plants shrink to nothing toward
// the edge so the ring doesn't pop. Rebuilt when the player crosses into another cell.
import * as THREE from 'three';
import { meshParts } from '../assets.js';

const CELL = 8;

function cellRng(i, j, k) {
  let s = (Math.imul(i, 73856093) ^ Math.imul(j, 19349663) ^ Math.imul(k + 1, 83492791)) >>> 0 || 1;
  return () => ((s = (Math.imul(s, 1664525) + 1013904223) >>> 0) / 4294967296);
}

export class GroundCover {
  // kinds: [{ key, density(x, z, h, slope) → plants per m², scale: [min, max], sink }]
  constructor(parent, assets, island, kinds, { radius = 40, blocked = () => false } = {}) {
    this.island = island;
    this.kinds = kinds;
    this.radius = radius;
    this.blocked = blocked;
    this.cells = new Map();
    this.cur = null;
    this.m = new THREE.Matrix4();
    this.q = new THREE.Quaternion();
    this.s = new THREE.Vector3();
    this.p = new THREE.Vector3();
    this.m2 = new THREE.Matrix4();
    const area = Math.PI * (radius + CELL) ** 2;
    for (const k of kinds) {
      k.cap = Math.ceil((k.max ?? 0.3) * area * 1.1) + 16;
      k.meshes = meshParts(assets[k.key].scene).map((part) => {
        const im = new THREE.InstancedMesh(part.geometry, part.material, k.cap);
        im.count = 0;
        im.castShadow = k.shadow ?? false;
        im.receiveShadow = true;
        im.frustumCulled = false;
        im.name = `cover:${k.key}`;
        parent.add(im);
        return { im, local: part.matrix };
      });
    }
  }

  // The plants of one cell: computed once, then cached.
  cell(i, j) {
    const id = `${i},${j}`;
    let list = this.cells.get(id);
    if (list) return list;
    list = [];
    const I = this.island;
    this.kinds.forEach((k, ki) => {
      const R = cellRng(i, j, ki);
      const n = Math.round((k.max ?? 0.3) * CELL * CELL);
      for (let t = 0; t < n; t++) {
        const x = (i + R()) * CELL, z = (j + R()) * CELL, roll = R(), rot = R() * Math.PI * 2, sc = R();
        const h = I.heightAt(x, z);
        if (h < 0.25) continue;
        const dens = k.density(x, z, h, I.slopeAt(x, z));
        if (roll * (k.max ?? 0.3) > dens) continue;
        if (this.blocked(x, z, 0.2)) continue;
        list.push({ ki, x, y: h - (k.sink ?? 0.03), z, rot, scale: k.scale[0] + (k.scale[1] - k.scale[0]) * sc });
      }
    });
    this.cells.set(id, list);
    return list;
  }

  update(px, pz) {
    const ci = Math.floor(px / CELL), cj = Math.floor(pz / CELL);
    const key = `${ci},${cj}`;
    if (key === this.cur) return;
    this.cur = key;
    const r = Math.ceil(this.radius / CELL) + 1, R2 = this.radius;
    for (const k of this.kinds) k.n = 0;
    for (let j = cj - r; j <= cj + r; j++) for (let i = ci - r; i <= ci + r; i++) {
      for (const pl of this.cell(i, j)) {
        const d = Math.hypot(pl.x - px, pl.z - pz);
        if (d > R2) continue;
        const k = this.kinds[pl.ki];
        if (k.n >= k.cap) continue;
        const fade = Math.min(1, (R2 - d) / (R2 * 0.25));
        this.q.setFromAxisAngle(THREE.Object3D.DEFAULT_UP, pl.rot);
        this.m.compose(this.p.set(pl.x, pl.y, pl.z), this.q, this.s.setScalar(pl.scale * fade));
        for (const mp of k.meshes) mp.im.setMatrixAt(k.n, this.m2.multiplyMatrices(this.m, mp.local));
        k.n++;
      }
    }
    for (const k of this.kinds) for (const mp of k.meshes) {
      mp.im.count = k.n;
      mp.im.instanceMatrix.needsUpdate = true;
    }
    // Keep the cache from growing without bound on a long walk.
    if (this.cells.size > 2000) this.cells.clear();
  }

  get triangles() {
    let t = 0;
    for (const k of this.kinds) for (const mp of k.meshes) t += mp.im.count * ((mp.im.geometry.index?.count ?? mp.im.geometry.attributes.position.count) / 3);
    return t;
  }
}
