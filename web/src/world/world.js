// Assembles the island: terrain, ocean, sky, landmarks, flora and collision.
import * as THREE from 'three';
import { Terrain, SEA } from './terrain.js';
import { Scatter, placement } from './scatter.js';
import { Colliders, Surfaces, SpatialGrid } from './collide.js';
import { createOcean, createSky } from '../water.js';
import { cloneModel, modelBox } from '../assets.js';
import { makeGroundMaterial } from './ground.js';
import { HARVEST } from '../data/harvest.js';
import { makeRng } from '../util.js';
import { smoothstep } from '../noise.js';

// Bump when the placement of trees/rocks changes, so saved node states are not applied
// to different nodes (see main.js).
const FLORA_VERSION = 'b1';

const PINES = ['tree/pine_large_a', 'tree/pine_large_b', 'tree/pine_medium_a', 'tree/pine_medium_b', 'tree/pine_small'];
const LEAFY = ['tree/oak_medium', 'tree/ash_medium', 'tree/aspen_medium', 'tree/oak_medium', 'tree/oak_large'];
const DEAD = ['tree/dead_oak', 'tree/dead_ash'];
const BUSHES = ['tree/bush_a', 'tree/bush_c'];
const ROCKS = ['rock/moss_a', 'rock/moss_b', 'rock/moss_c', 'rock/boulder_a'];
const STONES = ['rock/stone_a', 'rock/stone_b', 'rock/stone_c'];
const DRIFT = ['wood/drift_a', 'wood/drift_b', 'wood/branches', 'wood/drift_a'];
const NETTLES = ['plant/nettle_a', 'plant/nettle_b'];
const FERNS = ['plant/fern_a', 'plant/fern_b'];
const CRATES = ['props/crate_a', 'props/crate_b'];

export class World {
  constructor(scene, assets, { renderer, mobile = false } = {}) {
    this.scene = scene;
    this.assets = assets;
    this.floraVersion = FLORA_VERSION;
    this.root = new THREE.Group();
    this.root.name = 'world';
    scene.add(this.root);
    this.rng = makeRng('tideborn-island-2');
    this.terrain = new Terrain(11);
    this.colliders = new Colliders();
    this.surfaces = new Surfaces();
    this.nodeGrid = new SpatialGrid();
    this.nodes = [];
    this.boxes = new Map();
    this.scatter = new Scatter(this.root, assets, mobile ? { nearRadius: 30, nearCap: 30 } : { nearRadius: 44, nearCap: 60 });

    this.root.add(this.terrain.buildMesh(makeGroundMaterial(assets, renderer)));
    this.findSpawn();
    this.buildLandmarks();
    this.plantFlora();
    this.scatter.build();
    this.buildSky();
  }

  // Model size in metres at scale 1 (cached).
  size(key) {
    if (!this.boxes.has(key)) this.boxes.set(key, modelBox(this.assets, key).getSize(new THREE.Vector3()));
    return this.boxes.get(key);
  }

  // --- Ground queries ----------------------------------------------------------
  groundAt(x, z, fromY = Infinity) {
    const t = this.terrain.heightAt(x, z);
    const s = this.surfaces.heightAt(x, z, fromY === Infinity ? 1e9 : fromY);
    return Math.max(t, s);
  }

  walkable(x, z, fromY) {
    const t = this.terrain.heightAt(x, z);
    const s = this.surfaces.heightAt(x, z, fromY ?? 1e9);
    if (s > -Infinity && s >= t - 0.01) return true; // on a floor or stairs
    if (t < SEA - 0.7) return false; // too deep
    if (this.terrain.slopeAt(x, z) > 0.8) {
      // Allow stepping onto a slope only if it is not a climb (cliffs block, descents too).
      return false;
    }
    return true;
  }

  // --- Spawn: beach of the southern cove ---------------------------------------------
  findSpawn() {
    const x = 4;
    let z = 220;
    while (z > 60 && this.terrain.heightAt(x, z) < 0.6) z -= 0.5;
    const sz = z - 7;
    this.spawn = { x, z: sz, y: this.terrain.heightAt(x, sz), facing: Math.PI };
    this.beachLine = z;
  }

