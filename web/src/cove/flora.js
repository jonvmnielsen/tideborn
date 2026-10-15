// Plants, rocks and props for the cove, all from the faceted low-poly forge (D-013). The jungle
// is layered: emergent giants and canopy trees with lianas, palms, bamboo and tree ferns,
// a dense understory of big leaves and flowering shrubs, and ground cover (grass, ferns,
// bromeliads, flowers) that is generated around the player. Trees swap to cheaper versions in
// the distance. Leaves sway in the wind via a small vertex-shader patch.
import * as THREE from 'three';
import { Scatter, placement } from '../world/scatter.js';
import { cloneModel, modelBox } from '../assets.js';
import { makeRng } from '../util.js';
import { smoothstep } from '../noise.js';
import { prepareModel } from './facets.js';
import { VOLCANO } from './island.js';
import { GroundCover } from './cover.js';

const PALMS = ['tree/palm_tall_a', 'tree/palm_tall_b', 'tree/palm_bent', 'tree/palm_medium'];
const CANOPY = ['tree/canopy_a', 'tree/canopy_b', 'tree/canopy_tall', 'tree/canopy_vines'];
const TREES = [...PALMS, 'tree/palm_young', ...CANOPY, 'tree/canopy_giant'];
const UNDER = ['plant/banana_a', 'plant/banana_b', 'plant/ear_a', 'plant/ear_b', 'plant/monstera', 'plant/fern_a', 'plant/heliconia', 'plant/heliconia_orange'];
const MID = ['plant/bamboo', 'plant/bamboo_small', 'plant/treefern_a', 'plant/treefern_b'];
const COVER = ['cover/bromeliad_red', 'cover/bromeliad_pink', 'cover/flowers_yellow', 'cover/flowers_purple', 'cover/flowers_white', 'plant/fern_b'];
const BUSHES = ['bush/a', 'bush/b', 'bush/hibiscus', 'bush/hibiscus_pink'];
const GRASS = ['grass/a', 'grass/tall', 'grass/beach'];
const ROCKS = ['rock/a', 'rock/b', 'rock/c', 'rock/small', 'rock/sand', 'rock/cliff_a', 'rock/cliff_b', 'rock/basalt_a', 'rock/basalt_b'];
const PROPS = ['props/rowboat', 'props/barrel', 'props/crate', 'props/machete', 'wood/drift_a', 'wood/drift_b', 'wood/log_mossy'];

export const wind = { value: 0 };

// What kind of gatherable thing a model is (see gather.js); null = scenery.
export function kindOf(k) {
  if (k.startsWith('tree/palm_young')) return 'palm_young';
  if (k.startsWith('tree/palm')) return 'palm';
  if (k.startsWith('tree/canopy')) return 'canopy';
  if (k.includes('bamboo')) return 'bamboo';
  if (k.includes('banana')) return 'banana';
  if (k.includes('treefern')) return 'treefern';
  if (k.startsWith('bush/')) return 'bush';
  if (k.startsWith('plant/')) return 'leafy';
  if (k === 'rock/small') return 'stone';
  if (k.startsWith('wood/drift')) return 'drift';
  if (k === 'props/crate') return 'crate';
  if (k === 'props/barrel') return 'barrel';
  if (k === 'item/coconut') return 'coconut';
  if (k === 'pile') return 'pile';
  if (k === 'build/lean_to') return 'shelter';
  return null;
}

