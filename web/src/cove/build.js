// Base building in the cove (D-020). A modular kit on a world-aligned 3 m grid with 3 m storeys,
// all from our own faceted generator (game-assets forge-lowpoly b_* pieces):
//   foundation — a plank deck on stilts; the stilts reach down to the ground, so you can build on
//                slopes. Everything else stands on foundations.
//   wall, doorway, window, railing — on the edges of a foundation or a floor, at any storey.
//   door — hangs in a doorway; gate — hangs in a gate frame. Both open away from you.
//   floor — a loft over the walls; it is also the floor of the next storey.
//   roof — a thatch roof over a cell; the open ends get gables by themselves.
//   stairs, pillar, palisade (joins end to end), gate frame, campfire, torch, bed, chest, lean-to —
//                free pieces on the ground or on a floor.
// You aim with the crosshair: a ghost shows the piece, green where it can go, red with a reason.
// R turns it, Esc (or ✕) stops. In tear-down mode the piece you look at is marked and comes down
// with everything it cost given back. You walk on foundations, floors and stairs; walls, doors and
// fences stop you. Doors and gates open with E / a tap, chests hold things, a bed is where you wake.
import * as THREE from 'three';
import { cloneModel } from '../assets.js';
import { prepareModel } from './facets.js';

export const G = 3, H = 3;
const LIFT = 0.25;      // a new foundation's deck above the highest ground under it
const MAX_DEPTH = 3.6;  // ... and at most this far above the lowest
const STEP_UP = 1.05;   // how high a deck or floor edge you can climb onto (there is no jump)
const BODY = 1.75;      // the player's height (for walls above / below)
const ckey = (i, j, k = 0) => `${i},${j},${k}`;

export const PIECES = [
  { id: 'foundation', name: 'Fundament', model: 'build/foundation', cost: { wood: 6, stone: 2 }, snap: 'foundation', note: 'Gulv på pæle — alt bygges på det' },
  { id: 'wall', name: 'Væg', model: 'build/wall', cost: { bamboo: 4, wood: 2, rope: 1 }, snap: 'edge' },
  { id: 'doorway', name: 'Dørkarm', model: 'build/doorway', cost: { bamboo: 3, wood: 2, rope: 1 }, snap: 'edge', note: 'Væg med åbning' },
  { id: 'door', name: 'Dør', model: 'build/door', cost: { wood: 4, rope: 1 }, snap: 'door', note: 'Hænger i en dørkarm' },
  { id: 'window', name: 'Vindue', model: 'build/window', cost: { bamboo: 4, wood: 2, rope: 1 }, snap: 'edge' },
  { id: 'floor', name: 'Loft / etage', model: 'build/floor', cost: { wood: 5 }, snap: 'level', note: 'Over væggene — gulv på næste etage' },
  { id: 'roof', name: 'Stråtag', model: 'build/roof', cost: { palm_leaf: 12, bamboo: 2, rope: 1 }, snap: 'roof' },
  { id: 'stairs', name: 'Trappe', model: 'build/stairs', cost: { wood: 6 }, snap: 'free', size: [1.5, 3.1], step: 0.25, turn: Math.PI / 2, note: 'Op til næste etage' },
  { id: 'railing', name: 'Rækværk', model: 'build/railing', cost: { bamboo: 2, wood: 1 }, snap: 'edge' },
  { id: 'pillar', name: 'Stolpe', model: 'build/pillar', cost: { wood: 2 }, snap: 'free', size: [0.35, 0.35], step: 0.25 },
  { id: 'palisade', name: 'Palisade', model: 'build/palisade', cost: { wood: 6, rope: 1 }, snap: 'fence', size: [3, 0.36], step: 0.5, note: 'Sættes ende mod ende' },
  { id: 'gate_frame', name: 'Portåbning', model: 'build/gate_frame', cost: { wood: 4, rope: 1 }, snap: 'fence', size: [3, 0.4], step: 0.5, note: 'I palisaden' },
  { id: 'gate', name: 'Port', model: 'build/gate', cost: { wood: 5, rope: 2 }, snap: 'gate', note: 'Hænger i en portåbning' },
  { id: 'campfire', name: 'Bål', model: 'build/campfire', cost: { wood: 3, stone: 5 }, snap: 'free', size: [1.8, 1.8], step: 0.25, fire: 'big' },
  { id: 'torch', name: 'Fakkel', model: 'build/torch', cost: { wood: 1, fiber: 3 }, snap: 'free', size: [0.3, 0.3], step: 0.25, fire: 'small' },
  { id: 'bed', name: 'Seng', model: 'build/bed', cost: { bamboo: 4, palm_leaf: 8, fiber: 4 }, snap: 'free', size: [1.3, 2.25], step: 0.25, use: 'bed', note: 'Her vågner du' },
  { id: 'chest', name: 'Kiste', model: 'build/chest', cost: { wood: 8, rope: 1 }, snap: 'free', size: [1.26, 0.7], step: 0.25, use: 'chest', note: 'Opbevaring' },
  { id: 'lean_to', name: 'Læ', model: 'build/lean_to', cost: { bamboo: 6, palm_leaf: 10, rope: 2 }, snap: 'free', size: [3.2, 2.6], step: 0.5, pass: true },
];
export const PIECE = Object.fromEntries(PIECES.map((p) => [p.id, p]));

