// The island: hex tiles with auto-fitted coast pieces, a height lookup for walking,
// decoration, colliders, and the ocean around it.
import * as THREE from 'three';
import { HexGrid, TileHeights, DIRS, key, hexDistance } from './hex.js';
import { InstanceBatch, cloneStatic } from './assets.js';
import { createOcean, createSky } from './water.js';
import { makeRng } from './util.js';

export const WS = 4; // KayKit hex pack is board-game scale; this makes a tile ~9 m across.
const TILE_TYPES = ['grass', 'coast_a', 'coast_b', 'coast_c', 'coast_d', 'coast_e'];
const ROT = (k) => (k * Math.PI) / 3;

export class World {
  constructor(scene, assets, seed = 'tideborn-cove-1') {
    this.scene = scene;
    this.assets = assets;
    this.rng = makeRng(seed);
    this.root = new THREE.Group();
    this.root.name = 'world';
    scene.add(this.root);
    this.colliders = []; // { x, z, r, id? }
    this.clouds = [];

    this.measureTiles();
    this.generateIsland();
    this.placeTiles();
    this.findSpawn();
    this.buildDistanceField();
    this.decorate();
    this.buildOcean();
  }

  // --- Tile metrics and baked heights ------------------------------------
  measureTiles() {
    const box = new THREE.Box3().setFromObject(this.assets.grass.scene);
    const size = box.getSize(new THREE.Vector3()).multiplyScalar(WS);
    this.grid = new HexGrid(size.x, size.z);
    this.heights = {};
    for (const t of TILE_TYPES) {
      this.heights[t] = [];
      for (let k = 0; k < 6; k++) {
        const holder = new THREE.Group();
        holder.rotation.y = ROT(k);
        holder.scale.setScalar(WS);
        holder.add(this.assets[t].scene.clone(true));
        this.heights[t][k] = new TileHeights(holder, size.z * 0.5, 17);
      }
    }
    this.yGrass = this.heights.grass[0].at(0, 0);

    // Which edges of each coast piece (at each rotation) are water.
    let yWater = Infinity;
    const samples = {};
    for (const t of TILE_TYPES.slice(1)) {
      samples[t] = [];
      for (let k = 0; k < 6; k++) {
        const s = DIRS.map((_, i) => {
          const v = this.grid.dirVector(i);
          return this.heights[t][k].at(v.x * 0.45, v.z * 0.45);
        });
        samples[t].push(s);
        for (const h of s) yWater = Math.min(yWater, h);
      }
    }
    this.yWater = yWater;
    // Beach sand reaches ~half height; only count an edge as water when it is clearly open water.
    const mid = yWater + 0.25 * (this.yGrass - yWater);
    this.edgeMasks = {};
    for (const t of TILE_TYPES.slice(1)) {
      this.edgeMasks[t] = samples[t].map((s) => s.map((h) => h < mid));
    }
  }

  // --- Island shape --------------------------------------------------------
  generateIsland() {
    const rng = this.rng;
    const R = 7;
    const p1 = rng() * 6.28, p2 = rng() * 6.28;
    const cells = new Map();
    for (let q = -R - 3; q <= R + 3; q++) {
      for (let r = -R - 3; r <= R + 3; r++) {
        const d = hexDistance(q, r);
        if (d > R + 2) continue;
        const { x, z } = this.grid.toWorld(q, r);
        const ang = Math.atan2(z, x);
        // Wobbly outline, plus a cove biting into the south shore (toward the camera).
        let limit = R * (0.8 + 0.12 * Math.sin(3 * ang + p1) + 0.08 * Math.sin(5 * ang + p2));
        const southness = Math.cos(ang - Math.PI / 2);
        limit -= 3.2 * Math.max(0, southness) ** 6;
        cells.set(key(q, r), { q, r, land: d <= limit + (rng() - 0.5) * 0.6 });
      }
    }
    this.cells = cells;
    this.neighbors = (c) => DIRS.map(([dq, dr]) => cells.get(key(c.q + dq, c.r + dr)));

    // Smooth: remove spits and fill lakes, then make sure every coast cell has a fitting piece.
    for (let pass = 0; pass < 6; pass++) {
      let changed = false;
      for (const c of cells.values()) {
        const landN = this.neighbors(c).filter((n) => n?.land).length;
        if (c.land && landN <= 2) { c.land = false; changed = true; }
        else if (!c.land && landN >= 5) { c.land = true; changed = true; }
      }
      for (const c of cells.values()) {
        if (!c.land) continue;
        const fit = this.fitTile(c);
        if (!fit) { c.land = false; changed = true; }
      }
      if (!changed) break;
    }
    for (const c of cells.values()) {
      if (c.land) Object.assign(c, this.fitTile(c));
    }
  }

