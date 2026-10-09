// Gatherable trees and rocks: chop or mine them, they drop wood/stone and grow back later.
import * as THREE from 'three';
import { cloneStatic } from './assets.js';
import { WS } from './world.js';
import { makeRng, easeOutBack } from './util.js';

export const KINDS = {
  tree: {
    models: ['tree_a', 'tree_b'],
    stump: { tree_a: 'stump_a', tree_b: 'stump_b' },
    hits: 3,
    item: 'wood',
    radius: 0.55,
    label: 'Hug træ',
    icon: 'ui/tree.webp',
    respawn: 90,
    chip: '#9a6332',
    impactY: 1.1,
  },
  rock: {
    models: ['rock_c', 'rock_e', 'rock_d'],
    hits: 4,
    item: 'stone',
    radius: 1.0,
    label: 'Hak sten',
    icon: 'ui/rock.webp',
    respawn: 120,
    chip: '#9aa2a6',
    impactY: 0.5,
  },
};

const REACH = 1.5; // meters beyond the node's own radius

export class ResourceNodes {
  constructor(scene, assets, world) {
    this.scene = scene;
    this.assets = assets;
    this.world = world;
    this.nodes = [];
    const rng = makeRng('tideborn-nodes-1');
    const sp = world.spawn;

    const tryPlace = (kind, x, z, minGap) => {
      const k = KINDS[kind];
      if (!world.isOnGrass(x, z)) return false;
      if (!world.isFree(x, z, k.radius + minGap)) return false;
      if (Math.hypot(x - sp.x, z - sp.z) < 3.5) return false;
      this.create(kind, x, z, rng);
      return true;
    };

    // A few right next to the beach, so the first thing you see is something to do.
    const ring = (kind, n, r0, r1) => {
      let placed = 0;
      for (let i = 0; i < 200 && placed < n; i++) {
        const a = -Math.PI / 2 + (rng() - 0.5) * Math.PI * 1.3; // mostly inland (north)
        const r = rng.range(r0, r1);
        if (tryPlace(kind, sp.x + Math.cos(a) * r, sp.z + Math.sin(a) * r, 1.4)) placed++;
      }
    };
    ring('tree', 3, 5, 10);
    ring('rock', 2, 5, 11);

    const scatter = (kind, n) => {
      let placed = 0;
      for (let i = 0; i < 600 && placed < n; i++) {
        const p = world.randomLandPoint(rng);
        if (p && tryPlace(kind, p.x, p.z, 2.0)) placed++;
      }
    };
    scatter('tree', 22);
    scatter('rock', 12);
  }

  create(kind, x, z, rng) {
    const k = KINDS[kind];
    const model = rng.pick(k.models);
    const holder = new THREE.Group();
    const y = this.world.heightAt(x, z);
    holder.position.set(x, y, z);
    const obj = cloneStatic(this.assets, model);
    const scale = WS * (kind === 'rock' ? rng.range(1.5, 1.8) : rng.range(0.82, 1.0));
    obj.scale.setScalar(scale);
    obj.rotation.y = rng() * Math.PI * 2;
    holder.add(obj);
    let stump = null;
    if (k.stump) {
      stump = cloneStatic(this.assets, k.stump[model]);
      stump.scale.setScalar(scale);
      stump.rotation.y = obj.rotation.y;
      stump.visible = false;
      holder.add(stump);
    }
    this.scene.add(holder);
    const node = {
      id: this.nodes.length,
      kind, k, x, z, y, holder, obj, stump,
      hitsLeft: k.hits,
      state: 'ready',
      respawnAt: 0,
      anim: null, // { type, t, dur, dir }
      shake: 0,
      yaw: obj.rotation.y,
      collider: this.world.addCollider(x, z, k.radius, `${kind}`),
    };
    this.nodes.push(node);
    return node;
  }

  // Nearest ready node within reach, preferring ones in front of the player.
  findTarget(px, pz, facing) {
    let best = null, bestScore = Infinity;
    const fx = Math.sin(facing), fz = Math.cos(facing);
    for (const n of this.nodes) {
      if (n.state !== 'ready') continue;
      const dx = n.x - px, dz = n.z - pz;
      const d = Math.hypot(dx, dz);
      if (d > n.k.radius + REACH) continue;
      const front = d > 0.01 ? (dx * fx + dz * fz) / d : 1;
      const score = d - front * 0.6;
      if (score < bestScore) { bestScore = score; best = n; }
    }
    return best;
  }