// Doorway / gate-frame openings: where the leaf hangs (hinge x) and how wide it is.
const LEAF = { door: { hinge: -0.575, w: 1.15, h: 2.25, frame: 'doorway' }, gate: { hinge: -1.27, w: 2.55, h: 2.25, frame: 'gate_frame' } };

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

// Circle (x, z, r) against an oriented box.
function hitsBox(b, x, z, r) {
  const dx = x - b.x, dz = z - b.z;
  const lx = dx * b.c - dz * b.s, lz = dx * b.s + dz * b.c;
  const cx = Math.max(-b.hw, Math.min(b.hw, lx)), cz = Math.max(-b.hd, Math.min(b.hd, lz));
  return Math.hypot(lx - cx, lz - cz) < r;
}
function inBox(b, x, z, pad = 0) {
  const dx = x - b.x, dz = z - b.z;
  const lx = dx * b.c - dz * b.s, lz = dx * b.s + dz * b.c;
  return Math.abs(lx) <= b.hw + pad && Math.abs(lz) <= b.hd + pad ? { lx, lz } : null;
}
// Two oriented boxes overlap? (separating axes, 2D)
function boxesOverlap(a, b) {
  const axes = [[a.c, -a.s], [a.s, a.c], [b.c, -b.s], [b.s, b.c]];
  const corners = (q) => [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([u, v]) => [q.x + (u * q.hw * q.c + v * q.hd * q.s), q.z + (-u * q.hw * q.s + v * q.hd * q.c)]);
  const ca = corners(a), cb = corners(b);
  for (const [ax, az] of axes) {
    const pa = ca.map(([x, z]) => x * ax + z * az), pb = cb.map(([x, z]) => x * ax + z * az);
    if (Math.max(...pa) <= Math.min(...pb) || Math.max(...pb) <= Math.min(...pa)) return false;
  }
  return true;
}

// A coarse spatial hash for the boxes you bump into and the surfaces you stand on.
class Hash {
  constructor(cell = 6) { this.cell = cell; this.map = new Map(); }
  keys(x, z, r) {
    const out = [], C = this.cell;
    for (let i = Math.floor((x - r) / C); i <= Math.floor((x + r) / C); i++) for (let j = Math.floor((z - r) / C); j <= Math.floor((z + r) / C); j++) out.push(`${i},${j}`);
    return out;
  }
  add(o) {
    o.r = Math.hypot(o.hw, o.hd);
    o.keys = this.keys(o.x, o.z, o.r);
    for (const k of o.keys) { let a = this.map.get(k); if (!a) this.map.set(k, (a = [])); a.push(o); }
    return o;
  }
  remove(o) { for (const k of o.keys ?? []) { const a = this.map.get(k); if (a) a.splice(a.indexOf(o), 1); } }
  near(x, z, r) {
    const out = new Set();
    for (const k of this.keys(x, z, r)) for (const o of this.map.get(k) ?? []) out.add(o);
    return out;
  }
}

export class Building {
  constructor({ scene, assets, island, flora, camera }) {
    Object.assign(this, { scene, assets, island, flora, camera });
    this.root = new THREE.Group();
    this.root.name = 'buildings';
    scene.add(this.root);
    this.pieces = [];
    this.byCell = new Map();  // foundations "i,j,0", floors "i,j,k"
    this.byEdge = new Map();  // "x:i,j,k" | "z:i,j,k" → wall / doorway / window / railing
    this.roofs = new Map();   // "i,j,k"
    this.gables = new THREE.Group();
    this.root.add(this.gables);
    this.boxes = new Hash();
    this.floors = new Hash();
    this.mode = null;         // null | { id } (placing) | { tear: true }
    this.rot = 0;
    this.useTarget = null;
    this.flameMat = new THREE.SpriteMaterial({ map: flameTexture(), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, fog: true });
    this.flames = [];
    // A fixed pool of fire lights (changing the number of lights would recompile every shader).
    this.lights = [0, 1].map(() => { const l = new THREE.PointLight(0xffa04a, 0, 13, 1.6); scene.add(l); return l; });
    this.ghostMats = {
      ok: new THREE.MeshStandardMaterial({ color: '#7fe0c0', transparent: true, opacity: 0.45, depthWrite: false, emissive: '#2c7d68', emissiveIntensity: 0.6 }),
      bad: new THREE.MeshStandardMaterial({ color: '#ff7a5c', transparent: true, opacity: 0.45, depthWrite: false, emissive: '#8a2a12', emissiveIntensity: 0.6 }),
    };
    this.ray = new THREE.Raycaster();
    this.spawn = null;        // where you wake (a bed)
    this.changed = () => {};
  }

  // ---- visuals ---------------------------------------------------------------------------------
  model(key, center = false) {
    const o = cloneModel(this.assets, key);
    prepareModel(o);
    if (!center) return o;
    o.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(o), c = box.getCenter(new THREE.Vector3());
    o.position.set(-c.x, -box.min.y, -c.z);
    const g = new THREE.Group();
    g.add(o);
    return g;
  }