  fitTile(c) {
    const water = this.neighbors(c).map((n) => !n?.land);
    if (!water.some(Boolean)) return { tile: 'grass', rot: this.rng.int(0, 5), coast: false };
    for (const t of TILE_TYPES.slice(1)) {
      for (let k = 0; k < 6; k++) {
        const m = this.edgeMasks[t][k];
        if (m.every((w, i) => w === water[i])) return { tile: t, rot: k, coast: true };
      }
    }
    return null;
  }

  placeTiles() {
    const batch = new InstanceBatch(this.assets);
    const m = new THREE.Matrix4();
    const q = new THREE.Quaternion();
    const s = new THREE.Vector3(WS, WS, WS);
    this.bounds = { minX: Infinity, maxX: -Infinity, minZ: Infinity, maxZ: -Infinity };
    for (const c of this.cells.values()) {
      if (!c.land) continue;
      const { x, z } = this.grid.toWorld(c.q, c.r);
      c.x = x; c.z = z;
      q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), ROT(c.rot));
      m.compose(new THREE.Vector3(x, 0, z), q, s);
      batch.add(c.tile, m, { castShadow: false, receiveShadow: true });
      this.bounds.minX = Math.min(this.bounds.minX, x);
      this.bounds.maxX = Math.max(this.bounds.maxX, x);
      this.bounds.minZ = Math.min(this.bounds.minZ, z);
      this.bounds.maxZ = Math.max(this.bounds.maxZ, z);
    }
    batch.build(this.root);
    this.landCells = [...this.cells.values()].filter((c) => c.land);
  }

  // --- Queries used by the player and gathering ---------------------------
  heightAt(x, z) {
    const { q, r } = this.grid.fromWorld(x, z);
    const c = this.cells.get(key(q, r));
    if (!c || !c.land) return this.yWater - 3;
    return this.heights[c.tile][c.rot].at(x - c.x, z - c.z);
  }

  isWalkable(x, z) {
    return this.heightAt(x, z) > this.yWater + 0.18;
  }

  isOnGrass(x, z) {
    return this.heightAt(x, z) > this.yGrass - 0.08;
  }

  isFree(x, z, r) {
    for (const c of this.colliders) {
      const dx = x - c.x, dz = z - c.z, rr = r + c.r;
      if (dx * dx + dz * dz < rr * rr) return false;
    }
    return true;
  }

  addCollider(x, z, r, id) {
    const c = { x, z, r, id };
    this.colliders.push(c);
    return c;
  }

  removeCollider(c) {
    const i = this.colliders.indexOf(c);
    if (i >= 0) this.colliders.splice(i, 1);
  }

  randomLandPoint(rng, { grassOnly = true, tries = 60 } = {}) {
    for (let i = 0; i < tries; i++) {
      const c = rng.pick(this.landCells);
      const a = rng() * Math.PI * 2;
      const rad = Math.sqrt(rng()) * this.grid.W * 0.48;
      const x = c.x + Math.cos(a) * rad, z = c.z + Math.sin(a) * rad;
      if (grassOnly ? this.isOnGrass(x, z) : this.isWalkable(x, z)) return { x, z, cell: c };
    }
    return null;
  }

  // --- Spawn: on the beach inside the southern cove -------------------------
  findSpawn() {
    const zStart = this.bounds.maxZ + this.grid.H;
    let best = null;
    for (const x of [0, -2, 2, -4, 4, -6, 6, -9, 9]) {
      for (let z = zStart; z > this.bounds.minZ; z -= 0.25) {
        if (this.isWalkable(x, z)) {
          if (!best || z < best.z) best = { x, z };
          break;
        }
      }
    }
    // Deepest beach point into the cove, then a few steps inland.
    this.spawn = { x: best.x, z: best.z - 2.5, facing: 0.35 };
    this.spawn.y = this.heightAt(this.spawn.x, this.spawn.z);
  }

  // --- Distance-to-land field (drives water tint, foam, lily placement) ---
  buildDistanceField() {
    const N = 256;
    const margin = 30;
    const minX = Math.min(this.bounds.minX, this.bounds.minZ) - margin;
    const maxX = Math.max(this.bounds.maxX, this.bounds.maxZ) + margin;
    const size = maxX - minX;
    const cell = size / N;
    const INF = 1e9;
    const d = new Float32Array(N * N);
    for (let j = 0; j < N; j++) {
      for (let i = 0; i < N; i++) {
        const x = minX + (i + 0.5) * cell, z = minX + (j + 0.5) * cell;
        d[j * N + i] = this.heightAt(x, z) > this.yWater + 0.02 ? 0 : INF;
      }
    }
    // Two-pass chamfer distance transform.
    const a = 1, b = Math.SQRT2;
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
      let v = d[j * N + i];
      if (i > 0) v = Math.min(v, d[j * N + i - 1] + a);
      if (j > 0) {
        v = Math.min(v, d[(j - 1) * N + i] + a);
        if (i > 0) v = Math.min(v, d[(j - 1) * N + i - 1] + b);
        if (i < N - 1) v = Math.min(v, d[(j - 1) * N + i + 1] + b);
      }
      d[j * N + i] = v;
    }
    for (let j = N - 1; j >= 0; j--) for (let i = N - 1; i >= 0; i--) {
      let v = d[j * N + i];
      if (i < N - 1) v = Math.min(v, d[j * N + i + 1] + a);
      if (j < N - 1) {
        v = Math.min(v, d[(j + 1) * N + i] + a);
        if (i < N - 1) v = Math.min(v, d[(j + 1) * N + i + 1] + b);
        if (i > 0) v = Math.min(v, d[(j + 1) * N + i - 1] + b);
      }
      d[j * N + i] = v;
    }
    const maxD = 14;
    const bytes = new Uint8Array(N * N);
    for (let k = 0; k < N * N; k++) bytes[k] = Math.min(255, Math.round((d[k] * cell / maxD) * 255));
    const tex = new THREE.DataTexture(bytes, N, N, THREE.RedFormat, THREE.UnsignedByteType);
    tex.magFilter = THREE.LinearFilter;
    tex.minFilter = THREE.LinearFilter;
    tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.flipY = false;
    tex.needsUpdate = true;
    this.dist = { tex, N, cell, minX, size, maxD, meters: d };
  }

  waterDistance(x, z) {
    const { N, cell, minX, meters } = this.dist;
    const i = Math.floor((x - minX) / cell), j = Math.floor((z - minX) / cell);
    if (i < 0 || j < 0 || i >= N || j >= N) return 999;
    return meters[j * N + i] * cell;
  }

  // --- Decoration ------------------------------------------------------------
  decorate() {
    const rng = this.rng;
    const batch = new InstanceBatch(this.assets);
    const m = new THREE.Matrix4();
    const place = (k, x, z, { rot = rng() * Math.PI * 2, scale = WS, y = null, opts } = {}) => {
      const pos = new THREE.Vector3(x, y ?? this.heightAt(x, z), z);
      m.compose(pos, new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), rot), new THREE.Vector3(scale, scale, scale));
      batch.add(k, m, opts);
    };
    const W = this.grid.W;
    const sp = this.spawn;
    const distSpawn = (c) => Math.hypot(c.x - sp.x, c.z - sp.z);
    const interior = this.landCells.filter((c) => !c.coast);

    // Landmark: mountains on the north side, visible from the beach.
    const north = [...interior].sort((a, b) => a.z - b.z);
    const mountains = north.slice(0, 3);
    mountains.forEach((c, i) => {
      place(['mountain_a', 'mountain_b', 'mountain_c'][i % 3], c.x, c.z, { rot: ROT(rng.int(0, 5)), y: this.yGrass });
      c.used = true;
      this.addCollider(c.x, c.z, W * 0.46);
    });

    // Forest and hills on interior tiles away from the beach.
    for (const c of interior) {
      if (c.used || distSpawn(c) < W * 2.2) continue;
      const roll = rng();
      if (roll < 0.22) {
        const k = rng.pick(['forest_a_large', 'forest_b_large', 'forest_a_medium', 'forest_b_medium']);
        place(k, c.x, c.z, { rot: ROT(rng.int(0, 5)), y: this.yGrass });
        this.addCollider(c.x, c.z, W * 0.4);
        c.used = true;
      } else if (roll < 0.3) {
        place(rng.pick(['hills_a', 'hills_b', 'hills_c']), c.x, c.z, { rot: ROT(rng.int(0, 5)), y: this.yGrass });
        this.addCollider(c.x, c.z, W * 0.33);
        c.used = true;
      }
    }

    // Reeds along the waterline.
    let reeds = 0;
    for (let i = 0; i < 400 && reeds < 45; i++) {
      const c = rng.pick(this.landCells.filter((l) => l.coast));
      const a = rng() * Math.PI * 2, rad = rng() * W * 0.55;
      const x = c.x + Math.cos(a) * rad, z = c.z + Math.sin(a) * rad;
      const h = this.heightAt(x, z);
      if (h < this.yWater - 0.05 || h > this.yWater + 0.35) continue;
      if (Math.hypot(x - sp.x, z - sp.z) < 3) continue;
      place(rng.pick(['reed_a', 'reed_b', 'reed_c']), x, z, { scale: WS * rng.range(1.1, 1.6), opts: { castShadow: false } });
      reeds++;
    }
    // Lilies on calm water near the shore.
    let lilies = 0;
    for (let i = 0; i < 600 && lilies < 18; i++) {
      const x = rng.range(this.bounds.minX - 10, this.bounds.maxX + 10);
      const z = rng.range(this.bounds.minZ - 10, this.bounds.maxZ + 10);
      const wd = this.waterDistance(x, z);
      if (wd < 1.5 || wd > 5 || this.heightAt(x, z) > this.yWater - 0.1) continue;
      place(rng.pick(['lily_a', 'lily_b']), x, z, { scale: WS * rng.range(1.2, 1.8), y: this.yWater + 0.03, opts: { castShadow: false } });
      lilies++;
    }

    // A small stash where you washed ashore.
    const camp = [
      ['crate', 2.2, -1.2, 1.0], ['barrel', 2.9, 0.2, 0.5], ['sack', 1.8, 0.6, 0.4],
    ];
    for (const [k, dx, dz, r] of camp) {
      const x = sp.x + dx, z = sp.z + dz;
      if (!this.isWalkable(x, z)) continue;
      place(k, x, z, { scale: WS * 1.1 });
      this.addCollider(x, z, r);
    }
    this.stashSpot = { x: sp.x - 2.4, z: sp.z - 0.6 };

    batch.build(this.root);

    // Clouds drift slowly overhead.
    for (let i = 0; i < 8; i++) {
      const cl = cloneStatic(this.assets, rng() < 0.5 ? 'cloud_big' : 'cloud_small', { castShadow: false, receiveShadow: false });
      cl.scale.setScalar(WS * rng.range(1.3, 2.2));
      cl.position.set(rng.range(-110, 110), rng.range(48, 62), rng.range(-150, 10));
      cl.rotation.y = rng() * Math.PI * 2;
      cl.userData.speed = rng.range(0.6, 1.4);
      this.root.add(cl);
      this.clouds.push(cl);
    }
  }

  buildOcean() {
    this.sunDir = new THREE.Vector3(-0.45, 0.8, 0.35).normalize();
    this.ocean = createOcean({
      y: this.yWater + 0.07,
      distTexture: this.dist.tex,
      bounds: { minX: this.dist.minX, minZ: this.dist.minX, size: this.dist.size },
      maxDist: this.dist.maxD,
      sunDir: this.sunDir,
    });
    this.root.add(this.ocean);
    this.sky = createSky();
    this.scene.add(this.sky);
  }

  update(dt, t, camera) {
    this.ocean.update(t);
    this.sky.position.copy(camera.position);
    for (const c of this.clouds) {
      c.position.x += c.userData.speed * dt;
      if (c.position.x > 110) c.position.x = -110;
    }
  }
}
