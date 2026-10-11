// Plants, rocks and props for the cove. Trees and palms use the game's Scatter (full model near
// the camera, card further away); plants sway in the wind via a small vertex-shader patch.
import * as THREE from 'three';
import { Scatter, placement } from '../world/scatter.js';
import { cloneModel, modelBox } from '../assets.js';
import { makeRng } from '../util.js';
import { smoothstep } from '../noise.js';

const PALMS = ['tree/palm_tall_a', 'tree/palm_tall_b', 'tree/palm_bent', 'tree/palm_medium'];
const JUNGLE_TREES = ['tree/oak_large', 'tree/ash_medium'];
const BUSHES = ['tree/bush_a', 'tree/bush_c'];
const UNDER = ['plant/fern_a', 'plant/fern_b', 'plant/calathea', 'plant/anthurium', 'plant/pachira'];

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
  transformed += normal * sin(uWind * 7.0 + position.x * 4.0 + position.z * 3.0) * ${flutter.toFixed(3)} * k;
}`);
  };
  material.customProgramCacheKey = () => `wind-${amp}-${from}-${span}-${flutter}`;
}

function windFor(assets, key) {
  const box = modelBox(assets, key);
  const h = box.max.y;
  assets[key].scene.traverse((o) => {
    if (!o.isMesh) return;
    const leafy = /leaves|leaf|frond/i.test(o.material.name) || o.material.alphaTest > 0 || o.material.side === THREE.DoubleSide;
    if (key.startsWith('tree/palm')) addWind(o.material, leafy ? { amp: 0.35, from: h * 0.55, span: h * 0.6, flutter: 0.05 } : { amp: 0.12, from: 1, span: h });
    else if (key.startsWith('tree/')) addWind(o.material, leafy ? { amp: 0.2, from: h * 0.3, span: h * 0.8, flutter: 0.03 } : { amp: 0.05, from: 2, span: h });
    else addWind(o.material, { amp: 0.06, from: 0, span: Math.max(0.3, h), flutter: 0.02 });
  });
}

export class Flora {
  constructor(root, assets, island, { mobile = false } = {}) {
    this.assets = assets;
    this.island = island;
    this.root = root;
    this.colliders = []; // { x, z, r }
    this.scatter = new Scatter(root, assets, mobile ? { nearRadius: 34, nearCap: 35 } : { nearRadius: 55, nearCap: 70 });
    // Far cards: matte (Lambert). Their normals all point up, so a PBR material throws a white
    // sun sheen over every card when you look toward the sun.
    for (const k of [...PALMS, 'tree/palm_young', ...JUNGLE_TREES, ...BUSHES]) {
      assets[`${k}_far`].scene.traverse((o) => {
        if (!o.isMesh || o.material.isMeshLambertMaterial) return;
        const m = o.material;
        o.material = new THREE.MeshLambertMaterial({ name: m.name, map: m.map, color: m.color.clone().multiply(new THREE.Color(0.78, 0.86, 0.72)), alphaTest: 0.5, side: m.side });
      });
    }
    for (const k of [...PALMS, 'tree/palm_young', ...JUNGLE_TREES, ...BUSHES, ...UNDER]) windFor(assets, k);
    for (const k of PALMS.concat('tree/palm_young')) windFor(assets, `${k}_far`);
    for (const k of JUNGLE_TREES.concat(BUSHES)) {
      this.assets[k].scene.traverse((o) => {
        if (o.isMesh && /leaves/.test(o.material.name) && !o.material.userData.tropical) {
          o.material.color.multiply(new THREE.Color(0.58, 0.78, 0.36));
          o.material.roughness = 0.82;
          o.material.userData.tropical = true;
        }
      });
    }
    this.palmOpts = mobile ? { nearRadius: 50, nearCap: 60 } : { nearRadius: 85, nearCap: 110 };
    this.plantOpts = mobile ? { nearOnly: true, nearRadius: 24, nearCap: 35, castShadow: false } : { nearOnly: true, nearRadius: 42, nearCap: 110, castShadow: false };
    this.size = new Map();
    this.placeRocks();
    this.placeWreck();
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

  placeRocks() {
    const I = this.island;
    // Headland rock shelves running out into the lagoon, and a cliff wall on the east point.
    const wx = -150, ex = 150;
    this.put('rock/shelf_a', wx, I.shoreZ(wx) - 2, { rotY: 0.6, dy: -1.6, solid: true });
    this.put('rock/shelf_b', ex - 15, I.shoreZ(ex - 15) + 4, { rotY: 2.4, dy: -1.4, solid: true });
    this.put('rock/cliff', ex + 40, I.shoreZ(ex + 40) - 30, { rotY: -Math.PI / 2 + 0.3, dy: -2.5, s: 1.1, solid: true });
    const rng = makeRng('cove-rocks');
    for (let i = 0; i < 9; i++) {
      const x = rng.range(-130, 130) + (rng() < 0.5 ? -40 : 40);
      const z = I.shoreZ(x) + rng.range(-4, 26);
      this.put(rng() < 0.5 ? 'rock/coast' : 'rock/land', x, z, { rotY: rng() * 6.3, dy: -0.5 - rng() * 0.6, s: rng.range(0.6, 1.1), collide: 2.2 });
    }
    for (let i = 0; i < 7; i++) {
      const x = rng.range(-120, 120), z = I.shoreZ(x) - rng.range(4, 22);
      this.put('rock/pebbles', x, z, { rotY: rng() * 6.3, dy: -0.15 });
    }
  }

  placeWreck() {
    const I = this.island;
    const x = -78, z = I.shoreZ(x) + 17;
    const ship = cloneModel(this.assets, 'landmark/ship');
    ship.position.set(x, I.heightAt(x, z) - 1.4, z);
    ship.rotation.set(0, 0.9, 0);
    ship.rotateX(0.34);
    ship.rotateZ(-0.06);
    ship.traverse((o) => { if (o.isMesh && /sail/i.test(o.name + (o.material?.name ?? ''))) o.visible = false; });
    this.root.add(ship);
    this.footprint(ship, 1.5);
    this.wreck = { x, z };
    // Cargo and debris washed up the beach.
    const bx = -58, bz = I.shoreZ(bx) - 9;
    this.put('props/cannon', bx, bz, { rotY: 2.1, rotZ: 0.25, dy: -0.35, collide: 1.1 });
    this.put('props/crate_b', bx + 5, bz - 3, { rotY: 0.6, rotZ: 0.12, dy: -0.12, collide: 0.8 });
    this.put('props/crate_a', bx + 6.5, bz - 1.5, { rotY: 1.9, dy: -0.05, collide: 0.6 });
    this.put('props/chest', bx - 4, bz - 5, { rotY: 0.3, rotX: 0.08, dy: -0.18, collide: 0.7 });
    this.put('wood/drift_b', bx + 12, bz + 3, { rotY: 0.4, dy: -0.2, collide: 0.8 });
  }

  plant(mobile) {
    const I = this.island;
    const rng = makeRng('cove-flora');
    const step = mobile ? 3.4 : 2.6;
    const crown = new Map();
    for (const k of PALMS) {
      // Which way does this palm lean? (crown centre relative to the trunk foot)
      const c = this.dims(k).getCenter(new THREE.Vector3());
      crown.set(k, Math.atan2(c.z, c.x));
    }
    const leanToSea = (k) => {
      // Rotation about y that turns the crown toward +z (the sea), with some spread.
      const want = Math.PI / 2 + (rng() - 0.5) * 1.3;
      return crown.get(k) - want;
    };
    for (let z = -320; z < 140; z += step) for (let x = -300; x < 300; x += step) {
      const px = x + rng.range(0, step), pz = z + rng.range(0, step);
      const h = I.heightAt(px, pz);
      if (h < 0.4) continue;
      const d = I.inland(px, pz), slope = I.slopeAt(px, pz);
      if (slope > 0.75 || this.blocked(px, pz, 1)) continue;
      const r = rng();
      if (d < 50) {
        // Beach and its top: palms leaning out over the sand, shells near the water.
        const palmBand = smoothstep(8, 22, d) * (1 - smoothstep(42, 56, d));
        if (r < 0.06 * palmBand) {
          const k = rng.pick(PALMS);
          this.scatter.add(k, placement(px, h - 0.1, pz, leanToSea(k), rng.range(0.85, 1.15)), { far: `${k}_far`, ...this.palmOpts });
          this.colliders.push({ x: px, z: pz, r: 0.35 });
        } else if (r < 0.06 * palmBand + 0.03 * smoothstep(25, 45, d)) {
          this.scatter.add('tree/palm_young', placement(px, h - 0.05, pz, rng() * 6.3, rng.range(0.7, 1.2)), { far: 'tree/palm_young_far' });
        } else if (d < 14 && r > 0.985) {
          this.scatter.add('props/shell', placement(px, h - 0.01, pz, rng() * 6.3, rng.range(0.9, 1.4)), { maxDist: 40 });
        } else if (d > 30 && r > 0.93) {
          this.scatter.add(rng.pick(UNDER), placement(px, h - 0.05, pz, rng() * 6.3, rng.range(0.9, 1.5)), this.plantOpts);
        }
        continue;
      }
      // Jungle: palms and broadleaf trees over a dense understory.
      const dens = 0.55 + 0.45 * smoothstep(50, 90, d);
      if (r < 0.075 * dens) {
        const k = rng.pick(PALMS);
        this.scatter.add(k, placement(px, h - 0.1, pz, rng() * 6.3, rng.range(0.9, 1.25)), { far: `${k}_far`, ...this.palmOpts });
        this.colliders.push({ x: px, z: pz, r: 0.35 });
      } else if (r < 0.075 * dens + 0.03 * dens) {
        const k = rng.pick(JUNGLE_TREES);
        this.scatter.add(k, placement(px, h - 0.15, pz, rng() * 6.3, rng.range(0.85, 1.2)), { far: `${k}_far` });
        this.colliders.push({ x: px, z: pz, r: 0.5 });
      } else if (r < 0.105 * dens + 0.06) {
        const k = rng.pick(BUSHES);
        this.scatter.add(k, placement(px, h - 0.1, pz, rng() * 6.3, rng.range(0.9, 1.6)), { far: `${k}_far` });
      } else if (r < 0.105 * dens + 0.06 + 0.16 * dens) {
        const k = rng.pick(UNDER);
        // Lush: big-leaved calathea/anthurium grow knee- to waist-high here.
        const big = k === 'plant/calathea' || k === 'plant/anthurium' ? 2.2 : 1.3;
        this.scatter.add(k, placement(px, h - 0.05, pz, rng() * 6.3, rng.range(1.0, 1.6) * big), this.plantOpts);
      } else if (r > 0.995) {
        this.scatter.add('rock/moss_a', placement(px, h - 0.4, pz, rng() * 6.3, rng.range(0.5, 1)), { far: 'rock/moss_a_far' });
        this.colliders.push({ x: px, z: pz, r: 1.2 });
      }
    }
    // Driftwood along the high-tide line.
    for (let i = 0; i < 10; i++) {
      const x = rng.range(-140, 140), z = I.shoreZ(x) - rng.range(4, 14);
      this.put(rng() < 0.6 ? 'wood/drift_a' : 'wood/drift_b', x, z, { rotY: rng() * 6.3, dy: -0.1, s: rng.range(0.8, 1.1) });
    }
  }

  update(x, z, t) {
    wind.value = t;
    this.scatter.update(x, z, t);
  }
}