  visual(id) {
    const def = PIECE[id], g = new THREE.Group();
    if (id === 'foundation') {
      g.add(this.model('build/foundation'));
      for (const [dx, dz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
        const p = this.model('build/post');
        p.userData.post = true;
        p.position.set(dx * (G / 2 - 0.14), -0.28, dz * (G / 2 - 0.14));
        g.add(p);
      }
    } else if (id === 'door' || id === 'gate') {
      const L = LEAF[id], pivot = new THREE.Group();
      pivot.position.x = L.hinge;
      pivot.add(this.model(def.model));
      pivot.userData.leaf = true;
      g.add(pivot);
    } else if (def.snap === 'free') {
      g.add(this.model(def.model, true));
    } else {
      g.add(this.model(def.model));
    }
    return g;
  }

  setPosts(obj, depth) {
    for (const p of obj.children) if (p.userData.post) p.scale.y = Math.max(0.3, depth + 0.1);
  }

  // ---- modes -----------------------------------------------------------------------------------
  start(id) {
    this.stop();
    this.mode = { id };
    const obj = this.visual(id);
    obj.traverse((o) => { if (o.isMesh) { o.castShadow = false; o.receiveShadow = false; o.renderOrder = 5; } });
    this.root.add(obj);
    this.ghost = { id, obj, plan: null };
  }

  tearDown() { this.stop(); this.mode = { tear: true }; }

  stop() {
    if (this.ghost) this.ghost.obj.removeFromParent();
    this.ghost = null;
    this.mode = null;
    this.mark(null);
  }

  turn() { this.rot = (this.rot + (PIECE[this.mode?.id]?.turn ?? Math.PI / 4)) % (Math.PI * 2); }

  // ---- what the crosshair points at --------------------------------------------------------------
  // The first ground or floor along the view ray (within reach), with its storey.
  aim(reach = 9) {
    const cam = this.camera, p = cam.position;
    const d = new THREE.Vector3(0, 0, -1).applyQuaternion(cam.quaternion);
    const fl = new THREE.Vector2(d.x, d.z);
    const flen = fl.length() || 1;
    let hit = null;
    for (let s = 0.4; s <= reach; s += 0.2) {
      const x = p.x + d.x * s, y = p.y + d.y * s, z = p.z + d.z * s;
      const g = this.standAt(x, z, y + 0.05);
      if (y <= g.h) { hit = { x, z, y: g.h, k: g.k }; break; }
    }
    if (!hit) {
      const s = Math.min(reach, 5), x = p.x + d.x * s, z = p.z + d.z * s;
      const g = this.standAt(x, z, p.y - 1.2);
      hit = { x, z, y: g.h, k: g.k };
    }
    return { ...hit, vx: fl.x / flen, vz: fl.y / flen, rot: this.rot };
  }

  // Ground or building floor under (x, z) at or below height y, and which storey that is.
  standAt(x, z, y) {
    let h = this.island.heightAt(x, z), k = 0;
    for (const s of this.floors.near(x, z, 0)) {
      const l = inBox(s, x, z);
      if (!l) continue;
      const sh = s.h(l.lx, l.lz);
      if (sh <= y && sh > h) { h = sh; k = s.k ?? this.levelAt(x, z, sh); }
    }
    return { h, k };
  }

  // For the walker: the floor you're on (or can step up onto).
  groundAt(x, z, feet) { return this.standAt(x, z, feet + STEP_UP).h; }

  blockedAt(x, z, r, feet) {
    for (const b of this.boxes.near(x, z, r)) {
      if (b.off) continue;
      if (feet >= b.top - 0.05 || feet + BODY <= b.bottom) continue;
      if (b.step && feet >= b.top - STEP_UP) continue;
      if (hitsBox(b, x, z, r)) return true;
    }
    return false;
  }

  baseTop(i, j) { return this.byCell.get(ckey(i, j, 0))?.top; }

  levelAt(x, z, y) {
    const top = this.baseTop(Math.round(x / G), Math.round(z / G));
    return top === undefined ? 0 : Math.max(0, Math.round((y - top) / H));
  }

  // ---- placement rules ---------------------------------------------------------------------------
  pickCell(a, want, radius = 1) {
    const ci = Math.round(a.x / G), cj = Math.round(a.z / G);
    let best = null;
    for (let i = ci - radius; i <= ci + radius; i++) for (let j = cj - radius; j <= cj + radius; j++) {
      const w = want(i, j);
      if (w === null) continue;
      const dx = i * G - a.x, dz = j * G - a.z, d = Math.hypot(dx, dz);
      const ahead = d > 0.01 ? (dx * a.vx + dz * a.vz) / d : 0;
      const score = d - ahead * 0.7 + (w ? 0 : 5);
      if (!best || score < best.score) best = { i, j, free: w, score, d };
    }
    return best;
  }

  plan(id, a) {
    const def = PIECE[id], I = this.island;
    const L = a.k ?? 0;

    if (id === 'foundation') {
      const cell = this.pickCell(a, (i, j) => !this.byCell.has(ckey(i, j, 0)));
      if (!cell) return { ok: false, reason: 'Ingen plads her' };
      const { i, j } = cell, x = i * G, z = j * G;
      let hMin = Infinity, hMax = -Infinity;
      for (const [dx, dz] of [[-1, -1], [1, -1], [-1, 1], [1, 1], [0, 0], [0, -1], [0, 1], [-1, 0], [1, 0]]) {
        const h = I.heightAt(x + dx * G * 0.49, z + dz * G * 0.49);
        hMin = Math.min(hMin, h); hMax = Math.max(hMax, h);
      }
      let top = hMax + LIFT;
      for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const n = this.byCell.get(ckey(i + di, j + dj, 0));
        if (n && n.top >= hMax + 0.05 && n.top - hMin <= MAX_DEPTH) { top = n.top; break; }
      }
      const res = { pos: { x, y: top, z }, rot: 0, i, j, top, depth: top - hMin };
      if (!cell.free) return { ...res, ok: false, reason: 'Der er allerede et fundament' };
      if (hMin < 0.15) return { ...res, ok: false, reason: 'For tæt på vandet' };
      if (top - hMin > MAX_DEPTH) return { ...res, ok: false, reason: 'For stejlt her' };
      if (this.flora.blocked(x, z, G * 0.42)) return { ...res, ok: false, reason: 'Et træ eller en sten står i vejen — hug det først' };
      if (this.overlaps({ x, z, hw: G / 2 - 0.1, hd: G / 2 - 0.1, c: 1, s: 0 }, top - 0.3, (b) => b.piece.id !== 'foundation')) return { ...res, ok: false, reason: 'Noget står i vejen' };
      return { ...res, ok: true };
    }

    if (def.snap === 'edge') {
      const cx0 = a.x + a.vx * 0.4, cz0 = a.z + a.vz * 0.4;
      const ci = Math.round(a.x / G), cj = Math.round(a.z / G);
      const seen = new Set();
      let best = null, bestTaken = null;
      for (let i = ci - 1; i <= ci + 1; i++) for (let j = cj - 1; j <= cj + 1; j++) {
        const top = this.baseTop(i, j);
        if (top === undefined) continue;
        const cx = i * G, cz = j * G;
        for (const e of [
          { key: `x:${i},${j},${L}`, below: `x:${i},${j},${L - 1}`, x: cx, z: cz - G / 2, rot: 0, nx: 0, nz: 1 },
          { key: `x:${i},${j + 1},${L}`, below: `x:${i},${j + 1},${L - 1}`, x: cx, z: cz + G / 2, rot: 0, nx: 0, nz: 1 },
          { key: `z:${i},${j},${L}`, below: `z:${i},${j},${L - 1}`, x: cx - G / 2, z: cz, rot: Math.PI / 2, nx: 1, nz: 0 },
          { key: `z:${i + 1},${j},${L}`, below: `z:${i + 1},${j},${L - 1}`, x: cx + G / 2, z: cz, rot: Math.PI / 2, nx: 1, nz: 0 },
        ]) {
          if (seen.has(e.key)) continue;
          seen.add(e.key);
          if (L > 0 && !this.byCell.has(ckey(i, j, L)) && !this.byEdge.has(e.below)) continue;
          const d = Math.hypot(e.x - cx0, e.z - cz0);
          const facing = Math.abs(e.nx * a.vx + e.nz * a.vz);
          const cand = { ...e, d, score: d + (1 - facing) * 1.1, y: top + L * H };
          if (this.byEdge.has(e.key)) { if (!bestTaken || cand.score < bestTaken.score) bestTaken = cand; }
          else if (!best || cand.score < best.score) best = cand;
        }
      }
      const pick = best && best.d < 3.4 ? best : bestTaken;
      if (!pick || pick.d > 3.4) return { ok: false, reason: L > 0 ? 'Byg et loft eller en væg nedenunder først' : 'Byg et fundament først' };
      const res = { pos: { x: pick.x, y: pick.y, z: pick.z }, rot: pick.rot, edge: pick.key, k: L };
      if (pick === bestTaken) return { ...res, ok: false, reason: 'Her står allerede en væg' };
      return { ...res, ok: true };
    }

    if (def.snap === 'door' || def.snap === 'gate') {
      const frame = LEAF[id].frame;
      let best = null;
      for (const p of this.pieces) {
        if (p.id !== frame) continue;
        const d = Math.hypot(p.x - a.x, p.z - a.z) + Math.abs(p.y - a.y) * 0.5;
        if (d < 3.5 && (!best || (!!best.p.leaf > !!p.leaf) || (!!best.p.leaf === !!p.leaf && d < best.d))) best = { p, d };
      }
      if (!best) return { ok: false, reason: id === 'door' ? 'Sigt på en dørkarm' : 'Sigt på en portåbning' };
      const f = best.p;
      const res = { pos: { x: f.x, y: f.y, z: f.z }, rot: f.rot, frame: f };
      if (f.leaf) return { ...res, ok: false, reason: id === 'door' ? 'Der er allerede en dør' : 'Der er allerede en port' };
      return { ...res, ok: true };
    }

    if (def.snap === 'level' || def.snap === 'roof') {
      const k = L + 1;
      const taken = (i, j) => this.byCell.has(ckey(i, j, k)) || this.roofs.has(ckey(i, j, k));
      const cell = this.pickCell(a, (i, j) => (this.baseTop(i, j) === undefined ? null : !taken(i, j)));
      if (!cell || cell.d > 3.6) return { ok: false, reason: 'Skal stå over et fundament' };
      const { i, j } = cell;
      const y = this.baseTop(i, j) + k * H;
      const r = ((a.rot % Math.PI) + Math.PI) % Math.PI;
      const res = { pos: { x: i * G, y, z: j * G }, rot: id === 'roof' && r >= Math.PI / 4 && r < (3 * Math.PI) / 4 ? Math.PI / 2 : 0, i, j, k };
      if (!cell.free) return { ...res, ok: false, reason: 'Pladsen er optaget' };
      const walls = [`x:${i},${j},${k - 1}`, `x:${i},${j + 1},${k - 1}`, `z:${i},${j},${k - 1}`, `z:${i + 1},${j},${k - 1}`].some((e) => this.byEdge.has(e));
      const pillars = this.pieces.some((p) => p.id === 'pillar' && Math.abs(p.x - i * G) <= G / 2 + 0.2 && Math.abs(p.z - j * G) <= G / 2 + 0.2 && Math.abs(p.y + H - y) < 0.4);
      const neighbor = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([di, dj]) => this.byCell.has(ckey(i + di, j + dj, k)) || this.roofs.has(ckey(i + di, j + dj, k)));
      if (!walls && !pillars && !neighbor) return { ...res, ok: false, reason: id === 'roof' ? 'Taget skal hvile på vægge eller stolper' : 'Loftet skal hvile på vægge eller stolper' };
      return { ...res, ok: true };
    }

