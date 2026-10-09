// Assembles the island: terrain, ocean, sky, landmarks, flora and collision.
import * as THREE from 'three';
import { Terrain, SEA } from './terrain.js';
import { Scatter, placement } from './scatter.js';
import { Colliders, Surfaces, SpatialGrid } from './collide.js';
import { createOcean, createSky } from '../water.js';
import { cloneModel } from '../assets.js';
import { HARVEST } from '../data/harvest.js';
import { makeRng } from '../util.js';
import { smoothstep } from '../noise.js';

const PINE_TINT = '#4fae63';
const GIANT_TINT = '#3f9a58';

export class World {
  constructor(scene, assets) {
    this.scene = scene;
    this.assets = assets;
    this.root = new THREE.Group();
    this.root.name = 'world';
    scene.add(this.root);
    this.rng = makeRng('tideborn-island-2');
    this.terrain = new Terrain(11);
    this.colliders = new Colliders();
    this.surfaces = new Surfaces();
    this.nodeGrid = new SpatialGrid();
    this.nodes = [];
    this.clouds = [];
    this.scatter = new Scatter(this.root, assets);

    this.root.add(this.terrain.buildMesh());
    this.findSpawn();
    this.buildLandmarks();
    this.plantFlora();
    this.scatter.build();
    this.buildSky();
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
  buildLandmarks() {
    const rng = this.rng;
    const T = this.terrain;
    const sp = this.spawn;
    this.landmarks = [];

    // 1) The wreck: broken planking, cargo and a torn sail on the beach.
    const wreck = new THREE.Group();
    wreck.name = 'wreck';
    const wx = sp.x - 9, wz = this.beachLine + 3;
    const put = (key, dx, dz, { rotY = 0, rotX = 0, rotZ = 0, s = 1, dy = 0, collide = 0 } = {}) => {
      const o = cloneModel(this.assets, key);
      const x = wx + dx, z = wz + dz;
      o.position.set(x, T.heightAt(x, z) + dy, z);
      o.rotation.set(rotX, rotY, rotZ);
      o.scale.setScalar(s);
      wreck.add(o);
      if (collide) this.colliders.addCircle(x, z, collide);
      return o;
    };
    // Hull planks jutting from the sand like ribs.
    for (let k = 0; k < 6; k++) {
      put('build/floor', -6 + k * 2.4, -1 + Math.sin(k) * 0.8, { rotY: 0.35, rotX: -1.15 + k * 0.05, rotZ: 0.2 * Math.sin(k * 1.7), dy: -0.6, s: 1 });
    }
    this.colliders.addBox(wx + 0.4, wz - 0.3, 7.5, 1.2, 0.35, null);
    put('props/sail', 3.5, 2.5, { rotY: -0.6, rotZ: 0.18, s: 1.6, dy: -0.3, collide: 0.6 });
    put('props/barrel_large', 6.5, -2.2, { rotY: 0.4, rotZ: 1.45, dy: 0.5, collide: 1.2 });
    put('props/barrel_stack', -8.5, -3.5, { rotY: 2.1, collide: 1.2 });
    put('props/crates_stacked', 8.5, 1.2, { rotY: 0.7, collide: 1.5 });
    put('props/lumber', -3.5, -4.5, { rotY: 1.2, s: 4 });
    this.root.add(wreck);
    this.landmarks.push({ id: 'wreck', name: 'Vraget', x: wx, z: wz });

    // 2) Forest rise: one enormous tree on the hill in the middle of the island.
    const gx = T.riseX, gz = T.riseZ;
    const giant = cloneModel(this.assets, 'nature/pine_large');
    giant.traverse((o) => {
      if (o.isMesh) {
        o.material = o.material.clone();
        o.material.color = new THREE.Color(GIANT_TINT);
      }
    });
    giant.scale.setScalar(4.6);
    giant.position.set(gx, T.heightAt(gx, gz) - 0.5, gz);
    giant.rotation.y = 0.7;
    this.root.add(giant);
    this.colliders.addCircle(gx, gz, 3.6);
    this.landmarks.push({ id: 'giant', name: 'Kæmpetræet', x: gx, z: gz });

    // 3) Ridge overlook: a ruined watchtower on the highest northern ground.
    let best = { h: -1 };
    for (let i = 0; i < 2500; i++) {
      const x = rng.range(-120, 120), z = rng.range(-190, -90);
      const h = T.heightAt(x, z);
      if (h > best.h && T.slopeAt(x, z) < 0.35) best = { x, z, h };
    }
    const tower = cloneModel(this.assets, 'landmark/tower');
    tower.scale.setScalar(5.5);
    tower.position.set(best.x, best.h - 0.3, best.z);
    tower.rotation.y = rng() * Math.PI * 2;
    this.root.add(tower);
    this.colliders.addCircle(best.x, best.z, 4.2);
    const ruin = cloneModel(this.assets, 'landmark/rubble_half');
    ruin.position.set(best.x + 7, T.heightAt(best.x + 7, best.z + 3), best.z + 3);
    ruin.rotation.y = 1.1;
    this.root.add(ruin);
    this.colliders.addCircle(best.x + 7, best.z + 3, 2.2);
    this.landmarks.push({ id: 'overlook', name: 'Udsigtstårnet', x: best.x, z: best.z });

    // Rock crags on the ridge give it a skyline from the beach.
    let crags = 0;
    for (let i = 0; i < 400 && crags < 5; i++) {
      const x = rng.range(-150, 150), z = rng.range(-170, -70);
      const h = T.heightAt(x, z);
      if (h < 10 || Math.hypot(x - best.x, z - best.z) < 40) continue;
      if (this.colliders.blocked(x, z, 14)) continue;
      const c = cloneModel(this.assets, rng() < 0.5 ? 'nature/crag_a' : 'nature/crag_b');
      c.scale.setScalar(rng.range(7, 10));
      c.position.set(x, h - 2, z);
      c.rotation.y = rng() * Math.PI * 2;
      this.root.add(c);
      this.colliders.addCircle(x, z, 7.5);
      crags++;
    }
  }

  // --- Flora: every tree, rock and reed is a harvestable node -----------------------
  plantFlora() {
    const rng = makeRng('tideborn-flora-2');
    const T = this.terrain;
    const sp = this.spawn;
    const avoid = [
      { x: sp.x, z: sp.z, r: 9 },
      { x: T.riseX, z: T.riseZ, r: 9 },
      ...this.landmarks.map((l) => ({ x: l.x, z: l.z, r: 10 })),
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

        if (h < 1.6 && h > 0.05 && slope < 0.4) {
          if (r < 0.3) this.addNode('reed', rng.pick(['nature/reed_a', 'nature/reed_b', 'nature/reed_c']), px, pz, rng() * 6.3, rng.range(4.5, 6.5), rng);
          continue;
        }
        if (slope > 0.7) continue;
        if (biome === 'forest') {
          const dens = smoothstep(0.62, 0.9, T.forestMask(px, pz)) * 0.75 + 0.12;
          if (r < dens * 0.72) this.addPine(px, pz, rng);
          else if (r < dens * 0.95) this.addNode('cone', rng.pick(['nature/tree_cone_a', 'nature/tree_cone_b']), px, pz, rng() * 6.3, rng.range(3.8, 5.4), rng);
          else if (r < dens * 0.95 + 0.02) this.addNode('pebble', rng.pick(['nature/pebble_a', 'nature/pebble_b']), px, pz, rng() * 6.3, rng.range(3.5, 5), rng);
        } else if (biome === 'meadow') {
          if (r < 0.045) this.addNode('cone', rng.pick(['nature/tree_cone_a', 'nature/tree_cone_b']), px, pz, rng() * 6.3, rng.range(3.8, 5.6), rng);
          else if (r < 0.065) this.addPine(px, pz, rng);
          else if (r < 0.08) this.addBoulder(px, pz, rng);
          else if (r < 0.11) this.addNode('pebble', rng.pick(['nature/pebble_a', 'nature/pebble_b']), px, pz, rng() * 6.3, rng.range(3.5, 5), rng);
          else if (r < 0.12) this.addNode('dead', rng.pick(['nature/dead_medium', 'nature/dead_small']), px, pz, rng() * 6.3, rng.range(0.9, 1.2), rng);
        } else if (biome === 'shore') {
          if (r < 0.02) this.addNode('dead', rng.pick(['nature/dead_large', 'nature/dead_medium', 'nature/dead_small']), px, pz, rng() * 6.3, rng.range(0.9, 1.3), rng);
          else if (r < 0.06) this.addNode('pebble', rng.pick(['nature/pebble_a', 'nature/pebble_b']), px, pz, rng() * 6.3, rng.range(3.5, 5), rng);
          else if (r < 0.07) this.addBoulder(px, pz, rng);
        } else if (biome === 'ridge') {
          if (r < 0.06) this.addBoulder(px, pz, rng);
          else if (r < 0.1) this.addNode('dead', rng.pick(['nature/dead_large', 'nature/dead_medium']), px, pz, rng() * 6.3, rng.range(1, 1.4), rng);
          else if (r < 0.13) this.addNode('cone', 'nature/tree_cone_a', px, pz, rng() * 6.3, rng.range(3.4, 4.6), rng);
          else if (r < 0.17) this.addNode('pebble', rng.pick(['nature/pebble_a', 'nature/pebble_b']), px, pz, rng() * 6.3, rng.range(3.5, 5), rng);
        }
      }
    }

    // Guaranteed starter materials around the landing site.
    const ring = (type, keys, n, r0, r1, scale) => {
      let placed = 0;
      for (let i = 0; i < 300 && placed < n; i++) {
        const a = rng.range(-Math.PI * 0.95, -Math.PI * 0.05);
        const r = rng.range(r0, r1);
        const x = sp.x + Math.cos(a) * r, z = sp.z + Math.sin(a) * r;
        if (T.heightAt(x, z) < 0.5 || T.slopeAt(x, z) > 0.5 || this.colliders.blocked(x, z, 1.5)) continue;
        this.addNode(type, rng.pick(keys), x, z, rng() * 6.3, rng.range(...scale), rng);
        placed++;
      }
    };
    ring('dead', ['nature/dead_medium', 'nature/dead_small'], 4, 8, 20, [0.9, 1.2]);
    ring('pebble', ['nature/pebble_a', 'nature/pebble_b'], 6, 6, 18, [3.5, 5]);

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
      this.addNode('supplies', rng.pick(['props/supply_carrots', 'props/supply_potatoes', 'props/supply_tomatoes']), x, z, rng() * 6.3, 0.8, rng);
    }
  }

  addPine(x, z, rng) {
    const size = rng();
    const key = size < 0.45 ? 'nature/pine_large' : size < 0.8 ? 'nature/pine_medium' : 'nature/pine_small';
    const node = this.addNode('pine', key, x, z, rng() * 6.3, rng.range(0.85, 1.25), rng, { tint: PINE_TINT });
    if (key === 'nature/pine_large') { node.hitsMax += 1; node.per += 1; }
    return node;
  }

  addBoulder(x, z, rng) {
    const big = rng() < 0.35;
    const key = big ? rng.pick(['nature/boulders_a', 'nature/boulders_b']) : rng.pick(['nature/rock_c', 'nature/rock_d', 'nature/rock_e']);
    const scale = big ? rng.range(1.6, 2.4) : rng.range(4.5, 6.5);
    const node = this.addNode('boulder', key, x, z, rng() * 6.3, scale, rng);
    if (!node.handle) return node;
    node.radius = big ? 1.5 * scale * 0.55 : 0.32 * scale * 0.5 + 0.4;
    this.colliders.remove(node.collider);
    node.collider = this.colliders.addCircle(x, z, node.radius, node);
    return node;
  }

  addNode(type, key, x, z, rot, scale, rng, opts = {}) {
    const def = HARVEST[type];
    const y = this.terrain.heightAt(x, z);
    if (!def.walkable && this.colliders.blocked(x, z, def.radius + 0.4)) return { hitsMax: 0, per: 0 };
    const m = placement(x, y - (type === 'boulder' ? 0.15 : 0.05), z, rot, scale);
    const handle = this.scatter.add(key, m, { tint: opts.tint, castShadow: type !== 'reed' && type !== 'pebble' });
    let stump = null;
    if (def.stump) {
      const sk = key.includes('cone_b') ? 'nature/stump_b' : 'nature/stump_a';
      const ss = key.startsWith('nature/pine') ? scale * 4.8 : scale;
      stump = this.scatter.add(sk, placement(x, y - 0.05, z, rot, ss), {}, true);
    }
    const node = {
      id: this.nodes.length,
      type, def, key, x, y, z, rot, scale,
      handle, stump,
      hitsMax: def.hits, per: def.per, hits: def.hits,
      state: 'ready', regrowAt: 0,
      radius: def.radius * (type === 'pine' || type === 'cone' ? Math.min(1.3, scale / (key.startsWith('nature/pine') ? 1 : 4.5)) : 1),
      tint: opts.tint,
    };
    node.collider = def.walkable ? null : this.colliders.addCircle(x, z, node.radius, node);
    this.nodeGrid.insert(node, x - 0.1, z - 0.1, x + 0.1, z + 0.1);
    this.nodes.push(node);
    return node;
  }

  nodesNear(x, z, r) {
    return this.nodeGrid.query(x - r, z - r, x + r, z + r);
  }

  // --- Sky, ocean, clouds -------------------------------------------------------
  buildSky() {
    this.sunDir = new THREE.Vector3(-0.45, 0.8, 0.35).normalize();
    const df = this.terrain.distanceField();
    this.ocean = createOcean({ y: SEA, distTexture: df.tex, bounds: { minX: df.minX, minZ: df.minX, size: df.size }, maxDist: df.maxD, sunDir: this.sunDir });
    this.root.add(this.ocean);
    this.sky = createSky();
    this.scene.add(this.sky);
    const rng = makeRng('clouds');
    for (let i = 0; i < 14; i++) {
      const cl = cloneModel(this.assets, rng() < 0.5 ? 'nature/cloud_big' : 'nature/cloud_small', { castShadow: false, receiveShadow: false });
      cl.scale.setScalar(rng.range(7, 12));
      cl.position.set(rng.range(-300, 300), rng.range(70, 95), rng.range(-300, 300));
      cl.rotation.y = rng() * Math.PI * 2;
      cl.userData.speed = rng.range(1, 2.5);
      this.root.add(cl);
      this.clouds.push(cl);
    }
  }

  update(dt, t, camera, light = 1, sunDir = null) {
    this.ocean.update(t, light, sunDir);
    this.sky.position.copy(camera.position);
    for (const c of this.clouds) {
      c.position.x += c.userData.speed * dt;
      if (c.position.x > 320) c.position.x = -320;
    }
  }
}