// Sway grows with height above `from` (m, model space); leaves also flutter.
function addWind(material, { amp = 0.25, from = 1, span = 10, flutter = 0 }) {
  if (material.userData.wind) return;
  material.userData.wind = true;
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uWind = wind;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nuniform float uWind;')
      .replace('#include <begin_vertex>', `#include <begin_vertex>
{
  vec3 iw = vec3(0.0);
  #ifdef USE_INSTANCING
  iw = instanceMatrix[3].xyz;
  #endif
  float ph = uWind * 1.3 + dot(iw.xz, vec2(0.11, 0.07));
  float k = clamp((transformed.y - ${from.toFixed(2)}) / ${span.toFixed(2)}, 0.0, 1.0);
  k *= k;
  float gust = 0.65 + 0.35 * sin(uWind * 0.31 + iw.x * 0.01);
  transformed.x += (sin(ph) * ${amp.toFixed(3)} + sin(ph * 2.7) * ${(amp * 0.25).toFixed(3)}) * k * gust;
  transformed.z += cos(ph * 0.83) * ${(amp * 0.6).toFixed(3)} * k * gust;
  transformed.y += sin(uWind * 5.0 + position.x * 3.0 + position.z * 2.0) * ${flutter.toFixed(3)} * k;
}`);
  };
  material.customProgramCacheKey = () => `wind-${amp}-${from}-${span}-${flutter}`;
}

function windFor(assets, key) {
  const h = modelBox(assets, key).max.y;
  assets[key].scene.traverse((o) => {
    if (!o.isMesh) return;
    const name = o.material.name;
    const leafy = name === 'lowpoly_leaf' || name === 'lowpoly_foliage';
    if (key.startsWith('tree/palm')) addWind(o.material, leafy ? { amp: 0.3, from: h * 0.55, span: h * 0.6, flutter: 0.06 } : { amp: 0.1, from: 1, span: h });
    else if (key.startsWith('tree/')) addWind(o.material, leafy ? { amp: 0.14, from: h * 0.4, span: h * 0.7 } : { amp: 0.04, from: 2, span: h });
    else if (leafy) addWind(o.material, { amp: 0.07, from: 0, span: Math.max(0.3, h), flutter: 0.02 });
  });
}

export class Flora {
  constructor(root, assets, island, { mobile = false } = {}) {
    this.assets = assets;
    this.island = island;
    this.root = root;
    this.grid = new Map(); // collision circles { x, z, r } in 4 m cells
    this.nodes = new Map(); // gatherable things, see register()
    this.byId = new Map();
    this.nodeCount = 0;
    this.scatter = new Scatter(root, assets, mobile ? { nearRadius: 40, nearCap: 50 } : { nearRadius: 70, nearCap: 120 });
    const plants = [...TREES, ...TREES.map((t) => `${t}_far`), ...UNDER, ...MID, ...BUSHES, ...GRASS, ...COVER];
    for (const k of [...plants, ...ROCKS, ...PROPS]) prepareModel(assets[k].scene);
    for (const k of plants) windFor(assets, k);
    // Far versions sit outside the sun's shadow box anyway: no shadow pass for them.
    this.treeOpts = mobile ? { nearRadius: 45, nearCap: 55, farShadow: false, farThin: { dist: 120, keep: 0.5 } } : { nearRadius: 55, nearCap: 70, farShadow: false };
    // Only trees cast shadows: the understory sits in their shade anyway (and halves the cost).
    this.plantOpts = { maxDist: mobile ? 28 : 45, castShadow: false };
    this.grassOpts = { maxDist: mobile ? 22 : 38, castShadow: false };
    this.size = new Map();
    this.placeRocks(mobile);
    this.placeCamp();
    this.plant(mobile);
    this.scatter.build();
    this.cover = this.makeCover(mobile);
  }

  addCollider(x, z, r) {
    const k = `${Math.floor(x / 4)},${Math.floor(z / 4)}`;
    let a = this.grid.get(k);
    if (!a) this.grid.set(k, (a = []));
    const c = { x, z, r };
    a.push(c);
    return c;
  }

  restoreCollider(c) {
    const k = `${Math.floor(c.x / 4)},${Math.floor(c.z / 4)}`;
    let a = this.grid.get(k);
    if (!a) this.grid.set(k, (a = []));
    if (!a.includes(c)) a.push(c);
  }

  removeCollider(c) {
    const a = this.grid.get(`${Math.floor(c.x / 4)},${Math.floor(c.z / 4)}`);
    const i = a ? a.indexOf(c) : -1;
    if (i >= 0) a.splice(i, 1);
  }