  // --- Landmarks ---------------------------------------------------------------
  // Solid parts of a big model become small circle colliders: rays from above find where
  // the model stands more than knee-high over the ground.
  addFootprint(obj, step = 1.25, minH = 1.0) {
    obj.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(obj);
    const ray = new THREE.Raycaster();
    const down = new THREE.Vector3(0, -1, 0);
    let n = 0;
    for (let x = box.min.x; x <= box.max.x; x += step) {
      for (let z = box.min.z; z <= box.max.z; z += step) {
        ray.set(new THREE.Vector3(x, box.max.y + 1, z), down);
        const hits = ray.intersectObject(obj, true);
        const g = this.terrain.heightAt(x, z);
        if (hits.some((h) => h.point.y > g + minH) && hits.some((h) => h.point.y < g + 2.2)) {
          this.colliders.addCircle(x, z, step * 0.7);
          n++;
        }
      }
    }
    return n;
  }

  buildLandmarks() {
    const rng = this.rng;
    const T = this.terrain;
    const sp = this.spawn;
    this.landmarks = [];

    // 1) The wreck: a ship run aground in the shallows, listing to one side, with its
    //    cargo and timbers strewn up the beach.
    const wreck = new THREE.Group();
    wreck.name = 'wreck';
    const wx = sp.x - 17, wz = this.beachLine + 7;
    const ship = cloneModel(this.assets, 'landmark/ship');
    ship.position.set(wx, T.heightAt(wx, wz) - 1.6, wz);
    ship.rotation.set(0, 0.42, 0);
    ship.rotateX(0.3);   // heeled over onto its side (the hull runs along local x)
    ship.rotateZ(-0.05); // bow dug into the sand
    // No sails left on a wreck; the rigging hangs on.
    ship.traverse((o) => { if (o.isMesh && /sail/i.test(o.name + (o.material?.name ?? ''))) o.visible = false; });
    wreck.add(ship);
    this.root.add(wreck);
    this.addFootprint(ship, 1.5, 1.2);

    const put = (key, x, z, { rotY = 0, rotX = 0, rotZ = 0, s = 1, dy = 0, collide = 0 } = {}) => {
      const o = cloneModel(this.assets, key);
      o.position.set(x, T.heightAt(x, z) + dy, z);
      o.rotation.set(rotX, rotY, rotZ);
      o.scale.setScalar(s);
      wreck.add(o);
      if (collide) this.colliders.addCircle(x, z, collide);
      return o;
    };
    const bx = sp.x - 4, bz = this.beachLine - 2;
    put('props/crate_b', bx + 3.5, bz - 1.5, { rotY: 0.6, collide: 0.7 });
    put('props/crate_a', bx + 4.6, bz - 2.6, { rotY: 1.9, rotZ: 0.15, collide: 0.6 });
    put('props/planks', bx - 3, bz + 1.5, { rotY: 0.3, rotX: 0.05, dy: -0.05, s: 0.9 });
    put('props/planks', bx + 8, bz + 2.5, { rotY: 2.2, dy: -0.05, s: 0.8 });
    put('props/lantern', bx + 3.2, bz - 0.5, { rotY: 0.4, rotZ: 1.45, dy: 0.1 });
    put('wood/drift_b', bx - 7, bz - 1, { rotY: 0.9, dy: -0.15, collide: 0.8 });
    this.landmarks.push({ id: 'wreck', name: 'Vraget', x: wx, z: wz });

    // 2) Forest rise: one enormous oak on the hill in the middle of the island.
    const gx = T.riseX, gz = T.riseZ;
    const giant = cloneModel(this.assets, 'tree/giant_oak');
    giant.position.set(gx, T.heightAt(gx, gz) - 0.4, gz);
    giant.rotation.y = 0.7;
    this.root.add(giant);
    // Crowns that are not harvest nodes, so the camera stays out of them too.
    const gs = this.size('tree/giant_oak');
    this.canopies = [{ x: gx, z: gz, y: giant.position.y, height: gs.y, r: Math.max(gs.x, gs.z) * 0.42 }];
    this.colliders.addCircle(gx, gz, 2.4);
    this.landmarks.push({ id: 'giant', name: 'Kæmpetræet', x: gx, z: gz });

    // 3) Ridge overlook: the ruins of an old stone fort on the highest northern ground.
    let best = { h: -1 };
    for (let i = 0; i < 2500; i++) {
      const x = rng.range(-120, 120), z = rng.range(-190, -90);
      const h = T.heightAt(x, z);
      if (h > best.h && T.slopeAt(x, z) < 0.3) best = { x, z, h };
    }
    // An old fort, half sunk into the hill and overgrown: only the upper walls stand.
    const fort = cloneModel(this.assets, 'landmark/fort');
    fort.position.set(best.x, best.h - this.size('landmark/fort').y * 0.42, best.z);
    fort.rotation.y = rng() * Math.PI * 2;
    this.root.add(fort);
    this.addFootprint(fort, 1.25, 1.0);
    // The model's pivot is not its middle: use the real footprint for the landmark.
    const fb = new THREE.Box3().setFromObject(fort);
    const fc = fb.getCenter(new THREE.Vector3());
    this.landmarks.push({ id: 'overlook', name: 'Fæstningsruinen', x: fc.x, z: fc.z, r: Math.hypot(fb.max.x - fb.min.x, fb.max.z - fb.min.z) / 2 + 3 });

    // Great mossy boulders on the ridge give it a skyline from the beach.
    let crags = 0;
    for (let i = 0; i < 400 && crags < 9; i++) {
      const x = rng.range(-150, 150), z = rng.range(-170, -70);
      const h = T.heightAt(x, z);
      if (h < 10 || Math.hypot(x - best.x, z - best.z) < 45) continue;
      if (this.colliders.blocked(x, z, 10)) continue;
      const key = rng.pick(['rock/moss_a', 'rock/moss_c', 'rock/boulder_a', 'rock/moss_b']);
      const s = rng.range(3.2, 5.5);
      const c = cloneModel(this.assets, key);
      c.scale.setScalar(s);
      c.position.set(x, h - this.size(key).y * s * 0.25, z);
      c.rotation.y = rng() * Math.PI * 2;
      this.root.add(c);
      const sz = this.size(key);
      this.colliders.addCircle(x, z, Math.max(sz.x, sz.z) * s * 0.4);
      crags++;
    }
  }

