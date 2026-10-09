// Modular building: foundations on a 4 m world grid, walls on their edges, lofts and
// roofs stacked in 4 m levels, plus free-standing pieces (stairs, fire, chest, bed...).
// A ghost shows where the piece will go: green = valid, red = blocked (with a reason).
import * as THREE from 'three';
import { cloneModel } from '../assets.js';
import { PIECE, GRID, WALL_H } from '../data/build.js';
import { Inventory } from './inventory.js';

const MAX_STEP = 2.1;   // foundation top may sit at most this far above the lowest ground under it
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
        f.position.set(dx, -0.15 - 1.84, dz);
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
      for (let k = 0; k < 8; k++) {
        const s = normalized(a, k % 2 ? 'nature/pebble_a' : 'nature/pebble_b', { scale: 3.2 });
        const ang = (k / 8) * Math.PI * 2;
        s.position.set(Math.cos(ang) * 0.7, 0, Math.sin(ang) * 0.7);
        s.rotation.y = ang * 2.3;
        g.add(s);
      }
      for (let k = 0; k < 2; k++) {
        const log = normalized(a, 'props/lumber', { scale: 1.6 });
        log.rotation.y = k * 1.4 + 0.3;
        log.position.y = 0.02 + k * 0.12;
        g.add(log);
      }
    } else if (id === 'torch') {
      g.add(normalized(a, 'build/torch', { scale: 2 }));
    } else if (id === 'chest') {
      g.add(normalized(a, 'build/chest', { scale: 0.85 }));
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
    this.ghost = { id, obj, rot: 0, plan: null };
  }

  rotateGhost() {
    if (this.ghost) this.ghost.rot = (this.ghost.rot + Math.PI / 4) % (Math.PI * 2);
  }

  updateGhost(player, inventory) {
    const g = this.ghost;
    if (!g) return null;
    const plan = this.plan(g.id, player, g.rot);
    if (plan.ok && !inventory.canAfford(PIECE[g.id].cost)) { plan.ok = false; plan.reason = 'Du mangler materialer'; }
    g.plan = plan;
    g.obj.visible = !!plan.pos;
    if (plan.pos) {
      g.obj.position.set(plan.pos.x, plan.pos.y, plan.pos.z);
      g.obj.rotation.y = plan.rot;
    }
    const mat = plan.ok ? this.ghostMats.ok : this.ghostMats.bad;
    g.obj.traverse((o) => { if (o.isMesh) o.material = mat; });
    return plan;
  }

  // --- Placement rules --------------------------------------------------------------
  aim(player, dist) {
    return { x: player.pos.x + Math.sin(player.facing) * dist, z: player.pos.z + Math.cos(player.facing) * dist };
  }

  levelOf(i, j, y) {
    const f = this.byCell.get(cellKey(i, j, 0));
    if (!f) return 0;
    return Math.max(0, Math.round((y - f.top) / WALL_H));
  }

  baseTop(i, j) {
    return this.byCell.get(cellKey(i, j, 0))?.top;
  }

  plan(id, player, rot) {
    const T = this.world.terrain;
    if (id === 'foundation') {
      const a = this.aim(player, 3.6);
      const i = Math.round(a.x / GRID), j = Math.round(a.z / GRID);
      const x = i * GRID, z = j * GRID;
      const pos = { x, y: 0, z };
      if (this.byCell.has(cellKey(i, j, 0))) return { pos: null, ok: false, reason: 'Der er allerede et fundament' };
      let hMin = Infinity, hMax = -Infinity;
      for (const [dx, dz] of [[-2, -2], [2, -2], [-2, 2], [2, 2], [0, 0], [0, -2], [0, 2], [-2, 0], [2, 0]]) {
        const h = T.heightAt(x + dx * 0.98, z + dz * 0.98);
        hMin = Math.min(hMin, h); hMax = Math.max(hMax, h);
      }
      let top = hMax + LIFT;
      for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const n = this.byCell.get(cellKey(i + di, j + dj, 0));
        if (n && n.top >= hMax - 0.12 && n.top - hMin <= MAX_STEP) { top = n.top; break; }
      }
      pos.y = top;
      const res = { pos, rot: 0, i, j, top };
      if (hMin < -0.2) return { ...res, ok: false, reason: 'For tæt på vandet' };
      if (top - hMin > MAX_STEP) return { ...res, ok: false, reason: 'Jorden er for stejl' };
      if (this.blockedByNature(x, z, 2.1, 2.1, 0)) return { ...res, ok: false, reason: 'Noget står i vejen' };
      return { ...res, ok: true };
    }

    if (id === 'wall' || id === 'doorway' || id === 'window') {
      const a = this.aim(player, 2.4);
      let best = null;
      const ci = Math.round(a.x / GRID), cj = Math.round(a.z / GRID);
      for (let i = ci - 1; i <= ci + 1; i++) for (let j = cj - 1; j <= cj + 1; j++) {
        const top = this.baseTop(i, j);
        if (top === undefined) continue;
        const k = this.levelOf(i, j, player.pos.y + 0.5);
        if (k > 0 && !this.byCell.has(cellKey(i, j, k))) continue;
        const cx = i * GRID, cz = j * GRID;
        for (const e of [
          { key: `x:${i},${j},${k}`, x: cx, z: cz - 2, rot: 0 },
          { key: `x:${i},${j + 1},${k}`, x: cx, z: cz + 2, rot: 0 },
          { key: `z:${i},${j},${k}`, x: cx - 2, z: cz, rot: Math.PI / 2 },
          { key: `z:${i + 1},${j},${k}`, x: cx + 2, z: cz, rot: Math.PI / 2 },
        ]) {
          const d = Math.hypot(e.x - a.x, e.z - a.z);
          if (!best || d < best.d) best = { ...e, d, y: top + k * WALL_H, k };
        }
      }
      if (!best || best.d > 4) return { pos: null, ok: false, reason: 'Byg et fundament først' };
      const res = { pos: { x: best.x, y: best.y, z: best.z }, rot: best.rot, edge: best.key, k: best.k };
      if (this.byEdge.has(best.key)) return { ...res, ok: false, reason: 'Der står allerede en væg' };
      return { ...res, ok: true };
    }

    if (id === 'loft' || id === 'roof') {
      const a = this.aim(player, 2.2);
      const i = Math.round(a.x / GRID), j = Math.round(a.z / GRID);
      const top = this.baseTop(i, j);
      if (top === undefined) return { pos: null, ok: false, reason: 'Skal stå over et fundament' };
      const k = this.levelOf(i, j, player.pos.y + 0.5) + 1;
      const y = top + k * WALL_H;
      const res = { pos: { x: i * GRID, y, z: j * GRID }, rot: id === 'roof' ? rot % Math.PI >= Math.PI / 4 && rot % Math.PI < (3 * Math.PI) / 4 ? Math.PI / 2 : 0 : 0, i, j, k };
      const key = cellKey(i, j, k);
      if (this.byCell.has(key) || this.roofs.has(key)) return { ...res, ok: false, reason: 'Pladsen er optaget' };
      if (id === 'loft') {
        const walls = [`x:${i},${j},${k - 1}`, `x:${i},${j + 1},${k - 1}`, `z:${i},${j},${k - 1}`, `z:${i + 1},${j},${k - 1}`].some((e) => this.byEdge.has(e));
        const neighbor = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([di, dj]) => this.byCell.has(cellKey(i + di, j + dj, k)));
        if (!walls && !neighbor) return { ...res, ok: false, reason: 'Etagen skal hvile på vægge' };
      }
      return { ...res, ok: true };
    }

    // Free pieces
    const def = PIECE[id];
    const a = this.aim(player, Math.max(1.8, def.size[1] / 2 + 1.1));
    const st = def.step ?? 0.25;
    const x = Math.round(a.x / st) * st, z = Math.round(a.z / st) * st;
    const y = this.world.groundAt(x, z, player.pos.y + 0.5);
    const res = { pos: { x, y, z }, rot };
    if (T.heightAt(x, z) < -0.2 && y <= T.heightAt(x, z) + 0.01) return { ...res, ok: false, reason: 'For tæt på vandet' };
    const onFloor = y > T.heightAt(x, z) + 0.05;
    if (!onFloor && T.slopeAt(x, z) > 0.5) return { ...res, ok: false, reason: 'Jorden er for stejl' };
    if (this.blockedByAnything(x, z, def.size[0] / 2, def.size[1] / 2, rot, y)) return { ...res, ok: false, reason: 'Noget står i vejen' };
    return { ...res, ok: true };
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

  // Can this piece be removed without leaving others floating?
  removalBlocker(piece) {
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

  remove(piece) {
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