  // Things the player can cut or pick up (gather.js), in 4 m cells.
  register(key, x, y, z, ref, col = null) {
    const kind = kindOf(key);
    if (!kind) return;
    // Ids follow placement order (seeded, so stable between visits) — saves refer to them.
    const n = { id: ref.id ?? this.nodeCount++, kind, key, x, y, z, ...ref, col, hits: 0 };
    this.byId.set(n.id, n);
    const k = `${Math.floor(x / 4)},${Math.floor(z / 4)}`;
    let a = this.nodes.get(k);
    if (!a) this.nodes.set(k, (a = []));
    a.push(n);
    return n;
  }

  nodesNear(x, z) {
    const out = [], i0 = Math.floor(x / 4), j0 = Math.floor(z / 4);
    for (let j = j0 - 1; j <= j0 + 1; j++) for (let i = i0 - 1; i <= i0 + 1; i++) {
      const a = this.nodes.get(`${i},${j}`);
      if (a) for (const n of a) if (!n.gone) out.push(n);
    }
    return out;
  }

  // Grass, ferns, bromeliads and flowers around the player (see cover.js).
  makeCover(mobile) {
    const I = this.island, V = VOLCANO;
    const zone = (x, z) => {
      const d = I.inland(x, z);
      const bare = smoothstep(V.base * 0.6, V.base * 0.4, Math.hypot(x - V.x, z - V.z));
      return { d, jungle: smoothstep(42, 60, d) * (1 - bare), open: smoothstep(20, 34, d) * (1 - smoothstep(46, 62, d)) * (1 - bare) };
    };
    const k = mobile ? 0.6 : 1;
    const kinds = [
      { key: 'grass/a', max: 0.4 * k, scale: [0.8, 1.5], density: (x, z) => { const q = zone(x, z); return (0.4 * q.open + 0.12 * q.jungle) * k; } },
      { key: 'grass/tall', max: 0.14 * k, scale: [0.8, 1.4], density: (x, z) => { const q = zone(x, z); return (0.14 * q.open + 0.04 * q.jungle) * k; } },
      { key: 'grass/beach', max: 0.12 * k, scale: [0.7, 1.3], density: (x, z) => { const d = I.inland(x, z); return 0.12 * smoothstep(5, 12, d) * (1 - smoothstep(26, 36, d)) * k; } },
      { key: 'plant/fern_b', max: 0.13 * k, scale: [0.9, 1.7], density: (x, z) => 0.13 * zone(x, z).jungle * k, shadow: false },
      { key: 'plant/fern_a', max: 0.05 * k, scale: [0.8, 1.3], density: (x, z) => 0.05 * zone(x, z).jungle * k, shadow: false },
      { key: 'plant/ear_b', max: 0.03 * k, scale: [0.7, 1.2], density: (x, z) => 0.03 * zone(x, z).jungle * k },
      { key: 'cover/bromeliad_red', max: 0.025 * k, scale: [0.8, 1.4], density: (x, z) => 0.025 * zone(x, z).jungle * k },
      { key: 'cover/bromeliad_pink', max: 0.02 * k, scale: [0.8, 1.4], density: (x, z) => 0.02 * zone(x, z).jungle * k },
      { key: 'cover/flowers_yellow', max: 0.035 * k, scale: [0.8, 1.3], density: (x, z) => { const q = zone(x, z); return (0.035 * q.open + 0.01 * q.jungle) * k; } },
      { key: 'cover/flowers_purple', max: 0.03 * k, scale: [0.8, 1.3], density: (x, z) => { const q = zone(x, z); return (0.02 * q.open + 0.03 * q.jungle) * k; } },
      { key: 'cover/flowers_white', max: 0.03 * k, scale: [0.8, 1.3], density: (x, z) => { const q = zone(x, z); return (0.03 * q.open + 0.015 * q.jungle) * k; } },
    ];
    return new GroundCover(this.root, this.assets, I, kinds, { radius: mobile ? 24 : 38, blocked: (x, z, r) => this.blocked(x, z, r) });
  }