  // --- Flora: every tree, rock and plant is a harvestable node ------------------------
  plantFlora() {
    const rng = makeRng('tideborn-flora-b');
    const T = this.terrain;
    const sp = this.spawn;
    const avoid = [
      { x: sp.x, z: sp.z, r: 9 },
      { x: T.riseX, z: T.riseZ, r: 12 },
      ...this.landmarks.map((l) => ({ x: l.x, z: l.z, r: l.r ?? (l.id === 'wreck' ? 14 : 16) })),
    ];
    const clear = (x, z) => avoid.every((a) => Math.hypot(x - a.x, z - a.z) > a.r);
    const step = 3.4;
    for (let z = -240; z < 240; z += step) {
      for (let x = -240; x < 240; x += step) {
        const px = x + rng.range(0, step), pz = z + rng.range(0, step);
        const h = T.heightAt(px, pz);
        if (h < -0.2) continue;
        const slope = T.slopeAt(px, pz);
        const biome = T.biomeAt(px, pz);
        const r = rng();
        if (!clear(px, pz)) continue;

        if (h < 1.7 && h > 0.05 && slope < 0.4) {
          // Beach: driftwood, stones, the odd rock.
          if (r < 0.022) this.addNode('drift', rng.pick(DRIFT), px, pz, rng() * 6.3, rng.range(0.8, 1.15), rng);
          else if (r < 0.05) this.addStone(px, pz, rng);
          else if (r < 0.056) this.addRock(px, pz, rng, 'rock/coast');
          continue;
        }
        if (slope > 0.7) continue;
        if (biome === 'forest') {
          const dens = smoothstep(0.62, 0.9, T.forestMask(px, pz)) * 0.55 + 0.1;
          if (r < dens * 0.5) this.addTree('pine', rng.pick(PINES), px, pz, rng);
          else if (r < dens * 0.72) this.addTree('cone', rng.pick(LEAFY), px, pz, rng);
          else if (r < dens * 0.72 + 0.05) this.addDecor(rng.pick(BUSHES), px, pz, rng.range(0.8, 1.3), rng, true);
          else if (r < dens * 0.72 + 0.09) this.addNode('fern', rng.pick(FERNS), px, pz, rng() * 6.3, rng.range(1.1, 1.6), rng);
          else if (r < dens * 0.72 + 0.1) this.addStone(px, pz, rng);
        } else if (biome === 'meadow') {
          if (r < 0.03) this.addTree('cone', rng.pick(LEAFY), px, pz, rng);
          else if (r < 0.045) this.addTree('pine', rng.pick(PINES), px, pz, rng);
          else if (r < 0.058) this.addRock(px, pz, rng);
          else if (r < 0.08) this.addNode('reed', rng.pick(NETTLES), px, pz, rng() * 6.3, 1, rng);
          else if (r < 0.1) this.addDecor(rng.pick(BUSHES), px, pz, rng.range(0.7, 1.1), rng, true);
          else if (r < 0.112) this.addStone(px, pz, rng);
          else if (r < 0.12) this.addTree('dead', rng.pick(DEAD), px, pz, rng);
        } else if (biome === 'shore') {
          if (r < 0.015) this.addTree('dead', rng.pick(DEAD), px, pz, rng);
          else if (r < 0.04) this.addStone(px, pz, rng);
          else if (r < 0.05) this.addRock(px, pz, rng);
          else if (r < 0.08) this.addNode('reed', rng.pick(NETTLES), px, pz, rng() * 6.3, 1, rng);
          else if (r < 0.1) this.addNode('drift', rng.pick(DRIFT), px, pz, rng() * 6.3, rng.range(0.8, 1.1), rng);
        } else if (biome === 'ridge') {
          if (r < 0.05) this.addRock(px, pz, rng);
          else if (r < 0.08) this.addTree('dead', rng.pick(DEAD), px, pz, rng);
          else if (r < 0.11) this.addTree('pine', rng.pick(['tree/pine_small', 'tree/pine_medium_b']), px, pz, rng);
          else if (r < 0.15) this.addStone(px, pz, rng);
          else if (r < 0.17) this.addDecor('tree/bush_c', px, pz, rng.range(0.6, 1), rng, true);
        }
      }
    }

    // Guaranteed starter materials around the landing site.
    const ring = (fn, n, r0, r1) => {
      let placed = 0;
      for (let i = 0; i < 300 && placed < n; i++) {
        const a = rng.range(-Math.PI * 0.95, -Math.PI * 0.05);
        const r = rng.range(r0, r1);
        const x = sp.x + Math.cos(a) * r, z = sp.z + Math.sin(a) * r;
        if (T.heightAt(x, z) < 0.5 || T.slopeAt(x, z) > 0.5 || this.colliders.blocked(x, z, 1.5)) continue;
        if (fn(x, z).hitsMax) placed++;
      }
    };
    ring((x, z) => this.addTree('dead', rng.pick(DEAD), x, z, rng), 3, 9, 20);
    ring((x, z) => this.addNode('drift', rng.pick(DRIFT), x, z, rng() * 6.3, rng.range(0.8, 1), rng), 4, 5, 16);
    ring((x, z) => this.addStone(x, z, rng), 6, 5, 18);
    ring((x, z) => this.addNode('reed', rng.pick(NETTLES), x, z, rng() * 6.3, 1, rng), 5, 6, 18);

    // Washed-up supply crates along the beach (refilled by the tide each morning).
    this.tideSpots = [];
    for (let i = 0; i < 400 && this.tideSpots.length < 7; i++) {
      const x = sp.x + rng.range(-70, 70);
      let z = 230;
      while (z > 60 && T.heightAt(x, z) < 0.35) z -= 0.5;
      z -= rng.range(1, 3);
      if (z < 60 || this.colliders.blocked(x, z, 2) || T.slopeAt(x, z) > 0.4) continue;
      if (this.tideSpots.some((s) => Math.hypot(s.x - x, s.z - z) < 12)) continue;
      this.tideSpots.push({ x, z });
      this.addNode('supplies', rng.pick(CRATES), x, z, rng() * 6.3, 1, rng);
    }
  }

