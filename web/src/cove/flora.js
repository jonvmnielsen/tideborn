// Plants, rocks and props for the cove, all from the faceted low-poly forge (D-013). Palms and
// canopy trees swap to cheaper versions in the distance; small plants and grass are only drawn
// near the player. Leaves sway in the wind via a small vertex-shader patch.
import * as THREE from 'three';
import { Scatter, placement } from '../world/scatter.js';
import { cloneModel, modelBox } from '../assets.js';
import { makeRng } from '../util.js';
import { smoothstep } from '../noise.js';
import { prepareModel } from './facets.js';
import { VOLCANO } from './island.js';

const PALMS = ['tree/palm_tall_a', 'tree/palm_tall_b', 'tree/palm_bent', 'tree/palm_medium'];
const CANOPY = ['tree/canopy_a', 'tree/canopy_b', 'tree/canopy_tall'];
const TREES = [...PALMS, 'tree/palm_young', ...CANOPY];
const UNDER = ['plant/banana_a', 'plant/banana_b', 'plant/ear_a', 'plant/ear_b', 'plant/monstera', 'plant/fern_a', 'plant/fern_b', 'plant/heliconia', 'plant/heliconia_orange'];
const BUSHES = ['bush/a', 'bush/b', 'bush/hibiscus', 'bush/hibiscus_pink'];
const GRASS = ['grass/a', 'grass/tall', 'grass/beach'];
const ROCKS = ['rock/a', 'rock/b', 'rock/c', 'rock/small', 'rock/sand', 'rock/cliff_a', 'rock/cliff_b', 'rock/basalt_a', 'rock/basalt_b'];
const PROPS = ['props/rowboat', 'props/barrel', 'props/crate', 'props/machete', 'wood/drift_a', 'wood/drift_b'];