  // Returns what the hit yielded.
  hit(node, now, fromX, fromZ, chips) {
    if (node.state !== 'ready') return null;
    node.hitsLeft--;
    node.shake = 1;
    const impact = new THREE.Vector3(node.x, node.y + node.k.impactY, node.z);
    chips.burst(impact, node.k.chip, node.kind === 'tree' ? 7 : 9);
    if (node.hitsLeft <= 0) {
      node.state = 'falling';
      const dx = node.x - fromX, dz = node.z - fromZ, l = Math.hypot(dx, dz) || 1;
      node.anim = { type: node.kind === 'tree' ? 'fall' : 'crumble', t: 0, dur: node.kind === 'tree' ? 0.9 : 0.45, dir: { x: dx / l, z: dz / l } };
      node.respawnAt = now + node.k.respawn;
      this.world.removeCollider(node.collider);
      if (node.stump) {
        node.stump.visible = true;
        // The stump keeps blocking, just smaller.
        node.collider = this.world.addCollider(node.x, node.z, 0.35, 'stump');
      } else {
        node.collider = null;
      }
      if (node.kind === 'rock') chips.burst(impact, node.k.chip, 14, 1.3);
    }
    return { item: node.k.item, amount: 1, depleted: node.hitsLeft <= 0 };
  }

  update(dt, now, player) {
    for (const n of this.nodes) {
      if (n.shake > 0) {
        n.shake = Math.max(0, n.shake - dt * 3.2);
        const s = n.shake;
        if (!n.anim) n.obj.rotation.set(Math.cos(s * 33) * 0.04 * s, n.yaw, Math.sin(s * 40) * 0.06 * s);
      }
      if (n.anim) {
        const a = n.anim;
        a.t += dt;
        const p = Math.min(1, a.t / a.dur);
        if (a.type === 'fall') {
          // Tip over away from the player, accelerating like a real fall.
          const ang = p * p * (Math.PI / 2 - 0.12);
          const axis = new THREE.Vector3(a.dir.z, 0, -a.dir.x);
          n.obj.quaternion.setFromAxisAngle(axis, ang).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), n.yaw));
          if (p >= 1) { a.type = 'fade'; a.t = 0; a.dur = 0.5; }
        } else if (a.type === 'fade' || a.type === 'crumble') {
          const base = n.obj.userData.baseScale ?? (n.obj.userData.baseScale = n.obj.scale.x);
          n.obj.scale.setScalar(base * Math.max(0.001, 1 - p));
          if (p >= 1) {
            n.obj.visible = false;
            n.obj.scale.setScalar(base);
            n.obj.rotation.set(0, n.yaw, 0);
            n.anim = null;
            n.state = 'gone';
          }
        } else if (a.type === 'grow') {
          const base = n.obj.userData.baseScale ?? n.obj.scale.x;
          n.obj.scale.setScalar(base * Math.max(0.001, easeOutBack(p)));
          if (p >= 1) { n.anim = null; n.state = 'ready'; n.obj.scale.setScalar(base); }
        }
      }
      if (n.state === 'gone' && now >= n.respawnAt) {
        const far = Math.hypot(player.pos.x - n.x, player.pos.z - n.z) > n.k.radius + 2.5;
        if (far) this.regrow(n);
      }
    }
  }

  regrow(n) {
    if (n.collider) this.world.removeCollider(n.collider);
    n.collider = this.world.addCollider(n.x, n.z, n.k.radius, n.kind);
    n.hitsLeft = n.k.hits;
    n.obj.userData.baseScale = n.obj.userData.baseScale ?? n.obj.scale.x;
    n.obj.scale.setScalar(0.001);
    n.obj.visible = true;
    if (n.stump) n.stump.visible = false;
    n.state = 'growing';
    n.anim = { type: 'grow', t: 0, dur: 0.8 };
  }

  serialize(now) {
    return this.nodes
      .filter((n) => n.state !== 'ready' || n.hitsLeft < n.k.hits)
      .map((n) => ({ id: n.id, h: n.hitsLeft, w: n.state === 'ready' ? 0 : Math.max(0, Math.round(n.respawnAt - now)) }));
  }

  restore(list, now) {
    for (const s of list ?? []) {
      const n = this.nodes[s.id];
      if (!n) continue;
      if (s.w > 0 || s.h <= 0) {
        n.hitsLeft = 0;
        n.state = 'gone';
        n.obj.visible = false;
        n.respawnAt = now + (s.w ?? n.k.respawn);
        this.world.removeCollider(n.collider);
        n.collider = n.stump ? this.world.addCollider(n.x, n.z, 0.35, 'stump') : null;
        if (n.stump) n.stump.visible = true;
      } else {
        n.hitsLeft = Math.max(1, Math.min(n.k.hits, s.h));
      }
    }
  }
}