  // Trees: full model near the player, a card further away (see Scatter).
  addTree(type, key, x, z, rng) {
    const scale = rng.range(0.8, 1.15);
    const node = this.addNode(type, key, x, z, rng() * 6.3, scale, rng, { far: `${key}_far` });
    if (key === 'tree/pine_large_a' || key === 'tree/pine_large_b' || key === 'tree/oak_large') { node.hitsMax += 1; node.hits = node.hitsMax; node.per += 1; }
    return node;
  }

  addRock(x, z, rng, key = rng.pick(ROCKS)) {
    const scale = key === 'rock/coast' ? rng.range(0.6, 1) : rng.range(0.7, 1.35);
    const node = this.addNode('boulder', key, x, z, rng() * 6.3, scale, rng, { far: `${key}_far` });
    if (!node.handle) return node;
    const sz = this.size(key);
    node.radius = Math.max(sz.x, sz.z) * scale * 0.38;
    this.colliders.remove(node.collider);
    node.collider = this.colliders.addCircle(x, z, node.radius, node);
    return node;
  }

  // Loose stones, scaled to fist-to-head size whatever the scan's own scale.
  addStone(x, z, rng) {
    const key = rng.pick(STONES);
    const sz = this.size(key);
    return this.addNode('pebble', key, x, z, rng() * 6.3, rng.range(0.32, 0.5) / Math.max(sz.x, sz.z), rng);
  }