    // Free pieces (and fences): on the ground or on a floor.
    const st = def.step ?? 0.25;
    let x = Math.round(a.x / st) * st, z = Math.round(a.z / st) * st, rot = a.rot;
    if (def.snap === 'fence') { const s = this.fenceSnap(a); if (s) ({ x, z, rot } = s); }
    const g = this.standAt(x, z, a.y + 0.3);
    const y = g.h, ground = I.heightAt(x, z);
    const res = { pos: { x, y, z }, rot };
    if (ground < 0.1 && y <= ground + 0.01) return { ...res, ok: false, reason: 'For tæt på vandet' };
    const onFloor = y > ground + 0.05;
    if (!onFloor && I.slopeAt(x, z) > 0.55) return { ...res, ok: false, reason: 'Jorden er for stejl' };
    const [w, d] = def.size;
    if (!onFloor && this.flora.blocked(x, z, Math.min(w, d) * 0.4)) return { ...res, ok: false, reason: 'Noget står i vejen — hug det først' };
    const probe = { x, z, hw: w / 2 * 0.9, hd: d / 2 * 0.9, c: Math.cos(rot), s: Math.sin(rot) };
    if (this.overlaps(probe, y)) return { ...res, ok: false, reason: 'Noget står i vejen' };
    return { ...res, ok: true };
  }

  overlaps(probe, y, only = null) {
    for (const b of this.boxes.near(probe.x, probe.z, Math.hypot(probe.hw, probe.hd))) {
      if (only && !only(b)) continue;
      if (y >= b.top - 0.05 || y + 1.5 <= b.bottom) continue;
      if (boxesOverlap(probe, b)) return true;
    }
    return false;
  }

  // Palisades and gate frames join end to end, straight on or at a right angle.
  fenceSnap(a) {
    let best = null;
    for (const f of this.pieces) {
      if (PIECE[f.id].snap !== 'fence' || Math.hypot(f.x - a.x, f.z - a.z) > 6) continue;
      const c = Math.cos(f.rot), s = Math.sin(f.rot), ax = c, az = -s, px = s, pz = c, Hl = G / 2;
      const cands = [];
      for (const e of [-1, 1]) {
        cands.push({ x: f.x + ax * e * G, z: f.z + az * e * G, rot: f.rot });
        for (const side of [-1, 1]) cands.push({ x: f.x + ax * e * Hl + px * side * Hl, z: f.z + az * e * Hl + pz * side * Hl, rot: f.rot + Math.PI / 2 });
      }
      for (const cnd of cands) {
        if (this.pieces.some((p) => PIECE[p.id].snap === 'fence' && Math.hypot(p.x - cnd.x, p.z - cnd.z) < 0.5)) continue;
        const d = Math.hypot(cnd.x - a.x, cnd.z - a.z);
        if (d < 1.8 && (!best || d < best.d)) best = { ...cnd, d };
      }
    }
    return best;
  }

  // Ghost each frame while placing; the marked piece while tearing down; doors etc. to use.
  update(dt, t, inv) {
    const m = this.mode;
    if (m?.id && this.ghost) {
      const a = this.aim();
      const plan = this.plan(m.id, a);
      if (plan.ok && !this.canPay(m.id, inv)) { plan.ok = false; plan.reason = 'Du mangler materialer'; }
      this.ghost.plan = plan;
      const o = this.ghost.obj;
      o.visible = !!plan.pos;
      if (plan.pos) {
        o.position.set(plan.pos.x, plan.pos.y, plan.pos.z);
        o.rotation.y = plan.rot;
        if (m.id === 'foundation') this.setPosts(o, plan.depth);
      }
      const mat = plan.ok ? this.ghostMats.ok : this.ghostMats.bad;
      o.traverse((q) => { if (q.isMesh) q.material = mat; });
    }
    if (m?.tear) this.mark(this.pick(6));
    this.useTarget = m ? null : this.pick(2.8, (p) => PIECE[p.id].use || p.id === 'door' || p.id === 'gate');
    // Flames flicker; the fire lights go to the two fires nearest to you.
    for (const f of this.flames) {
      const s = f.base * (1 + 0.12 * Math.sin(t * 13 + f.seed) + 0.08 * Math.sin(t * 7.3 + f.seed * 2));
      f.sprite.scale.set(s, s * 1.3, s);
    }
    const p = this.camera.position;
    const fires = this.pieces.filter((q) => q.fire).sort((u, v) => Math.hypot(u.x - p.x, u.z - p.z) - Math.hypot(v.x - p.x, v.z - p.z));
    this.lights.forEach((l, i) => {
      const f = fires[i];
      l.intensity = f ? (f.fire === 'big' ? 26 : 9) * (1 + 0.1 * Math.sin(t * 11 + i)) : 0;
      if (f) l.position.set(f.x, f.y + (f.fire === 'big' ? 0.8 : 1.8), f.z);
    });
    // Swinging doors and gates.
    for (const q of this.pieces) if (q.leafPivot) {
      const want = q.open ? q.openDir * 1.75 : 0;
      q.leafPivot.rotation.y += (want - q.leafPivot.rotation.y) * Math.min(1, dt * 8);
    }
  }

  // The placed piece under the crosshair (ray against the piece models), within reach.
  pick(reach, filter = null) {
    const p = this.camera.position;
    const objs = this.pieces.filter((q) => Math.hypot(q.x - p.x, q.z - p.z) < reach + 4 && (!filter || filter(q))).map((q) => q.obj);
    if (!objs.length) return null;
    this.ray.setFromCamera(new THREE.Vector2(0, 0), this.camera);
    this.ray.far = reach;
    const hit = this.ray.intersectObjects(objs, true)[0];
    if (!hit) return null;
    let o = hit.object;
    while (o && !o.userData.piece) o = o.parent;
    return o?.userData.piece ?? null;
  }

  mark(piece) {
    if (this.marked === piece) return;
    if (this.marked) this.marked.obj.traverse((o) => { if (o.isMesh && o.userData.mat) { o.material = o.userData.mat; delete o.userData.mat; } });
    this.marked = piece;
    if (piece) piece.obj.traverse((o) => { if (o.isMesh) { o.userData.mat = o.material; o.material = this.ghostMats.bad; } });
  }

  // A lean-to made earlier as a kit (an item in the bag) pays for itself.
  kit(id, inv) { return id === 'lean_to' && inv.count('lean_to') > 0; }

  canPay(id, inv) { return this.kit(id, inv) || Object.entries(PIECE[id].cost).every(([k, n]) => inv.count(k) >= n); }

  // Place the ghost (if it can go there and you can pay). Returns a message or null.
  commit(inv) {
    const g = this.ghost;
    if (!g?.plan) return null;
    if (!g.plan.ok) return { warn: true, text: g.plan.reason ?? 'Kan ikke bygges her' };
    if (this.kit(g.id, inv)) inv.remove('lean_to', 1);
    else for (const [k, n] of Object.entries(PIECE[g.id].cost)) inv.remove(k, n);
    this.place(g.id, g.plan);
    this.changed();
    return { text: `${PIECE[g.id].name} bygget` };
  }

  // Take the marked piece down and give back what it cost.
  removeMarked(inv) {
    const p = this.marked;
    if (!p) return { warn: true, text: 'Sigt på det, du vil rive ned' };
    const why = this.removalBlocker(p);
    if (why) return { warn: true, text: why };
    this.mark(null);
    this.remove(p);
    inv.add({ ...PIECE[p.id].cost });
    if (p.storage) inv.add(p.storage);
    this.changed();
    return { text: `${PIECE[p.id].name} revet ned — materialerne er tilbage i rygsækken` };
  }

  // ---- place / remove ----------------------------------------------------------------------------
  addBox(piece, x, z, hw, hd, rot, bottom, top, extra = {}) {
    const b = this.boxes.add({ x, z, hw, hd, c: Math.cos(rot), s: Math.sin(rot), bottom, top, piece, ...extra });
    piece.boxes.push(b);
    return b;
  }

  addFloor(piece, x, z, hw, hd, rot, h, k) {
    const s = this.floors.add({ x, z, hw, hd, c: Math.cos(rot), s: Math.sin(rot), h, k, piece });
    piece.floors.push(s);
  }

  place(id, plan, extra = {}) {
    const obj = this.visual(id);
    obj.position.set(plan.pos.x, plan.pos.y, plan.pos.z);
    obj.rotation.y = plan.rot;
    this.root.add(obj);
    const piece = { id, x: plan.pos.x, y: plan.pos.y, z: plan.pos.z, rot: plan.rot, obj, boxes: [], floors: [] };
    obj.userData.piece = piece;
    const { x, y, z, rot } = piece, c = Math.cos(rot), s = Math.sin(rot);
    const along = (d) => [x + c * d, z - s * d]; // a point d metres along the piece's own x axis

    if (id === 'foundation') {
      Object.assign(piece, { i: plan.i, j: plan.j, k: 0, top: y, depth: plan.depth ?? 1 });
      this.setPosts(obj, piece.depth);
      this.byCell.set(ckey(plan.i, plan.j, 0), piece);
      this.addBox(piece, x, z, G / 2, G / 2, 0, -1e4, y, { step: true });
      this.addFloor(piece, x, z, G / 2, G / 2, 0, () => y, 0);
    } else if (id === 'floor') {
      Object.assign(piece, { i: plan.i, j: plan.j, k: plan.k });
      this.byCell.set(ckey(plan.i, plan.j, plan.k), piece);
      this.addBox(piece, x, z, G / 2, G / 2, 0, y - 0.25, y, { step: true });
      this.addFloor(piece, x, z, G / 2, G / 2, 0, () => y, plan.k);
    } else if (id === 'roof') {
      Object.assign(piece, { i: plan.i, j: plan.j, k: plan.k });
      this.roofs.set(ckey(plan.i, plan.j, plan.k), piece);
      this.gableUp();
    } else if (id === 'wall' || id === 'window') {
      piece.edge = plan.edge;
      this.byEdge.set(plan.edge, piece);
      this.addBox(piece, x, z, G / 2, 0.13, rot, y, y + H);
    } else if (id === 'railing') {
      piece.edge = plan.edge;
      this.byEdge.set(plan.edge, piece);
      this.addBox(piece, x, z, G / 2, 0.1, rot, y, y + 1.05);
    } else if (id === 'doorway') {
      piece.edge = plan.edge;
      this.byEdge.set(plan.edge, piece);
      for (const side of [-1, 1]) { const [bx, bz] = along(side * 1.06); this.addBox(piece, bx, bz, 0.44, 0.13, rot, y, y + H); }
      this.addBox(piece, x, z, G / 2, 0.13, rot, y + 2.28, y + H);
    } else if (id === 'door' || id === 'gate') {
      const f = plan.frame ?? this.pieces.find((p) => p.id === LEAF[id].frame && Math.abs(p.x - x) < 0.01 && Math.abs(p.z - z) < 0.01 && Math.abs(p.y - y) < 0.01);
      piece.frame = f;
      if (f) f.leaf = piece;
      piece.leafPivot = obj.children[0];
      piece.open = !!extra.open;
      piece.openDir = extra.openDir ?? 1;
      piece.door = this.addBox(piece, x, z, LEAF[id].w / 2, 0.14, rot, y, y + LEAF[id].h, { off: piece.open });
    } else if (id === 'stairs') {
      // Rises 3 m along its own +z (from −1.5 to +1.5).
      this.addFloor(piece, x, z, 0.72, 1.55, rot, (lx, lz) => y + Math.min(H, Math.max(0, (lz + 1.5) / 3 * H)), undefined);
      for (const side of [-1, 1]) { const [bx, bz] = along(side * 0.78); this.addBox(piece, bx, bz, 0.06, 1.5, rot, y + 0.9, y + H + 1); }
    } else if (id === 'gate_frame') {
      for (const side of [-1, 1]) { const [bx, bz] = along(side * 1.34); this.addBox(piece, bx, bz, 0.18, 0.18, rot, y - 0.2, y + 2.9); }
      this.addBox(piece, x, z, G / 2, 0.15, rot, y + 2.58, y + 2.85);
    } else if (!PIECE[id].pass) {
      const [w, d] = PIECE[id].size;
      const top = { palisade: 2.4, pillar: H, campfire: 0.5, torch: 1.7, bed: 0.5, chest: 0.75 }[id] ?? 1;
      this.addBox(piece, x, z, w / 2, d / 2, rot, y - 0.2, y + top);
    }
    const def = PIECE[id];
    if (def.fire) {
      const fy = def.fire === 'big' ? 0.5 : 1.62;
      const flame = new THREE.Sprite(this.flameMat);
      flame.position.set(def.fire === 'big' ? 0 : 0.045, fy, 0);
      flame.scale.setScalar(def.fire === 'big' ? 1.3 : 0.5);
      obj.add(flame);
      this.flames.push({ sprite: flame, base: flame.scale.x, seed: Math.random() * 10 });
      piece.fire = def.fire;
    }
    if (id === 'chest') piece.storage = { ...(extra.storage ?? {}) };
    if (id === 'bed' && extra.home) this.spawn = piece;
    this.pieces.push(piece);
    return piece;
  }

  // Gable ends wherever a roof's ridge has no roof continuing it.
  gableUp() {
    this.gables.clear();
    for (const r of this.roofs.values()) {
      const along = Math.abs(Math.sin(r.rot)) > 0.5 ? [0, 1] : [1, 0]; // ridge along x (rot 0) or z
      for (const e of [-1, 1]) {
        const n = this.roofs.get(ckey(r.i + along[0] * e, r.j + along[1] * e, r.k));
        if (n && Math.abs(Math.sin(n.rot - r.rot)) < 0.5) continue;
        const g = this.model('build/gable');
        g.position.set(r.x + along[0] * e * G / 2, r.y, r.z + along[1] * e * G / 2);
        g.rotation.y = r.rot;
        this.gables.add(g);
      }
    }
  }

  removalBlocker(piece) {
    if (piece.leaf) return 'Tag døren / porten ned først';
    if (piece.edge) {
      const [axis, rest] = piece.edge.split(':');
      const [i, j, k] = rest.split(',').map(Number);
      if (this.byEdge.has(`${axis}:${i},${j},${k + 1}`)) {
        const cells = axis === 'x' ? [[i, j], [i, j - 1]] : [[i, j], [i - 1, j]];
        if (!cells.some(([ci, cj]) => this.byCell.has(ckey(ci, cj, k + 1)))) return 'Riv væggen ovenpå ned først';
      }
    }
    if (piece.id === 'foundation' || piece.id === 'floor') {
      const { i, j, k } = piece;
      const onIt = [...this.byEdge.keys()].some((e) => {
        const [ax, rest] = e.split(':');
        const [ei, ej, ek] = rest.split(',').map(Number);
        return ek === k && ((ax === 'x' && ei === i && (ej === j || ej === j + 1)) || (ax === 'z' && ej === j && (ei === i || ei === i + 1)));
      });
      if (onIt) return 'Riv væggene på den ned først';
      if (piece.id === 'foundation' && [...this.byCell.values(), ...this.roofs.values()].some((p) => p !== piece && p.i === i && p.j === j)) return 'Riv lofter og tag over den ned først';
      const cx = i * G, cz = j * G;
      if (this.pieces.some((p) => PIECE[p.id].snap === 'free' && Math.abs(p.x - cx) < G / 2 && Math.abs(p.z - cz) < G / 2 && Math.abs(p.y - piece.y) < 0.2)) return 'Fjern det, der står på den, først';
    }
    if (piece.id === 'gate_frame' && piece.leaf) return 'Tag porten ned først';
    return null;
  }

  remove(piece) {
    if (this.marked === piece) this.mark(null);
    piece.obj.removeFromParent();
    for (const b of piece.boxes) this.boxes.remove(b);
    for (const s of piece.floors) this.floors.remove(s);
    if (piece.edge) this.byEdge.delete(piece.edge);
    if (piece.id === 'foundation' || piece.id === 'floor') this.byCell.delete(ckey(piece.i, piece.j, piece.k));
    if (piece.id === 'roof') { this.roofs.delete(ckey(piece.i, piece.j, piece.k)); this.gableUp(); }
    if (piece.frame) piece.frame.leaf = null;
    if (piece.fire) this.flames = this.flames.filter((f) => f.sprite.parent !== piece.obj);
    if (this.spawn === piece) this.spawn = null;
    this.pieces.splice(this.pieces.indexOf(piece), 1);
  }

  // Doors and gates swing away from you; chests and beds are handled by the caller.
  toggle(piece) {
    if (!piece.leafPivot) return;
    const p = this.camera.position;
    if (!piece.open) {
      // Which side are you on? Open the other way.
      const nx = Math.sin(piece.rot), nz = Math.cos(piece.rot);
      piece.openDir = (p.x - piece.x) * nx + (p.z - piece.z) * nz > 0 ? 1 : -1; // + swings the leaf to the piece's −z side
    }
    piece.open = !piece.open;
    piece.door.off = piece.open;
    this.changed();
  }

  // ---- saving ------------------------------------------------------------------------------------
  serialize() {
    return this.pieces.map((p) => {
      const o = { id: p.id, x: +p.x.toFixed(3), y: +p.y.toFixed(3), z: +p.z.toFixed(3), r: +p.rot.toFixed(4) };
      if (p.i !== undefined) Object.assign(o, { i: p.i, j: p.j, k: p.k });
      if (p.edge) o.e = p.edge;
      if (p.depth !== undefined) o.d = +p.depth.toFixed(3);
      if (p.storage && Object.keys(p.storage).length) o.s = p.storage;
      if (p.open) { o.open = 1; o.od = p.openDir; }
      if (this.spawn === p) o.home = 1;
      return o;
    });
  }

  restore(list) {
    const order = ['foundation', 'floor', 'wall', 'doorway', 'window', 'railing', 'gate_frame', 'roof'];
    const rank = (id) => { const r = order.indexOf(id); return r < 0 ? (id === 'door' || id === 'gate' ? 99 : 50) : r; };
    for (const o of [...(list ?? [])].sort((a, b) => rank(a.id) - rank(b.id))) {
      if (!PIECE[o.id]) continue;
      this.place(o.id, { pos: { x: o.x, y: o.y, z: o.z }, rot: o.r, i: o.i, j: o.j, k: o.k, edge: o.e, depth: o.d }, { storage: o.s, open: !!o.open, openDir: o.od, home: !!o.home });
    }
  }
}