  dims(key) {
    if (!this.size.has(key)) this.size.set(key, modelBox(this.assets, key));
    return this.size.get(key);
  }

  ground(x, z) { return this.island.heightAt(x, z); }

  blocked(x, z, r) {
    const i0 = Math.floor(x / 4), j0 = Math.floor(z / 4);
    for (let j = j0 - 1; j <= j0 + 1; j++) for (let i = i0 - 1; i <= i0 + 1; i++) {
      const a = this.grid.get(`${i},${j}`);
      if (a) for (const c of a) if (Math.hypot(c.x - x, c.z - z) < c.r + r) return true;
    }
    return false;
  }

  // Big static models: rays from above mark where they stand more than knee-high (blocked).
  footprint(obj, step = 2) {
    obj.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(obj);
    const ray = new THREE.Raycaster();
    for (let x = box.min.x; x <= box.max.x; x += step) for (let z = box.min.z; z <= box.max.z; z += step) {
      ray.set(new THREE.Vector3(x, box.max.y + 1, z), new THREE.Vector3(0, -1, 0));
      const hit = ray.intersectObject(obj, true)[0];
      if (hit && hit.point.y > this.ground(x, z) + 0.9) this.addCollider(x, z, step * 0.7);
    }
  }

  put(key, x, z, { rotY = 0, rotX = 0, rotZ = 0, s = 1, dy = 0, collide = 0, solid = false } = {}) {
    const o = cloneModel(this.assets, key);
    o.position.set(x, this.ground(x, z) + dy, z);
    o.rotation.set(rotX, rotY, rotZ);
    o.scale.setScalar(s);
    this.root.add(o);
    const col = collide ? this.addCollider(x, z, Math.min(collide, 2.5)) : null;
    if (solid) this.footprint(o);
    this.register(key, x, o.position.y, z, { obj: o }, col);
    return o;
  }

  placeRocks(mobile) {
    const I = this.island;
    const rng = makeRng('cove-rocks');
    // Headlands: piled cliff blocks standing in the surf at both ends of the beach.
    for (const side of [-1, 1]) {
      for (let i = 0; i < 9; i++) {
        const x = side * rng.range(118, 190), z = I.shoreZ(x) + rng.range(-28, 8);
        this.put(rng() < 0.5 ? 'rock/cliff_a' : 'rock/cliff_b', x, z, { rotY: rng() * 6.3, dy: -rng.range(1.5, 3.5), s: rng.range(0.9, 1.7), solid: true });
      }
    }
    // Boulders on the beach and in the shallows.
    for (let i = 0; i < 16; i++) {
      const x = rng.range(-130, 130), z = I.shoreZ(x) + rng.range(-6, 22);
      const k = rng.pick(['rock/a', 'rock/b', 'rock/sand', 'rock/c']);
      this.put(k, x, z, { rotY: rng() * 6.3, dy: -0.35 - rng() * 0.4, s: rng.range(0.6, 1.3), collide: 1.4 });
    }
    for (let i = 0; i < 24; i++) {
      const x = rng.range(-125, 125), z = I.shoreZ(x) - rng.range(2, 30);
      const y = I.heightAt(x, z) - 0.08;
      this.register('rock/small', x, y, z, { handle: this.scatter.add('rock/small', placement(x, y, z, rng() * 6.3, rng.range(0.7, 1.4)), { maxDist: 70 }) });
    }
    // Basalt fields on the volcano's flanks.
    const V = VOLCANO;
    for (let i = 0; i < (mobile ? 60 : 110); i++) {
      const a = rng() * Math.PI * 2, d = rng.range(V.crater + 8, V.base * 0.7);
      const x = V.x + Math.cos(a) * d, z = V.z + Math.sin(a) * d;
      if (I.lavaAt(x, z).lava > 0.1) continue;
      this.scatter.add(rng() < 0.6 ? 'rock/basalt_a' : 'rock/basalt_b', placement(x, I.heightAt(x, z) - 0.4, z, rng() * 6.3, rng.range(0.6, 1.8)), {});
    }
  }