  // Pure decoration (bushes): no node, no collision.
  addDecor(key, x, z, scale, rng, lod = false) {
    if (this.colliders.blocked(x, z, 0.8)) return;
    const y = this.terrain.heightAt(x, z);
    this.scatter.add(key, placement(x, y - 0.1, z, rng() * 6.3, scale), lod ? { far: `${key}_far` } : { maxDist: 70 });
  }

  addNode(type, key, x, z, rot, scale, rng, opts = {}) {
    const def = HARVEST[type];
    const y = this.terrain.heightAt(x, z);
    if (!def.walkable && this.colliders.blocked(x, z, def.radius + 0.4)) return { hitsMax: 0, per: 0 };
    // Plants are scaled to a target height in metres (scans come in odd units).
    if (def.height) scale *= rng.range(...def.height) / this.size(key).y;
    const sink = type === 'boulder' ? 0.25 * scale : type === 'drift' ? 0.08 : 0.05;
    const m = placement(x, y - sink, z, rot, scale);
    const small = type === 'pebble' || type === 'reed' || type === 'fern' || type === 'supplies' || type === 'drift';
    const handle = this.scatter.add(key, m, {
      far: opts.far,
      castShadow: type !== 'pebble',
      maxDist: small ? (type === 'supplies' ? 120 : 60) : 0,
    });
    let stump = null;
    if (def.stump) {
      const sk = rng() < 0.5 ? 'wood/stump_a' : 'wood/stump_b';
      // Stump about as wide as the trunk: ~0.9 m for big trees.
      const sw = this.size(sk);
      const trunk = (key.includes('large') ? 1.0 : key.includes('small') ? 0.55 : 0.8) * scale;
      stump = this.scatter.add(sk, placement(x, y - 0.05, z, rot, trunk / Math.max(sw.x, sw.z)), { pool: true }, true);
    }
    const node = {
      id: this.nodes.length,
      type, def, key, x, y, z, rot, scale,
      handle, stump,
      hitsMax: def.hits, per: def.per, hits: def.hits,
      state: 'ready', regrowAt: 0,
      radius: def.radius * (def.fall ? Math.min(1.3, Math.max(0.7, scale)) : 1),
    };
    node.collider = def.walkable ? null : this.colliders.addCircle(x, z, node.radius, node);
    this.nodeGrid.insert(node, x - 0.1, z - 0.1, x + 0.1, z + 0.1);
    this.nodes.push(node);
    return node;
  }

  nodesNear(x, z, r) {
    return this.nodeGrid.query(x - r, z - r, x + r, z + r);
  }

  // --- Sky, ocean ------------------------------------------------------------------
  buildSky() {
    this.sunDir = new THREE.Vector3(-0.45, 0.8, 0.35).normalize();
    const df = this.terrain.distanceField();
    this.ocean = createOcean({ y: SEA, distTexture: df.tex, bounds: { minX: df.minX, minZ: df.minX, size: df.size }, maxDist: df.maxD, sunDir: this.sunDir });
    this.root.add(this.ocean);
    this.sky = createSky();
    this.scene.add(this.sky);
  }

  update(dt, t, camera, light = 1, sunDir = null, focus = camera.position) {
    this.ocean.update(t, light, sunDir);
    this.sky.position.copy(camera.position);
    this.scatter.update(focus.x, focus.z, t);
  }
}