export const wind = { value: 0 };

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
    this.colliders = []; // { x, z, r }
    this.scatter = new Scatter(root, assets, mobile ? { nearRadius: 40, nearCap: 50 } : { nearRadius: 70, nearCap: 120 });
    for (const k of [...TREES, ...TREES.map((t) => `${t}_far`), ...UNDER, ...BUSHES, ...GRASS, ...ROCKS, ...PROPS]) prepareModel(assets[k].scene);
    for (const k of [...TREES, ...TREES.map((t) => `${t}_far`), ...UNDER, ...BUSHES, ...GRASS]) windFor(assets, k);
    // Far versions sit outside the sun's shadow box anyway: no shadow pass for them.
    this.treeOpts = mobile ? { nearRadius: 45, nearCap: 55, farShadow: false } : { nearRadius: 55, nearCap: 70, farShadow: false };
    this.plantOpts = { maxDist: mobile ? 34 : 60, castShadow: !mobile };
    this.grassOpts = { maxDist: mobile ? 22 : 38, castShadow: false };
    this.size = new Map();
    this.placeRocks(mobile);
    this.placeCamp();
    this.plant(mobile);
    this.scatter.build();
  }

  dims(key) {
    if (!this.size.has(key)) this.size.set(key, modelBox(this.assets, key));
    return this.size.get(key);
  }

  ground(x, z) { return this.island.heightAt(x, z); }

  blocked(x, z, r) { return this.colliders.some((c) => Math.hypot(c.x - x, c.z - z) < c.r + r); }

  // Big static models: rays from above mark where they stand more than knee-high (blocked).
  footprint(obj, step = 2) {
    obj.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(obj);
    const ray = new THREE.Raycaster();
    for (let x = box.min.x; x <= box.max.x; x += step) for (let z = box.min.z; z <= box.max.z; z += step) {
      ray.set(new THREE.Vector3(x, box.max.y + 1, z), new THREE.Vector3(0, -1, 0));
      const hit = ray.intersectObject(obj, true)[0];
      if (hit && hit.point.y > this.ground(x, z) + 0.9) this.colliders.push({ x, z, r: step * 0.7 });
    }
  }

  put(key, x, z, { rotY = 0, rotX = 0, rotZ = 0, s = 1, dy = 0, collide = 0, solid = false } = {}) {
    const o = cloneModel(this.assets, key);
    o.position.set(x, this.ground(x, z) + dy, z);
    o.rotation.set(rotX, rotY, rotZ);
    o.scale.setScalar(s);
    this.root.add(o);
    if (collide) this.colliders.push({ x, z, r: collide });
    if (solid) this.footprint(o);
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
      this.scatter.add('rock/small', placement(x, I.heightAt(x, z) - 0.08, z, rng() * 6.3, rng.range(0.7, 1.4)), { maxDist: 70 });
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
    this.colliders.push({ x: x + 1.2, z: z + 1.0, r: 1.2 }, { x: x - 1.2, z: z - 1.0, r: 1.2 });
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
    const step = mobile ? 3.4 : 2.5;
    const crown = new Map();
    for (const k of PALMS) {
      const c = this.dims(k).getCenter(new THREE.Vector3());
      crown.set(k, Math.atan2(c.z, c.x));
    }
    // Rotation about y that turns a palm's crown toward +z (the sea), with some spread.
    const leanToSea = (k) => crown.get(k) - (Math.PI / 2 + (rng() - 0.5) * 1.3);
    const tree = (k, x, y, z, rot, s, r = 0.35) => {
      this.scatter.add(k, placement(x, y, z, rot, s), { far: `${k}_far`, ...this.treeOpts });
      this.colliders.push({ x, z, r });
    };
    const V = VOLCANO;
    for (let z = -330; z < 140; z += step) for (let x = -300; x < 300; x += step) {
      const px = x + rng.range(0, step), pz = z + rng.range(0, step);
      const h = I.heightAt(px, pz);
      if (h < 0.35) continue;
      const d = I.inland(px, pz), slope = I.slopeAt(px, pz);
      if (slope > 0.72 || this.blocked(px, pz, 0.8)) continue;
      // Vegetation thins out up the volcano.
      const bare = smoothstep(V.base * 0.62, V.base * 0.4, Math.hypot(px - V.x, pz - V.z));
      if (rng() < bare) continue;
      const r = rng();
      if (d < 46) {
        // Beach and its top: palms leaning out over the sand, beach grass, flowering shrubs.
        const palmBand = smoothstep(7, 20, d) * (1 - smoothstep(40, 52, d));
        if (r < 0.065 * palmBand) {
          const k = rng.pick(PALMS);
          tree(k, px, h - 0.1, pz, leanToSea(k), rng.range(0.85, 1.15));
        } else if (r < 0.065 * palmBand + 0.03 * smoothstep(22, 40, d)) {
          tree('tree/palm_young', px, h - 0.05, pz, rng() * 6.3, rng.range(0.8, 1.25), 0.25);
        } else if (r < 0.2 && d > 6) {
          this.scatter.add(d < 24 ? 'grass/beach' : rng.pick(GRASS), placement(px, h - 0.02, pz, rng() * 6.3, rng.range(0.8, 1.4)), this.grassOpts);
        } else if (d > 26 && r > 0.9) {
          this.scatter.add(rng.pick(r > 0.96 ? BUSHES : UNDER), placement(px, h - 0.05, pz, rng() * 6.3, rng.range(0.9, 1.4)), this.plantOpts);
        }
        continue;
      }
      // Jungle: palms and canopy trees over a dense understory.
      const dens = (0.55 + 0.45 * smoothstep(46, 90, d)) * (1 - bare);
      if (r < 0.055 * dens) {
        const k = rng.pick(PALMS);
        tree(k, px, h - 0.1, pz, rng() * 6.3, rng.range(0.9, 1.25));
      } else if (r < 0.055 * dens + 0.035 * dens) {
        tree(rng.pick(CANOPY), px, h - 0.2, pz, rng() * 6.3, rng.range(0.85, 1.25), 0.6);
      } else if (r < 0.09 * dens + 0.06) {
        this.scatter.add(rng.pick(BUSHES), placement(px, h - 0.1, pz, rng() * 6.3, rng.range(0.9, 1.7)), this.plantOpts);
      } else if (r < 0.09 * dens + 0.06 + 0.2 * dens) {
        const k = rng.pick(UNDER);
        this.scatter.add(k, placement(px, h - 0.05, pz, rng() * 6.3, rng.range(1.0, 1.6) * (k.includes('banana') ? 1.2 : 1.4)), this.plantOpts);
      } else if (r < 0.09 * dens + 0.06 + 0.2 * dens + 0.15) {
        this.scatter.add(rng.pick(GRASS.slice(0, 2)), placement(px, h - 0.02, pz, rng() * 6.3, rng.range(0.9, 1.5)), this.grassOpts);
      } else if (r > 0.993) {
        this.scatter.add(rng.pick(['rock/a', 'rock/c']), placement(px, h - 0.3, pz, rng() * 6.3, rng.range(0.6, 1.2)), {});
        this.colliders.push({ x: px, z: pz, r: 1.1 });
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
  }
}