  // The castaway's landing: a rowboat pulled up the sand, cargo and driftwood around it.
  placeCamp() {
    const I = this.island;
    const x = -46, z = I.shoreZ(x) - 3;
    this.put('props/rowboat', x, z, { rotY: 1.05, rotZ: 0.12, dy: 0.05, s: 1.15, collide: 1.6 });
    this.addCollider(x + 1.2, z + 1.0, 1.2);
    this.addCollider(x - 1.2, z - 1.0, 1.2);
    const bx = -36, bz = I.shoreZ(bx) - 8;
    this.put('props/barrel', bx, bz, { rotY: 0.4, collide: 0.45 });
    this.put('props/barrel', bx + 1.0, bz + 0.5, { rotY: 1.4, rotX: Math.PI / 2, dy: 0.32, collide: 0.5 });
    this.put('props/crate', bx - 1.6, bz - 0.6, { rotY: 0.5, dy: -0.04, collide: 0.6 });
    this.put('props/crate', bx - 1.4, bz - 0.4, { rotY: 0.9, dy: 0.76, s: 0.8 });
    this.put('props/barrel', bx + 9, bz + 7, { rotY: 0.2, rotZ: Math.PI / 2, dy: 0.3, collide: 0.5 });
    this.put('props/crate', bx + 15, bz + 10, { rotY: 2.2, rotZ: 0.15, dy: -0.2, collide: 0.6 });
    this.camp = { x, z };
  }

