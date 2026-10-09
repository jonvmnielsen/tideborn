// Harvesting: find the node in front of the player, hit it, fell it, regrow it later.
import * as THREE from 'three';
import { cloneModel } from '../assets.js';
import { easeOutBack } from '../util.js';

export class Gather {
  constructor(world, chips) {
    this.world = world;
    this.chips = chips;
    this.anims = [];
  }

  // Best ready node within reach; prefers what the player is facing.
  findTarget(px, pz, facing) {
    const fx = Math.sin(facing), fz = Math.cos(facing);
    let best = null, bestScore = Infinity;
    for (const n of this.world.nodesNear(px, pz, 4)) {
      if (n.state !== 'ready') continue;
      const dx = n.x - px, dz = n.z - pz, d = Math.hypot(dx, dz);
      if (d > n.radius + 1.5) continue;
      const front = d > 0.01 ? (dx * fx + dz * fz) / d : 1;
      if (front < -0.2 && d > n.radius + 0.6) continue;
      const score = d - n.radius - front * 0.8;
      if (score < bestScore) { bestScore = score; best = n; }
    }
    return best;
  }

  // Apply one hit. Returns { item, amount, spent }.
  hit(node, now, fromX, fromZ) {
    if (node.state !== 'ready') return null;
    node.hits--;
    const impact = new THREE.Vector3(node.x, node.y + (node.def.fall ? 1.1 : 0.4), node.z);
    this.chips.burst(impact, node.def.fx, node.def.fall ? 7 : 6);
    if (!node.def.fall && node.hits > 0) this.shake(node);
    else if (node.def.fall && node.hits > 0) this.shake(node);
    const spent = node.hits <= 0;
    if (spent) this.spend(node, now, fromX, fromZ);
    return { item: node.def.item, amount: node.per, spent };
  }

  spend(node, now, fromX, fromZ) {
    const w = this.world;
    node.state = 'spent';
    node.regrowAt = node.def.tide ? Infinity : now + node.def.regrow;
    w.scatter.set(node.handle, null);
    if (node.collider) { w.colliders.remove(node.collider); node.collider = null; }
    if (node.stump) {
      w.scatter.set(node.stump, w.scatter.original(node.stump));
      node.collider = w.colliders.addCircle(node.x, node.z, 0.35, node);
    }
    // Temporary clone to animate the fall / crumble.
    const obj = cloneModel(w.assets, node.key);
    if (node.tint) obj.traverse((o) => { if (o.isMesh) { o.material = o.material.clone(); o.material.color.set(node.tint); } });
    obj.position.set(node.x, node.y, node.z);
    obj.rotation.y = node.rot;
    obj.scale.setScalar(node.scale);
    w.root.add(obj);
    const dx = node.x - fromX, dz = node.z - fromZ, l = Math.hypot(dx, dz) || 1;
    this.anims.push({
      obj, node,
      type: node.def.fall ? 'fall' : 'shrink',
      t: 0,
      dur: node.def.fall ? 1.0 : 0.35,
      axis: new THREE.Vector3(dz / l, 0, -dx / l),
    });
    if (node.def.fall) this.chips.burst(new THREE.Vector3(node.x, node.y + 0.3, node.z), '#c2a77a', 10, 1.2);
  }

  shake(node) {
    this.anims.push({ node, type: 'shake', t: 0, dur: 0.35 });
  }

  regrow(node) {
    const w = this.world;
    node.state = 'growing';
    node.hits = node.hitsMax;
    if (node.stump) w.scatter.set(node.stump, null);
    if (node.collider) w.colliders.remove(node.collider);
    node.collider = node.def.walkable ? null : w.colliders.addCircle(node.x, node.z, node.radius, node);
    this.anims.push({ node, type: 'grow', t: 0, dur: 0.9 });
  }

  // Supplies washed up by the tide come back every morning.
  tideIn() {
    for (const n of this.world.nodes) if (n.def.tide && n.state === 'spent') this.regrow(n);
  }

  update(dt, now, player) {
    const w = this.world;
    for (let i = this.anims.length - 1; i >= 0; i--) {
      const a = this.anims[i];
      a.t += dt;
      const p = Math.min(1, a.t / a.dur);
      const n = a.node;
      if (a.type === 'shake') {
        const s = 1 - p;
        const m = w.scatter.original(n.handle).clone().multiply(new THREE.Matrix4().makeRotationZ(Math.sin(p * 30) * 0.05 * s));
        w.scatter.set(n.handle, m);
        if (p >= 1) w.scatter.set(n.handle, w.scatter.original(n.handle));
      } else if (a.type === 'fall') {
        const ang = p * p * (Math.PI / 2 - 0.1);
        a.obj.quaternion.setFromAxisAngle(a.axis, ang).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), n.rot));
        if (p >= 1) { a.type = 'shrink'; a.t = 0; a.dur = 0.5; a.base = a.obj.scale.x; continue; }
      } else if (a.type === 'shrink') {
        a.base ??= a.obj.scale.x;
        a.obj.scale.setScalar(a.base * Math.max(0.001, 1 - p));
        if (p >= 1) w.root.remove(a.obj);
      } else if (a.type === 'grow') {
        const k = Math.max(0.001, easeOutBack(p));
        const m = w.scatter.original(n.handle).clone().multiply(new THREE.Matrix4().makeScale(k, k, k));
        w.scatter.set(n.handle, m);
        if (p >= 1) { n.state = 'ready'; w.scatter.set(n.handle, w.scatter.original(n.handle)); }
      }
      if (p >= 1) this.anims.splice(i, 1);
    }
    // Regrowth, a few nodes per frame.
    if (!this.cursor) this.cursor = 0;
    for (let k = 0; k < 40 && w.nodes.length; k++) {
      const n = w.nodes[this.cursor = (this.cursor + 1) % w.nodes.length];
      if (n.state === 'spent' && now >= n.regrowAt) {
        if (Math.hypot(player.pos.x - n.x, player.pos.z - n.z) > n.radius + 3) this.regrow(n);
      }
    }
  }

  serialize(now) {
    const out = [];
    for (const n of this.world.nodes) {
      if (n.state === 'ready' && n.hits === n.hitsMax) continue;
      out.push([n.id, n.state === 'ready' ? n.hits : 0, n.state === 'ready' || n.regrowAt === Infinity ? -1 : Math.max(0, Math.round(n.regrowAt - now))]);
    }
    return out;
  }

  restore(list, now) {
    for (const [id, hits, wait] of list ?? []) {
      const n = this.world.nodes[id];
      if (!n) continue;
      if (hits > 0) { n.hits = Math.min(n.hitsMax, hits); continue; }
      n.hits = 0;
      n.state = 'spent';
      n.regrowAt = wait < 0 ? Infinity : now + wait;
      this.world.scatter.set(n.handle, null);
      if (n.collider) this.world.colliders.remove(n.collider);
      n.collider = null;
      if (n.stump) {
        this.world.scatter.set(n.stump, this.world.scatter.original(n.stump));
        n.collider = this.world.colliders.addCircle(n.x, n.z, 0.35, n);
      }
    }
  }
}
