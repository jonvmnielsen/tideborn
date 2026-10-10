// Modular building: foundations on a 4 m world grid, walls on their edges, lofts and
// roofs stacked in 4 m levels, plus free-standing pieces (stairs, fire, chest, bed...).
// A ghost shows where the piece will go: green = valid, red = blocked (with a reason).
import * as THREE from 'three';
import { cloneModel } from '../assets.js';
import { PIECE, GRID, WALL_H } from '../data/build.js';
import { Inventory } from './inventory.js';

const MAX_DEPTH = 4.5;  // foundation top may sit at most this far above the lowest ground under it
const LIFT_STEP = 0.5;  // raise/lower step for foundations
const FOOTING_H = 1.84; // height of one stone footing at the scale used
const FENCE_LEN = 4.6;
const LIFT = 0.35;      // foundation top above the highest ground under it
const ROOF_PITCH = Math.PI / 6;

const cellKey = (i, j, k = 0) => `${i},${j},${k}`;

// Wrap a model so its footprint is centered on x/z and its lowest point sits at y = 0.
function normalized(assets, key, { scale = 1, rotY = 0 } = {}) {
  const obj = cloneModel(assets, key);
  obj.rotation.y = rotY;
  obj.scale.setScalar(scale);
  obj.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(obj);
  const c = box.getCenter(new THREE.Vector3());
  obj.position.set(-c.x, -box.min.y, -c.z);
  const g = new THREE.Group();
  g.add(obj);
  return g;
}

// Heights of the stairs' walking surface, baked once by raycasting the model (local frame).
function bakeStairs(model) {
  model.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(model);
  const ray = new THREE.Raycaster();
  const N = 13;
  const grid = new Float32Array(N);
  for (let k = 0; k < N; k++) {
    const z = box.min.z + ((k + 0.5) / N) * (box.max.z - box.min.z);
    ray.set(new THREE.Vector3(0, 50, z), new THREE.Vector3(0, -1, 0));
    const hit = ray.intersectObject(model, true)[0];
    grid[k] = hit ? hit.point.y : 0;
  }
  // Make it a smooth monotone ramp between its low and high ends.
  const lowFirst = grid[0] < grid[N - 1];
  const hi = Math.max(grid[0], grid[N - 1]);
  return {
    minZ: box.min.z, maxZ: box.max.z, hw: (box.max.x - box.min.x) / 2,
    height(lz) {
      const t = (lz - box.min.z) / (box.max.z - box.min.z);
      const u = lowFirst ? t : 1 - t;
      return Math.max(0, Math.min(hi, u * hi * 1.04));
    },
  };
}

function flameTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(32, 40, 2, 32, 36, 30);
  grd.addColorStop(0, 'rgba(255,240,190,1)');
  grd.addColorStop(0.35, 'rgba(255,170,60,0.9)');
  grd.addColorStop(1, 'rgba(255,90,20,0)');
  g.fillStyle = grd;
  g.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export class Building {
  constructor(world, assets) {
    this.world = world;
    this.assets = assets;
    this.root = new THREE.Group();
    this.root.name = 'buildings';
    world.root.add(this.root);
    this.pieces = [];
    this.byCell = new Map();   // foundations: "i,j,0", lofts: "i,j,k"
    this.byEdge = new Map();   // "x:i,j,k" | "z:i,j,k"
    this.roofs = new Map();    // "i,j,k"
    this.lights = [];          // { x, y, z, color, power, flicker }
    this.flameMat = new THREE.SpriteMaterial({ map: flameTexture(), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, fog: true });
    this.flames = [];
    this.templates = {};
    this.stairs = bakeStairs(normalized(assets, 'build/stairs'));
    this.ghost = null;
    this.ghostMats = {
      ok: new THREE.MeshStandardMaterial({ color: '#7fe0c0', transparent: true, opacity: 0.45, depthWrite: false, emissive: '#2c7d68', emissiveIntensity: 0.6 }),
      bad: new THREE.MeshStandardMaterial({ color: '#ff7a5c', transparent: true, opacity: 0.45, depthWrite: false, emissive: '#8a2a12', emissiveIntensity: 0.6 }),
    };
  }

  // --- Piece visuals -------------------------------------------------------------
  makeVisual(id) {
    const a = this.assets;
    const g = new THREE.Group();
    if (id === 'foundation') {
      const floor = normalized(a, 'build/floor');
      floor.position.y = -0.15;
      g.add(floor);
      for (const [dx, dz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
        const f = normalized(a, 'build/footing', { scale: 0.92 });
        f.userData.footing = true;
        f.position.set(dx, -0.15 - FOOTING_H, dz);
        g.add(f);
      }
    } else if (id === 'loft') {
      const floor = normalized(a, 'build/floor');
      floor.position.y = -0.15;
      g.add(floor);
    } else if (id === 'wall' || id === 'doorway' || id === 'window') {
      g.add(normalized(a, `build/${id}`));
    } else if (id === 'roof') {
      const L = (GRID / 2) / Math.cos(ROOF_PITCH) + 0.25;
      for (const side of [-1, 1]) {
        const p = normalized(a, 'build/floor');
        p.scale.set(1.06, 1, L / 4);
        const holder = new THREE.Group();
        holder.add(p);
        p.position.set(0, 0, -side * L / 2);
        holder.rotation.x = -side * ROOF_PITCH;
        holder.position.set(0, Math.sin(ROOF_PITCH) * (L - 0.25), 0);
        g.add(holder);
      }
    } else if (id === 'stairs') {
      g.add(normalized(a, 'build/stairs'));
    } else if (id === 'fence') {
      g.add(normalized(a, 'build/fence', { scale: 3.9, rotY: Math.PI / 2 }));
    } else if (id === 'campfire') {
      g.add(normalized(a, 'build/firepit', { scale: 1.05 }));
      for (let k = 0; k < 2; k++) {
        const b = normalized(a, 'wood/branches', { scale: 0.75, rotY: k * 1.7 + 0.4 });
        b.position.y = 0.05 + k * 0.06;
        g.add(b);
      }
    } else if (id === 'torch') {
      g.add(normalized(a, 'build/torch', { scale: 2 }));
    } else if (id === 'chest') {
      g.add(normalized(a, 'build/chest', { scale: 1.35 }));
    } else if (id === 'bed') {
      g.add(normalized(a, 'build/bed'));
    }
    g.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    return g;
  }

  // --- Ghost ------------------------------------------------------------------------
  setGhost(id) {
    if (this.ghost) this.root.remove(this.ghost.obj);
    this.ghost = null;
    if (!id) return;
    const obj = this.makeVisual(id === 'loft' ? 'loft' : id);
    obj.traverse((o) => { if (o.isMesh) { o.castShadow = false; o.receiveShadow = false; o.renderOrder = 5; } });
    this.root.add(obj);
    this.ghost = { id, obj, plan: null };
  }

  // ctx = { x, z, vx, vz, rot, level, lift } — cursor point, flat camera view direction,
  // chosen rotation, floor level (0 = ground floor) and foundation lift (0.5 m steps).
  updateGhost(ctx, inventory) {
    const g = this.ghost;
    if (!g) return null;
    const plan = this.plan(g.id, ctx);
    if (plan.ok && !inventory.canAfford(PIECE[g.id].cost)) { plan.ok = false; plan.reason = 'Du mangler materialer'; }
    g.plan = plan;
    g.obj.visible = !!plan.pos;
    if (plan.pos) {
      g.obj.position.set(plan.pos.x, plan.pos.y, plan.pos.z);
      g.obj.rotation.y = plan.rot;
      if (g.id === 'foundation') this.setFootingDepth(g.obj, plan.depth);
    }
    const mat = plan.ok ? this.ghostMats.ok : this.ghostMats.bad;
    g.obj.traverse((o) => { if (o.isMesh) o.material = mat; });
    return plan;
  }

  // Stretch the stone footings so a raised foundation still reaches the ground.
  setFootingDepth(obj, depth) {
    const s = Math.max(1, (depth + 0.4) / FOOTING_H);
    for (const f of obj.children) {
      if (!f.userData.footing) continue;
      f.scale.y = s;
      f.position.y = -0.15 - FOOTING_H * s;
    }
  }

  // --- Placement rules --------------------------------------------------------------
  baseTop(i, j) {
    return this.byCell.get(cellKey(i, j, 0))?.top;
  }

  // Which floor level is a height at, over cell (i, j)?
  levelAt(x, z, y) {
    const top = this.baseTop(Math.round(x / GRID), Math.round(z / GRID));
    if (top === undefined) return 0;
    return Math.max(0, Math.round((y - top) / WALL_H));
  }

  // Pick the best grid cell near the cursor. `want(i, j)` says whether a cell can take the piece.
  // Free cells win; between candidates the one in the view direction wins.
  pickCell(ctx, want, radius = 1) {
    const ci = Math.round(ctx.x / GRID), cj = Math.round(ctx.z / GRID);
    let best = null;
    for (let i = ci - radius; i <= ci + radius; i++) for (let j = cj - radius; j <= cj + radius; j++) {
      const w = want(i, j);
      if (w === null) continue;
      const dx = i * GRID - ctx.x, dz = j * GRID - ctx.z;
      const d = Math.hypot(dx, dz);
      const ahead = d > 0.01 ? (dx * ctx.vx + dz * ctx.vz) / d : 0;
      const score = d - ahead * 0.9 + (w ? 0 : 6);
      if (!best || score < best.score) best = { i, j, free: w, score, d };
    }
    return best;
  }

  plan(id, ctx) {
    const T = this.world.terrain;
    const L = ctx.level ?? 0;

    if (id === 'foundation') {
      // Next to existing foundations the empty neighbour you look toward is chosen.
      const hasAny = this.byCell.size > 0;
      const cell = this.pickCell(ctx, (i, j) => {
        if (this.byCell.has(cellKey(i, j, 0))) return false;
        if (!hasAny) return true;
        const near = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([di, dj]) => this.byCell.has(cellKey(i + di, j + dj, 0)));
        const ci = Math.round(ctx.x / GRID), cj = Math.round(ctx.z / GRID);
        return near || (i === ci && j === cj);
      });
      if (!cell) return { pos: null, ok: false, reason: 'Ingen plads her' };
      const { i, j } = cell;
      const x = i * GRID, z = j * GRID;
      let hMin = Infinity, hMax = -Infinity;
      for (const [dx, dz] of [[-2, -2], [2, -2], [-2, 2], [2, 2], [0, 0], [0, -2], [0, 2], [-2, 0], [2, 0]]) {
        const h = T.heightAt(x + dx * 0.98, z + dz * 0.98);
        hMin = Math.min(hMin, h); hMax = Math.max(hMax, h);
      }
      let top = hMax + LIFT;
      for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const n = this.byCell.get(cellKey(i + di, j + dj, 0));
        if (n && n.top >= hMax - 0.12 && n.top - hMin <= MAX_DEPTH) { top = n.top; break; }
      }
      top += (ctx.lift ?? 0) * LIFT_STEP;
      const res = { pos: { x, y: top, z }, rot: 0, i, j, top, depth: top - hMin };
      if (!cell.free) return { ...res, ok: false, reason: 'Der er allerede et fundament' };
      if (hMin < -0.2) return { ...res, ok: false, reason: 'For tæt på vandet' };
      if (top < hMax - 0.15) return { ...res, ok: false, reason: 'For lavt: hæv fundamentet' };
      if (top - hMin > MAX_DEPTH) return { ...res, ok: false, reason: 'For højt over jorden' };
      if (this.blockedByNature(x, z, 2.1, 2.1, 0)) return { ...res, ok: false, reason: 'Noget står i vejen' };
      return { ...res, ok: true };
    }

    if (id === 'wall' || id === 'doorway' || id === 'window') {
      // All foundation edges around the cursor on this level. The edge you face wins at corners.
      const cx0 = ctx.x + ctx.vx * 0.5, cz0 = ctx.z + ctx.vz * 0.5;
      const ci = Math.round(ctx.x / GRID), cj = Math.round(ctx.z / GRID);
      const seen = new Set();
      let best = null, bestTaken = null;
      for (let i = ci - 1; i <= ci + 1; i++) for (let j = cj - 1; j <= cj + 1; j++) {
        const top = this.baseTop(i, j);
        if (top === undefined) continue;
        const cx = i * GRID, cz = j * GRID;
        for (const e of [
          { key: `x:${i},${j},${L}`, below: `x:${i},${j},${L - 1}`, x: cx, z: cz - 2, rot: 0, nx: 0, nz: 1 },
          { key: `x:${i},${j + 1},${L}`, below: `x:${i},${j + 1},${L - 1}`, x: cx, z: cz + 2, rot: 0, nx: 0, nz: 1 },
          { key: `z:${i},${j},${L}`, below: `z:${i},${j},${L - 1}`, x: cx - 2, z: cz, rot: Math.PI / 2, nx: 1, nz: 0 },
          { key: `z:${i + 1},${j},${L}`, below: `z:${i + 1},${j},${L - 1}`, x: cx + 2, z: cz, rot: Math.PI / 2, nx: 1, nz: 0 },
        ]) {
          if (seen.has(e.key)) continue;
          seen.add(e.key);
          // Upper floors need a floor (loft) on this cell or a wall right below.
          if (L > 0 && !this.byCell.has(cellKey(i, j, L)) && !this.byEdge.has(e.below)) continue;
          const d = Math.hypot(e.x - cx0, e.z - cz0);
          const facing = Math.abs(e.nx * ctx.vx + e.nz * ctx.vz);
          const score = d + (1 - facing) * 1.4;
          const cand = { ...e, score, d, y: top + L * WALL_H };
          if (this.byEdge.has(e.key)) { if (!bestTaken || score < bestTaken.score) bestTaken = cand; }
          else if (!best || score < best.score) best = cand;
        }
      }
      const pick = best && best.d < 4.5 ? best : bestTaken;
      if (!pick || pick.d > 4.5) return { pos: null, ok: false, reason: L > 0 ? 'Byg en etage eller væg nedenunder først' : 'Byg et fundament først' };
      const res = { pos: { x: pick.x, y: pick.y, z: pick.z }, rot: pick.rot, edge: pick.key, k: L };
      if (pick === bestTaken) return { ...res, ok: false, reason: 'Der står allerede en væg' };
      return { ...res, ok: true };
    }

    if (id === 'loft' || id === 'roof') {
      // Sits on top of the walls of the current level.
      const k = L + 1;
      const taken = (i, j) => this.byCell.has(cellKey(i, j, k)) || this.roofs.has(cellKey(i, j, k));
      const cell = this.pickCell(ctx, (i, j) => (this.baseTop(i, j) === undefined ? null : !taken(i, j)));
      if (!cell || cell.d > 4.5) return { pos: null, ok: false, reason: 'Skal stå over et fundament' };
      const { i, j } = cell;
      const y = this.baseTop(i, j) + k * WALL_H;
      const r = ((ctx.rot % Math.PI) + Math.PI) % Math.PI;
      const res = { pos: { x: i * GRID, y, z: j * GRID }, rot: id === 'roof' && r >= Math.PI / 4 && r < (3 * Math.PI) / 4 ? Math.PI / 2 : 0, i, j, k };
      if (!cell.free) return { ...res, ok: false, reason: 'Pladsen er optaget' };
      if (id === 'loft') {
        const walls = [`x:${i},${j},${k - 1}`, `x:${i},${j + 1},${k - 1}`, `z:${i},${j},${k - 1}`, `z:${i + 1},${j},${k - 1}`].some((e) => this.byEdge.has(e));
        const neighbor = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([di, dj]) => this.byCell.has(cellKey(i + di, j + dj, k)));
        if (!walls && !neighbor) return { ...res, ok: false, reason: 'Etagen skal hvile på vægge' };
      }
      return { ...res, ok: true };
    }

    // Free pieces: on the ground, or on a floor of the chosen level.
    const def = PIECE[id];
    let x, z, rot = ctx.rot;
    const st = def.step ?? 0.25;
    x = Math.round(ctx.x / st) * st;
    z = Math.round(ctx.z / st) * st;
    if (id === 'fence') {
      const snap = this.fenceSnap(ctx);
      if (snap) ({ x, z, rot } = snap);
    }
    const base = this.baseTop(Math.round(x / GRID), Math.round(z / GRID));
    const ref = (base ?? T.heightAt(x, z)) + L * WALL_H;
    const y = this.world.groundAt(x, z, ref + 0.3);
    const res = { pos: { x, y, z }, rot };
    if (L > 0 && y < ref - 0.3) return { ...res, ok: false, reason: 'Ingen etage her' };
    if (T.heightAt(x, z) < -0.2 && y <= T.heightAt(x, z) + 0.01) return { ...res, ok: false, reason: 'For tæt på vandet' };
    const onFloor = y > T.heightAt(x, z) + 0.05;
    if (!onFloor && T.slopeAt(x, z) > 0.5) return { ...res, ok: false, reason: 'Jorden er for stejl' };
    if (this.blockedByAnything(x, z, def.size[0] / 2, def.size[1] / 2, rot, y)) return { ...res, ok: false, reason: 'Noget står i vejen' };
    return { ...res, ok: true };
  }

  // Fences join end to end, straight on or at a right angle, when the cursor is near an end.
  fenceSnap(ctx) {
    let best = null;
    for (const f of this.pieces) {
      if (f.id !== 'fence' || Math.hypot(f.x - ctx.x, f.z - ctx.z) > 7) continue;
      const c = Math.cos(f.rot), s = Math.sin(f.rot);
      const ax = c, az = -s;           // along the fence
      const px = s, pz = c;            // across the fence
      const H = FENCE_LEN / 2;
      const cands = [];
      for (const e of [-1, 1]) {
        cands.push({ x: f.x + ax * e * FENCE_LEN, z: f.z + az * e * FENCE_LEN, rot: f.rot });
        for (const side of [-1, 1]) cands.push({ x: f.x + ax * e * H + px * side * H, z: f.z + az * e * H + pz * side * H, rot: f.rot + Math.PI / 2 });
      }
      for (const cnd of cands) {
        if (this.pieces.some((p) => p.id === 'fence' && Math.hypot(p.x - cnd.x, p.z - cnd.z) < 0.5)) continue;
        const d = Math.hypot(cnd.x - ctx.x, cnd.z - ctx.z);
        if (d < 2.2 && (!best || d < best.d)) best = { ...cnd, d };
      }
    }
    return best;
  }

  // Tint one placed piece red (removal target). null clears it.
  highlight(piece) {
    if (this.lit === piece) return;
    if (this.lit) this.lit.obj.traverse((o) => { if (o.isMesh && o.userData.mat) { o.material = o.userData.mat; delete o.userData.mat; } });
    this.lit = piece;
    if (piece) piece.obj.traverse((o) => { if (o.isMesh) { o.userData.mat = o.material; o.material = this.ghostMats.bad; } });
  }

  // Piece closest to the cursor on the current level (for removal).
  pieceNear(ctx, reach = 3.5) {
    let best = null, bd = Infinity;
    const L = ctx.level ?? 0;
    for (const p of this.pieces) {
      const d = Math.hypot(p.x - ctx.x, p.z - ctx.z);
      if (d > reach) continue;
      const lvl = p.k ?? this.levelAt(p.x, p.z, p.y + 0.1);
      const score = d + Math.abs(lvl - L - (p.id === 'roof' || p.id === 'loft' ? 1 : 0)) * 3;
      if (score < bd) { bd = score; best = p; }
    }
    return best;
  }

  blockedByNature(x, z, hw, hd) {
    for (const s of this.world.colliders.near(x, z, Math.max(hw, hd))) {
      if (s.owner?.isPiece) continue;
      if (s.kind === 'circle' && Math.abs(s.x - x) < hw + s.r * 0.6 && Math.abs(s.z - z) < hd + s.r * 0.6) return true;
      if (s.kind === 'box' && Math.abs(s.x - x) < hw + s.hw && Math.abs(s.z - z) < hd + s.hd) return true;
    }
    return false;
  }

  blockedByAnything(x, z, hw, hd, rot, y) {
    const probe = { kind: 'box', x, z, hw: hw * 0.9, hd: hd * 0.9, c: Math.cos(rot), s: Math.sin(rot) };
    for (const s of this.world.colliders.near(x, z, Math.hypot(hw, hd))) {
      if (s.top !== undefined && y >= s.top - 0.05) continue;
      if (s.bottom !== undefined && y + 1.5 <= s.bottom) continue;
      const r = s.kind === 'circle' ? s.r : Math.min(s.hw, s.hd);
      if (boxCircle(probe, s.x, s.z, r)) return true;
    }
    return false;
  }

  // --- Commit / remove ---------------------------------------------------------------
  place(id, plan, extra = {}) {
    const w = this.world;
    const obj = this.makeVisual(id);
    obj.position.set(plan.pos.x, plan.pos.y, plan.pos.z);
    obj.rotation.y = plan.rot;
    this.root.add(obj);
    const piece = { id, x: plan.pos.x, y: plan.pos.y, z: plan.pos.z, rot: plan.rot, obj, colliders: [], surfaces: [], isPiece: true };
    const { x, y, z, rot } = piece;

    if (id === 'foundation') {
      piece.i = plan.i; piece.j = plan.j; piece.top = y; piece.k = 0;
      piece.depth = plan.depth ?? this.depthUnder(x, z, y);
      this.setFootingDepth(obj, piece.depth);
      this.byCell.set(cellKey(plan.i, plan.j, 0), piece);
      piece.colliders.push(w.colliders.addBox(x, z, 2, 2, 0, piece, { top: y }));
      piece.surfaces.push(w.surfaces.add(x, z, 2, 2, 0, () => y, piece));
    } else if (id === 'loft') {
      piece.i = plan.i; piece.j = plan.j; piece.k = plan.k;
      this.byCell.set(cellKey(plan.i, plan.j, plan.k), piece);
      piece.colliders.push(w.colliders.addBox(x, z, 2, 2, 0, piece, { top: y, bottom: y - 0.15 }));
      piece.surfaces.push(w.surfaces.add(x, z, 2, 2, 0, () => y, piece));
    } else if (id === 'roof') {
      piece.i = plan.i; piece.j = plan.j; piece.k = plan.k;
      this.roofs.set(cellKey(plan.i, plan.j, plan.k), piece);
    } else if (id === 'wall' || id === 'window') {
      piece.edge = plan.edge;
      this.byEdge.set(plan.edge, piece);
      piece.colliders.push(w.colliders.addBox(x, z, 2, 0.35, rot, piece, { bottom: y, top: y + WALL_H }));
    } else if (id === 'doorway') {
      piece.edge = plan.edge;
      this.byEdge.set(plan.edge, piece);
      for (const side of [-1, 1]) {
        const ox = Math.cos(rot) * side * 1.72, oz = -Math.sin(rot) * side * 1.72;
        piece.colliders.push(w.colliders.addBox(x + ox, z + oz, 0.3, 0.35, rot, piece, { bottom: y, top: y + WALL_H }));
      }
    } else if (id === 'stairs') {
      const S = this.stairs;
      piece.surfaces.push(w.surfaces.add(x, z, S.hw, (S.maxZ - S.minZ) / 2, rot, (lx, lz) => y + S.height(lz), piece));
      for (const side of [-1, 1]) {
        const ox = Math.cos(rot) * side * (S.hw + 0.1), oz = -Math.sin(rot) * side * (S.hw + 0.1);
        piece.colliders.push(w.colliders.addBox(x + ox, z + oz, 0.1, (S.maxZ - S.minZ) / 2, rot, piece, { bottom: y }));
      }
    } else {
      const def = PIECE[id];
      piece.colliders.push(w.colliders.addBox(x, z, def.size[0] / 2, def.size[1] / 2, rot, piece, { bottom: y, top: y + (id === 'bed' ? 0.6 : id === 'campfire' ? 0.3 : 1.2) }));
      if (id === 'bed') piece.surfaces.push(w.surfaces.add(x, z, def.size[0] / 2, def.size[1] / 2, rot, () => y + 0.55, piece));
    }

    if (id === 'campfire' || id === 'torch') {
      const fy = id === 'campfire' ? 0.55 : 2.1;
      const flame = new THREE.Sprite(this.flameMat);
      flame.position.set(0, fy, 0);
      flame.scale.setScalar(id === 'campfire' ? 1.3 : 0.6);
      obj.add(flame);
      this.flames.push({ sprite: flame, base: flame.scale.x, seed: Math.random() * 10 });
      piece.light = { x, y: y + fy + 0.3, z, color: 0xffa64a, power: id === 'campfire' ? 26 : 12, range: id === 'campfire' ? 16 : 10, piece };
      this.lights.push(piece.light);
    }
    if (id === 'chest') piece.storage = new Inventory(extra.storage ?? {});
    this.pieces.push(piece);
    return piece;
  }

  depthUnder(x, z, top) {
    let hMin = Infinity;
    for (const [dx, dz] of [[-2, -2], [2, -2], [-2, 2], [2, 2], [0, 0]]) hMin = Math.min(hMin, this.world.terrain.heightAt(x + dx * 0.98, z + dz * 0.98));
    return top - hMin;
  }

  // Can this piece be removed without leaving others floating?
  removalBlocker(piece) {
    if (this.stackedOn(piece)) return 'Fjern væggen ovenpå først';
    if (piece.id === 'foundation' || piece.id === 'loft') {
      const { i, j, k } = piece;
      const dependents = [...this.byEdge.keys()].some((e) => {
        const [, rest] = e.split(':');
        const [ei, ej, ek] = rest.split(',').map(Number);
        return ek === k && ((e.startsWith('x') && ei === i && (ej === j || ej === j + 1)) || (e.startsWith('z') && ej === j && (ei === i || ei === i + 1)));
      });
      if (dependents) return 'Fjern væggene på den først';
      if (piece.id === 'foundation' && [...this.byCell.values(), ...this.roofs.values()].some((p) => p !== piece && p.i === i && p.j === j)) return 'Fjern etager og tag over den først';
    }
    return null;
  }

  // Walls stacked on this wall, with no floor holding them up.
  stackedOn(piece) {
    if (!piece.edge) return false;
    const [axis, rest] = piece.edge.split(':');
    const [i, j, k] = rest.split(',').map(Number);
    const above = `${axis}:${i},${j},${k + 1}`;
    if (!this.byEdge.has(above)) return false;
    const cells = axis === 'x' ? [[i, j], [i, j - 1]] : [[i, j], [i - 1, j]];
    return !cells.some(([ci, cj]) => this.byCell.has(cellKey(ci, cj, k + 1)));
  }

  remove(piece) {
    if (this.lit === piece) this.highlight(null);
    const w = this.world;
    this.root.remove(piece.obj);
    for (const c of piece.colliders) w.colliders.remove(c);
    for (const s of piece.surfaces) w.surfaces.remove(s);
    if (piece.edge) this.byEdge.delete(piece.edge);
    if (piece.id === 'foundation' || piece.id === 'loft') this.byCell.delete(cellKey(piece.i, piece.j, piece.k));
    if (piece.id === 'roof') this.roofs.delete(cellKey(piece.i, piece.j, piece.k));
    if (piece.light) this.lights.splice(this.lights.indexOf(piece.light), 1);
    this.flames = this.flames.filter((f) => f.sprite.parent !== piece.obj);
    this.pieces.splice(this.pieces.indexOf(piece), 1);
  }

  // Nearest placed piece roughly in front of the player (for removal / chest / bed use).
  pieceInFront(player, ids = null, reach = 3.2) {
    let best = null, bd = Infinity;
    const fx = Math.sin(player.facing), fz = Math.cos(player.facing);
    for (const p of this.pieces) {
      if (ids && !ids.includes(p.id)) continue;
      if (Math.abs(p.y - player.pos.y) > (p.id === 'roof' || p.id === 'loft' ? 5 : 2.5)) continue;
      const dx = p.x - player.pos.x, dz = p.z - player.pos.z, d = Math.hypot(dx, dz);
      if (d > reach + (p.id === 'foundation' || p.id === 'loft' || p.id === 'roof' ? 1.5 : 0)) continue;
      const front = d > 0.01 ? (dx * fx + dz * fz) / d : 1;
      if (front < 0.1 && d > 1.2) continue;
      const score = d - front;
      if (score < bd) { bd = score; best = p; }
    }
    return best;
  }

  update(dt, t) {
    for (const f of this.flames) {
      const s = f.base * (1 + 0.12 * Math.sin(t * 13 + f.seed) + 0.08 * Math.sin(t * 7.3 + f.seed * 2));
      f.sprite.scale.set(s, s * 1.25, s);
    }
  }

  serialize() {
    return this.pieces.map((p) => {
      const o = { id: p.id, x: p.x, y: +p.y.toFixed(3), z: p.z, r: +p.rot.toFixed(3) };
      if (p.i !== undefined) { o.i = p.i; o.j = p.j; o.k = p.k; }
      if (p.edge) o.e = p.edge;
      if (p.storage) o.s = p.storage.serialize();
      return o;
    });
  }

  restore(list) {
    // Foundations first so everything else finds its grid.
    const order = ['foundation', 'loft', 'wall', 'doorway', 'window', 'roof'];
    const sorted = [...(list ?? [])].sort((a, b) => (order.indexOf(a.id) + 1 || 99) - (order.indexOf(b.id) + 1 || 99));
    for (const o of sorted) {
      if (!PIECE[o.id] && o.id !== 'loft') continue;
      this.place(o.id, { pos: { x: o.x, y: o.y, z: o.z }, rot: o.r, i: o.i, j: o.j, k: o.k, edge: o.e, top: o.y }, { storage: o.s });
    }
  }
}

function boxCircle(b, x, z, r) {
  const dx = x - b.x, dz = z - b.z;
  const lx = dx * b.c - dz * b.s, lz = dx * b.s + dz * b.c;
  const cx = Math.max(-b.hw, Math.min(b.hw, lx)), cz = Math.max(-b.hd, Math.min(b.hd, lz));
  return Math.hypot(lx - cx, lz - cz) < r;
}