  plant(mobile) {
    const I = this.island;
    const rng = makeRng('cove-flora');
    const step = mobile ? 3.2 : 2.4;
    const crown = new Map();
    for (const k of PALMS) {
      const c = this.dims(k).getCenter(new THREE.Vector3());
      crown.set(k, Math.atan2(c.z, c.x));
    }
    // Rotation about y that turns a palm's crown toward +z (the sea), with some spread.
    const leanToSea = (k) => crown.get(k) - (Math.PI / 2 + (rng() - 0.5) * 1.3);
    const tree = (k, x, y, z, rot, s, r = 0.35) => {
      const handle = this.scatter.add(k, placement(x, y, z, rot, s), { far: `${k}_far`, ...this.treeOpts });
      this.register(k, x, y, z, { handle, scale: s }, this.addCollider(x, z, r));
    };
    const put = (k, x, y, z, s, opts = this.plantOpts, r = 0) => {
      const handle = this.scatter.add(k, placement(x, y, z, rng() * 6.3, s), opts);
      this.register(k, x, y, z, { handle, scale: s }, r ? this.addCollider(x, z, r) : null);
      return handle;
    };
    const { fbm } = I.noise;
    const V = VOLCANO;
    // Emergent giants first (they need room), then everything else.
    for (let i = 0; i < (mobile ? 14 : 22); i++) {
      for (let tries = 0; tries < 30; tries++) {
        const x = rng.range(-220, 220), z = rng.range(-300, 0);
        const h = I.heightAt(x, z);
        if (h < 3 || I.inland(x, z) < 70 || I.slopeAt(x, z) > 0.5 || Math.hypot(x - V.x, z - V.z) < V.base * 0.62 || this.blocked(x, z, 6)) continue;
        tree('tree/canopy_giant', x, h - 0.4, z, rng() * 6.3, rng.range(0.85, 1.2), 1.4);
        break;
      }
    }
    const MID_MAX = mobile ? 55 : 75;
    const midOpts = { maxDist: MID_MAX, castShadow: false };
    for (let z = -330; z < 140; z += step) for (let x = -300; x < 300; x += step) {
      const px = x + rng.range(0, step), pz = z + rng.range(0, step);
      const h = I.heightAt(px, pz);
      if (h < 0.35) continue;
      const d = I.inland(px, pz), slope = I.slopeAt(px, pz);
      if (slope > 0.75 || this.blocked(px, pz, 0.7)) continue;
      // Vegetation thins out up the volcano.
      const bare = smoothstep(V.base * 0.6, V.base * 0.38, Math.hypot(px - V.x, pz - V.z));
      if (rng() < bare) continue;
      const r = rng();
      if (d < 44) {
        // Beach and its top: palms leaning out over the sand, flowering shrubs and big leaves
        // where the sand gives way to the jungle.
        const palmBand = smoothstep(7, 18, d) * (1 - smoothstep(40, 50, d));
        const edge = smoothstep(24, 40, d);
        if (r < 0.08 * palmBand) {
          const k = rng.pick(PALMS);
          tree(k, px, h - 0.1, pz, leanToSea(k), rng.range(0.85, 1.2));
        } else if (r < 0.08 * palmBand + 0.04 * smoothstep(16, 36, d)) {
          put('tree/palm_young', px, h - 0.05, pz, rng.range(0.8, 1.3), { maxDist: MID_MAX }, 0.25);
        } else if (r < 0.08 * palmBand + 0.04 + 0.12 * edge) {
          put(rng.pick(r > 0.2 ? UNDER : BUSHES), px, h - 0.05, pz, rng.range(0.9, 1.4));
        }
        continue;
      }
      // Jungle, layered. Bamboo grows in groves (noise), the rest is mixed.
      const dens = (0.6 + 0.4 * smoothstep(44, 80, d)) * (1 - bare);
      const grove = smoothstep(0.15, 0.4, fbm(px * 0.012 + 40, pz * 0.012, 2));
      let t = 0;
      if (r < (t += 0.045 * dens)) {
        tree(rng.pick(CANOPY), px, h - 0.2, pz, rng() * 6.3, rng.range(0.85, 1.3), 0.6);
      } else if (r < (t += 0.04 * dens)) {
        tree(rng.pick(PALMS), px, h - 0.1, pz, rng() * 6.3, rng.range(0.9, 1.25));
      } else if (r < (t += 0.06 * dens * grove)) {
        put(rng() < 0.6 ? 'plant/bamboo' : 'plant/bamboo_small', px, h - 0.05, pz, rng.range(0.9, 1.3), midOpts, 0.8);
      } else if (r < (t += 0.035 * dens)) {
        put(rng.pick(['plant/treefern_a', 'plant/treefern_b']), px, h - 0.05, pz, rng.range(0.9, 1.4), midOpts, 0.25);
      } else if (r < (t += 0.025 * dens)) {
        put('tree/palm_young', px, h - 0.05, pz, rng.range(0.8, 1.3), midOpts, 0.25);
      } else if (r < (t += 0.05 * dens)) {
        put(rng.pick(BUSHES), px, h - 0.1, pz, rng.range(0.9, 1.8));
      } else if (r < (t += 0.3 * dens)) {
        const k = rng.pick(UNDER);
        put(k, px, h - 0.05, pz, rng.range(1.0, 1.6) * (k.includes('banana') ? 1.25 : 1.45));
      } else if (r < (t += 0.006)) {
        this.scatter.add('wood/log_mossy', placement(px, h - 0.15, pz, rng() * 6.3, rng.range(0.8, 1.3)), { maxDist: MID_MAX });
        this.addCollider(px, pz, 1.0);
      } else if (r > 0.994) {
        this.scatter.add(rng.pick(['rock/a', 'rock/c']), placement(px, h - 0.3, pz, rng() * 6.3, rng.range(0.6, 1.2)), {});
        this.addCollider(px, pz, 1.1);
      }
    }
    // Driftwood along the high-tide line.
    for (let i = 0; i < 12; i++) {
      const x = rng.range(-140, 140), z = I.shoreZ(x) - rng.range(3, 12);
      this.put(rng() < 0.6 ? 'wood/drift_a' : 'wood/drift_b', x, z, { rotY: rng() * 6.3, dy: -0.15, s: rng.range(0.8, 1.2) });
    }
  }

  update(x, z, t) {
    wind.value = t;
    this.scatter.update(x, z, t);
    this.cover.update(x, z);
  }
}
