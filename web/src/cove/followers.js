// People of the island and the follower layer (D-023, D-025, Docs/FOLLOWERS_RULES.md v3). Two
// ways to get people on your side, and how you got them is for good:
//   Allieret (earn) — rescue Ida, who lies hurt on the far beach (bring her food), or help Mads fix
//                  his boat (bring rope and wood). Allies follow you and fight for you, do every job
//                  well and each has a skill of their own (Ida heals you, Mads makes building
//                  cheaper). They eat, and their loyalty follows whether they're fed.
//   Træl (force)  — raiders camp on the west headland and attack anyone who comes near. A blade kills
//                  them at 0. A club knocks them out when a blow leaves them under 10 % — a narrow
//                  margin. Bind the unconscious one with a rope, wake them, lead them on the rope to
//                  a captive post in your camp; a minute at the post and they are your træl. Trælle
//                  never leave and never eat — but they only do simple work at a post (gather,
//                  guard), slower and weaker than an ally, and never follow you.
// Roles: Følg (allies), Saml (gathers near the post into the nearest chest), Vagt, Hvil.
// The dead leave something to search; new raiders turn up at the camp after a while.
import * as THREE from 'three';
import { makeCastaway } from './npc.js';

const MEAL = 300;            // seconds between an ally's meals
const OUT = 60;              // seconds unconscious
const BREAK = 60;            // seconds at the captive post
const FOOD = ['meat_cooked', 'banana', 'coconut', 'meat'];
const KNOCKOUT = 0.1;        // a club blow that leaves less than this share of health knocks out
const LOOKS = {
  ida: { outfit: 'char/peasant_f', body: 'char/body_female', parts: ['char/hair_long', 'char/eyebrows_female'], hair: '#3a2418' },
  mads: { outfit: 'char/ranger', parts: ['char/hair_beard', 'char/eyebrows'], hair: '#2a1e16' },
  jens: { outfit: 'char/peasant', parts: ['char/hair_beard', 'char/hair_parted', 'char/eyebrows'], hair: '#5a3a22' },
  raider_m1: { outfit: 'char/ranger', parts: ['char/hair_buzzed', 'char/eyebrows'], hair: '#1a1410' },
  raider_m2: { outfit: 'char/peasant', parts: ['char/hair_beard', 'char/hair_buzzed', 'char/eyebrows'], hair: '#4a2a14' },
  raider_f1: { outfit: 'char/ranger_f', body: 'char/body_female', parts: ['char/hair_buns', 'char/eyebrows_female'], hair: '#6a2a14' },
  raider_f2: { outfit: 'char/peasant_f', body: 'char/body_female', parts: ['char/hair_long', 'char/eyebrows_female'], hair: '#1c1612' },
};
const RAIDERS = [['Rask', 'raider_m1'], ['Vibe', 'raider_f1'], ['Bo', 'raider_m2'], ['Ragna', 'raider_f2'], ['Kaj', 'raider_m1'], ['Sus', 'raider_f1'], ['Ebbe', 'raider_m2'], ['Dorte', 'raider_f2']];
// Allies' own skills.
export const SKILLS = {
  ida: { name: 'Helbreder', note: 'Heler dig, når hun er tæt på' },
  mads: { name: 'Tømrer', note: 'Alt du bygger koster 25 % mindre' },
};
export const ROLE_NAMES = { follow: 'Følger dig', gather: 'Samler', guard: 'Vagt', rest: 'Hviler' };
const _v = new THREE.Vector3();

class Person {
  constructor(world, key, name, look, at, setup) {
    this.w = world;
    this.key = key;
    this.name = name;
    this.lookKey = look;
    this.char = makeCastaway(world.assets, LOOKS[look]);
    world.scene.add(this.char.root);
    this.pos = at.clone();
    this.yaw = 0;
    this.maxHp = 70;
    this.hp = 70;
    this.speed = 0;
    this.t = 0;
    this.loyalty = 0;
    this.post = at.clone();
    this.meal = MEAL * (0.5 + Math.random() * 0.5);
    Object.assign(this, setup);
    this.place();
  }

  get follower() { return this.side === 'ally' || this.side === 'thrall'; }
  get ceiling() { return this.side === 'ally' ? 100 : 0; }
  // Ally output falls off when they're unhappy; trælle always do the same, basic work.
  get output() { return this.side === 'ally' ? (this.loyalty >= 30 ? 1.6 : 1.1) : 1; }
  anim(name, fade = 0.3) { this.char.play(name, fade); }

  // Hit by one of your followers (only raiders take it).
  hurt(n) { if (this.side === 'hostile' && ['camp', 'attack', 'return', 'standup'].includes(this.state)) this.w.hit(this, n, false); return false; }
  get reach() { return 1.3; }

  step(dt, dir, speed) {
    const W = this.w;
    this.speed += (speed - this.speed) * Math.min(1, dt * 6);
    if (this.speed < 0.05) return;
    // Standing inside something already (a bush, after a fall)? Then just walk out of it.
    const stuck = W.blocked(this.pos.x, this.pos.z, 0.3, this.pos.y);
    for (const turn of [0, 0.5, -0.5, 1.1, -1.1, 1.8, -1.8]) {
      const a = Math.atan2(dir.x, dir.z) + turn;
      const nx = this.pos.x + Math.sin(a) * this.speed * dt, nz = this.pos.z + Math.cos(a) * this.speed * dt;
      if (W.island.heightAt(nx, nz) < -0.3 || (!stuck && W.blocked(nx, nz, 0.3, this.pos.y))) continue;
      this.pos.x = nx; this.pos.z = nz;
      let d = a - this.yaw;
      d = Math.atan2(Math.sin(d), Math.cos(d));
      this.yaw += d * Math.min(1, dt * 8);
      return;
    }
    this.speed = 0;
  }

  face(x, z, dt, k = 6) {
    let d = Math.atan2(x - this.pos.x, z - this.pos.z) - this.yaw;
    d = Math.atan2(Math.sin(d), Math.cos(d));
    this.yaw += d * Math.min(1, dt * k);
  }

  goTo(dt, x, z, near = 0.8, run = false) {
    const dx = x - this.pos.x, dz = z - this.pos.z, d = Math.hypot(dx, dz);
    if (d < near) { this.speed = 0; return true; }
    this.step(dt, _v.set(dx, 0, dz).normalize(), run ? 4.2 : 1.5);
    this.anim(run ? 'Jog_Fwd_Loop' : this.carrying ? 'Walk_Carry_Loop' : 'Walk_Loop', 0.2);
    return false;
  }

  place() {
    this.pos.y = this.w.ground(this.pos.x, this.pos.z, this.pos.y);
    this.char.root.position.copy(this.pos);
    this.char.root.rotation.y = this.yaw;
  }

  swing(dt, target, dmg, onHit) {
    if (this.punch == null) { this.punch = 0; this.anim(Math.random() < 0.5 ? 'Punch_Jab' : 'Punch_Cross', 0.1); }
    this.punch += dt;
    this.face(target.x, target.z, dt, 10);
    if (!this.landed && this.punch > 0.35) { this.landed = true; onHit(dmg); }
    if (this.punch > 0.9) { this.punch = null; this.landed = false; }
  }

  // Lying still (unconscious, bound or dead): the end of the fall.
  lie() { this.anim('Death01', 0.1); }

  update(dt, ctx) {
    this.char.mixer.update(dt);
    const W = this.w, P = ctx.player;
    const dx = P.x - this.pos.x, dz = P.z - this.pos.z, dist = Math.hypot(dx, dz);
    this.t -= dt;
    switch (this.state) {
      case 'injured': this.anim('Death01', 0); if (this.char.current) this.char.current.time = this.char.current.getClip().duration; break;
      case 'mending': this.anim('Fixing_Kneeling'); break;
      case 'getup':
        this.anim('LayToIdle', 0.1);
        if (this.t < 0) { this.state = this.side === 'captive' ? 'led' : 'cheer'; this.t = 1.6; if (this.state === 'cheer') this.anim('Yes', 0.2); }
        break;
      case 'cheer': if (this.t < 0) this.state = 'work'; break;
      case 'ambient': this.ambient(dt); break;
      case 'camp':
        this.anim(this.sit ? 'Sitting_Idle_Loop' : 'Idle_FoldArms_Loop');
        if (P.alive && dist < 13 && Math.hypot(P.x - this.post.x, P.z - this.post.z) < 22) { this.state = 'attack'; this.anim('Jog_Fwd_Loop', 0.2); }
        break;
      case 'attack':
        if (!P.alive || Math.hypot(this.pos.x - this.post.x, this.pos.z - this.post.z) > 32) { this.state = 'return'; break; }
        if (dist > 1.4 && this.punch == null) this.goTo(dt, P.x, P.z, 1.3, true);
        else this.swing(dt, P, 7, (n) => { if (Math.hypot(P.x - this.pos.x, P.z - this.pos.z) < 2.0) W.onPlayerHit?.(this, n); });
        break;
      case 'return':
        if (this.goTo(dt, this.post.x, this.post.z, 1)) { this.state = 'camp'; this.yaw = this.campYaw ?? this.yaw; }
        break;
      case 'out': // unconscious: wakes up angry if nobody binds them
        this.lie();
        if (this.t < 0) { this.state = 'standup'; this.t = 2.4; this.anim('LayToIdle', 0.1); }
        break;
      case 'standup':
        if (this.t < 0) { this.hp = Math.max(this.hp, this.maxHp * 0.4); this.state = P.alive && dist < 12 ? 'attack' : 'return'; }
        break;
      case 'bound': this.lie(); break; // bound and unconscious until you wake them
      case 'dead': this.lie(); if (this.t < -300) this.w.remove(this); break;
      case 'led': {
        // On the rope: walks a couple of metres behind you.
        if (!P.alive) { this.anim('Idle_Loop'); break; }
        if (dist > 2.6) this.goTo(dt, P.x - (P.fx ?? 0) * 1.8, P.z - (P.fz ?? 0) * 1.8, 1.0, dist > 7);
        else { this.speed = 0; this.anim('Idle_Loop'); this.face(P.x, P.z, dt, 3); }
        break;
      }
      case 'staked': // at the captive post, kneeling, until broken
        this.anim('Fixing_Kneeling');
        if (this.stake) this.face(this.stake.x, this.stake.z, dt, 4);
        if (this.t < 0) this.w.makeThrall(this);
        break;
      case 'work': this.work(dt, ctx, dist); break;
    }
    if (this.side === 'ally' && this.state === 'work') this.upkeep(dt, ctx);
    this.place();
  }

  ambient(dt) {
    const path = this.path;
    if (this.wait > 0) { this.wait -= dt; this.anim(this.wait > 1.5 ? 'Idle_Talking_Loop' : 'Idle_Loop'); return; }
    const [tx, tz] = path[(this.leg + 1) % path.length];
    if (this.goTo(dt, tx, tz, 0.4)) { this.leg = (this.leg + 1) % path.length; this.wait = 3 + Math.random() * 4; }
  }

  work(dt, ctx, dist) {
    const W = this.w, P = ctx.player, ally = this.side === 'ally';
    const fights = (this.role === 'follow' || this.role === 'guard');
    const threat = fights ? W.threatNear(this.role === 'follow' ? P : this.post, this.role === 'follow' ? 10 : ally ? 16 : 9) : null;
    if (threat && P.alive) {
      const tp = threat.pos;
      if (Math.hypot(tp.x - this.pos.x, tp.z - this.pos.z) > (threat.reach ?? 1.4) * 0.8 + 0.6 && this.punch == null) this.goTo(dt, tp.x, tp.z, 1.2, true);
      else this.swing(dt, tp, ally ? 10 : 5, (n) => threat.hurt?.(n, this.pos));
      return;
    }
    this.punch = null;
    if (this.role === 'follow') {
      if (!P.alive) { this.anim('Idle_Loop'); return; }
      if (dist > 60) this.pos.copy(W.spot(new THREE.Vector3(P.x, 0, P.z), 4));
      const k = W.list.filter((q) => q.side === 'ally' && q.role === 'follow').indexOf(this);
      const side = k % 2 ? 1 : -1, back = 2.6 + Math.floor(k / 2) * 1.4;
      const fx = P.x - (P.fx ?? 0) * back + (P.fz ?? 0) * side * 1.3, fz = P.z - (P.fz ?? 0) * back - (P.fx ?? 0) * side * 1.3;
      const dslot = Math.hypot(fx - this.pos.x, fz - this.pos.z);
      if (dslot > 1.2) { this.goTo(dt, fx, fz, 1.0, dslot > 7); return; }
      this.speed = 0;
      this.anim('Idle_Loop');
      this.face(P.x, P.z, dt, 2);
      return;
    }
    if (this.role === 'guard') {
      if (!this.goTo(dt, this.post.x, this.post.z, 0.6)) return;
      this.anim('Idle_FoldArms_Loop');
      return;
    }
    if (this.role === 'rest') {
      if (!this.goTo(dt, this.post.x, this.post.z, 0.6)) return;
      this.anim('Sitting_Idle_Loop');
      return;
    }
    // Gather: walk to something growing near the post, chop at it, carry it home.
    if (!this.job) {
      const n = W.workSpot(this.post);
      this.job = n ? { x: n.x, z: n.z, phase: 'go' } : { x: this.post.x + 2, z: this.post.z + 2, phase: 'go' };
    }
    const j = this.job;
    if (j.phase === 'go') { if (this.goTo(dt, j.x, j.z, 1.4)) { j.phase = 'chop'; j.t = ally ? 12 : 16; } }
    else if (j.phase === 'chop') { this.anim('TreeChopping_Loop'); this.face(j.x, j.z, dt); j.t -= dt; if (j.t < 0) { j.phase = 'back'; this.carrying = true; } }
    else if (j.phase === 'back') {
      if (this.goTo(dt, this.post.x, this.post.z, 1.0)) {
        this.carrying = false;
        const k = this.output;
        W.deliver(this, { wood: Math.round(2 * k), fiber: Math.round(2 * k), palm_leaf: Math.round(1 * k), bamboo: Math.round(1 * k) });
        this.job = null;
      }
    }
  }

  // Allies eat every few minutes — from a chest near their post, or your bag when they walk with you.
  upkeep(dt, ctx) {
    this.meal -= dt;
    if (this.meal > 0) return;
    this.meal = MEAL;
    const got = this.w.takeFood(this, ctx);
    this.loyalty = Math.max(0, Math.min(this.ceiling, this.loyalty + (got ? 6 : -12)));
    this.w.onMeal?.(this, got);
  }
}

export class People {
  constructor({ scene, assets, island, flora, building, camp }) {
    Object.assign(this, { scene, assets, island, flora, building });
    this.list = [];
    this.raiderN = 0;
    this.respawnT = 0;
    const I = island, at = (x, z) => new THREE.Vector3(x, I.heightAt(x, z), z);
    const jens = new Person(this, 'jens', 'Jens', 'jens', at(camp.x + 8, camp.z - 9), { side: 'neutral', state: 'ambient', path: [[camp.x + 8, camp.z - 9], [camp.x + 34, camp.z - 11], [camp.x + 22, camp.z - 16]], leg: 0, wait: 2 });
    const mx = camp.x + 3.5, mz = camp.z - 2.5;
    const mads = new Person(this, 'mads', 'Mads', 'mads', at(mx, mz), { side: 'neutral', state: 'mending', need: { rope: 2, wood: 6 }, ask: 'Hjælp mig med at få båden tæt — 2 reb og 6 træ — så går jeg med dig.' });
    mads.yaw = -2.2;
    const ix = 95, iz = I.shoreZ(95) - 5;
    const ida = new Person(this, 'ida', 'Ida', 'ida', at(ix, iz), { side: 'neutral', state: 'injured', need: { food: 3 }, ask: 'Ida er udmattet og såret. Hun har brug for mad — giv hende tre måltider.' });
    ida.yaw = 1.2;
    // The raiders' camp on the west headland: the most open, flattest spot in that stretch.
    let rx = -125, rz = I.shoreZ(-125) - 22, best = Infinity;
    for (let x = -160; x <= -95; x += 5) for (let back = 14; back <= 40; back += 4) {
      const z = I.shoreZ(x) - back;
      if (I.heightAt(x, z) < 1) continue;
      let crowd = 0;
      for (let a = 0; a < 8; a++) for (const r of [3, 6, 9]) if (flora.blocked(x + Math.cos(a * 0.785) * r, z + Math.sin(a * 0.785) * r, 0.5)) crowd += 10 - r;
      const score = crowd + I.slopeAt(x, z) * 40 + Math.abs(x + 125) * 0.05;
      if (score < best) { best = score; rx = x; rz = z; }
    }
    this.raidCamp = at(rx, rz);
    this.list.push(jens, mads, ida);
    this.addRaider([2, 1.5], -0.6, false);
    this.addRaider([-1.8, 1], 0.8, true);
    this.campProps(rx, rz);
    // The rope from your hand to a led captive.
    const g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]);
    this.rope = new THREE.Line(g, new THREE.LineBasicMaterial({ color: 0xc4a26a }));
    this.rope.frustumCulled = false;
    this.rope.visible = false;
    scene.add(this.rope);
  }

  addRaider(off, yaw, sit) {
    const [name, look] = RAIDERS[this.raiderN % RAIDERS.length];
    const key = `raider${this.raiderN++}`;
    const c = this.raidCamp;
    const q = new Person(this, key, name, look, new THREE.Vector3(c.x + off[0], 0, c.z + off[1]), { side: 'hostile', state: 'camp', sit, campYaw: yaw });
    q.yaw = yaw;
    this.list.push(q);
    return q;
  }

  remove(q) {
    q.char.root.removeFromParent();
    this.list = this.list.filter((p) => p !== q);
  }

  campProps(x, z) {
    const add = (key, px, pz, rot = 0) => {
      const o = this.assets[key].scene.clone(true);
      o.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
      o.position.set(px, this.island.heightAt(px, pz), pz);
      o.rotation.y = rot;
      this.scene.add(o);
    };
    add('build/lean_to', x - 1, z - 3.5, 0.3);
    add('build/campfire', x, z + 3);
    add('props/barrel', x + 3, z - 2.4);
    add('props/crate', x + 3.8, z - 1.3, 0.5);
  }

  ground(x, z, y) { return this.building.groundAt(x, z, y ?? this.island.heightAt(x, z)); }
  blocked(x, z, r, y) { return this.flora.blocked(x, z, r) || this.building.blockedAt(x, z, r, y ?? this.island.heightAt(x, z)); }

  spot(c, r) {
    for (let i = 0; i < 20; i++) {
      const a = Math.random() * Math.PI * 2, d = Math.sqrt(Math.random()) * r;
      const x = c.x + Math.cos(a) * d, z = c.z + Math.sin(a) * d;
      if (this.island.heightAt(x, z) > 0.2 && !this.blocked(x, z, 0.4)) return new THREE.Vector3(x, this.island.heightAt(x, z), z);
    }
    return c.clone();
  }

  workSpot(post) {
    const near = this.flora.nodesNear(post.x, post.z).filter((n) => ['palm', 'palm_young', 'bush', 'bamboo', 'treefern', 'banana', 'leafy'].includes(n.kind) && Math.hypot(n.x - post.x, n.z - post.z) < 14);
    return near.length ? near[Math.floor(Math.random() * near.length)] : null;
  }

  chestNear(p, r = 25) {
    let best = null, bd = r;
    for (const q of this.building.pieces) if (q.id === 'chest') { const d = Math.hypot(q.x - p.x, q.z - p.z); if (d < bd) { bd = d; best = q; } }
    return best;
  }

  deliver(person, items) {
    const chest = this.chestNear(person.post);
    if (chest) for (const [k, n] of Object.entries(items)) chest.storage[k] = (chest.storage[k] ?? 0) + n;
    this.onDeliver?.(person, items, chest);
  }

  takeFood(person, ctx) {
    if (person.role === 'follow') { const f = FOOD.find((k) => ctx.inv.count(k) > 0); if (f) { ctx.inv.remove(f, 1); return f; } }
    const chest = this.chestNear(person.post);
    if (chest) { const f = FOOD.find((k) => (chest.storage[k] ?? 0) > 0); if (f) { chest.storage[f] -= 1; if (!chest.storage[f]) delete chest.storage[f]; return f; } }
    return null;
  }

  threatNear(at, r) {
    for (const c of this.creatures?.list ?? []) if (!c.dead && !c.tamed && (c.state === 'chase' || c.state === 'bite') && Math.hypot(c.pos.x - at.x, c.pos.z - at.z) < r) return c;
    for (const q of this.list) if (q.side === 'hostile' && q.state === 'attack' && Math.hypot(q.pos.x - at.x, q.pos.z - at.z) < r) return q;
    return null;
  }

  // A træl on guard keeps animals from charging near their post.
  feared(x, z) { return this.list.some((q) => q.follower && q.role === 'guard' && Math.hypot(q.pos.x - x, q.pos.z - z) < 12); }

  ally(key) { const q = this.list.find((p) => p.key === key); return q?.side === 'ally' && q.loyalty >= 30 ? q : null; }

  // Building costs less while Mads (carpenter) is your ally.
  costFactor() { return this.ally('mads') ? 0.75 : 1; }

  update(dt, ctx) {
    const P = ctx.player;
    for (const q of [...this.list]) {
      const d = Math.hypot(q.pos.x - P.x, q.pos.z - P.z);
      q.char.root.visible = d < 150;
      if (d > 170 && !q.follower && q.state !== 'led') continue;
      q.update(dt, ctx);
    }
    // Ida heals you when she's near.
    const ida = this.ally('ida');
    if (ida && P.alive && Math.hypot(ida.pos.x - P.x, ida.pos.z - P.z) < 7) this.onHeal?.(2.5 * dt);
    // The rope to a led captive.
    const led = this.list.find((q) => q.state === 'led');
    this.rope.visible = !!led;
    if (led) {
      const a = this.rope.geometry.attributes.position;
      a.setXYZ(0, P.x + (P.fz ?? 0) * 0.25 + (P.fx ?? 0) * 0.3, (P.y ?? led.pos.y + 1.6) - 0.55, P.z - (P.fx ?? 0) * 0.25 + (P.fz ?? 0) * 0.3);
      a.setXYZ(1, led.pos.x, led.pos.y + 1.0, led.pos.z);
      a.needsUpdate = true;
    }
    // New raiders turn up at the camp when there are fewer than two.
    const raiders = this.list.filter((q) => q.side === 'hostile' && q.state !== 'dead').length;
    if (raiders < 2) { this.respawnT += dt; if (this.respawnT > 480) { this.respawnT = 0; this.addRaider([Math.random() * 4 - 2, 1.5], Math.random() * 2 - 1, Math.random() < 0.5); } }
    else this.respawnT = 0;
  }

  inArc(p, f, reach, cosMin) {
    return this.list.filter((q) => {
      if (q.side !== 'hostile' && q.side !== 'captive' && q.side !== 'neutral') return false;
      if (q.state === 'dead') return false;
      const dx = q.pos.x - p.x, dz = q.pos.z - p.z, d = Math.hypot(dx, dz);
      if (d - 0.3 > reach) return false;
      return d < 0.6 || (dx * f.x + dz * f.y) / d > cosMin;
    });
  }

  personNear(p, f, reach = 3.0) {
    let best = null, bd = Infinity;
    for (const q of this.list) {
      if (q.side === 'hostile' && !['out', 'dead'].includes(q.state)) continue;
      if (q.state === 'dead' && q.searched) continue;
      const dx = q.pos.x - p.x, dz = q.pos.z - p.z, d = Math.hypot(dx, dz);
      if (d > reach + 0.4) continue;
      const cos = (dx * f.x + dz * f.y) / Math.max(0.01, d);
      if (cos < 0.6 && d > 1) continue;
      if (d < bd) { bd = d; best = q; }
    }
    return best;
  }

  // Your blow lands. Blades kill at 0; a club blow that leaves them under 10 % knocks them out
  // instead — but one that takes them to 0 still kills. Returns 'out', 'dead' or null.
  hit(q, n, blunt) {
    if (q.state === 'dead') return null;
    // Strangers: the first blow is a warning (no harm done); hit them again within a few seconds
    // and they fight back — and are fair game from then on.
    if (q.side === 'neutral') {
      const now = performance.now() / 1000;
      if (!(now - (q.provoked ?? -99) < 8)) { q.provoked = now; if (!['injured', 'mending'].includes(q.state)) q.anim('Hit_Chest', 0.05); return 'warn'; }
      q.side = 'hostile';
      q.need = null;
      q.post = q.pos.clone();
      q.campYaw = q.yaw;
      q.state = 'attack';
      q.anim('Jog_Fwd_Loop', 0.2);
    }
    const down = ['out', 'bound', 'led', 'staked'].includes(q.state);
    if (down && !blunt) return this.kill(q);
    if (down) return null;
    q.hp -= n;
    if (q.hp <= 0) return this.kill(q);
    if (blunt && q.hp <= q.maxHp * KNOCKOUT) { q.state = 'out'; q.t = OUT; q.punch = null; q.anim('Death01', 0.1); return 'out'; }
    q.anim(Math.random() < 0.5 ? 'Hit_Chest' : 'Hit_Head', 0.05);
    q.punch = null;
    if (q.state === 'camp' || q.state === 'return') q.state = 'attack';
    return null;
  }

  kill(q) {
    q.state = 'dead';
    q.side = 'hostile';
    q.hp = 0;
    q.t = 0;
    q.punch = null;
    q.anim('Death01', 0.1);
    return 'dead';
  }

  // Search the dead.
  search(q) {
    q.searched = true;
    return { rope: 1, meat_cooked: 1, fiber: 3, stone: 2 };
  }

  // Earn: hand over what they asked for.
  give(q, inv) {
    if (q.need.food) {
      const f = FOOD.find((k) => inv.count(k) > 0);
      if (!f) return { warn: true, text: 'Du har ingen mad at give' };
      inv.remove(f, 1);
      q.fed = (q.fed ?? 0) + 1;
      if (q.fed < q.need.food) return { text: `${q.name} spiser (${q.fed}/${q.need.food})`, item: f };
      this.join(q, 'ally');
      q.state = 'getup'; q.t = 2.4;
      return { text: `${q.name} kommer på benene: "Tak. Jeg står i gæld til dig." — hun er din allierede (${SKILLS.ida.name})`, good: true, xp: 40 };
    }
    const missing = Object.entries(q.need).filter(([k, n]) => inv.count(k) < n);
    if (missing.length) return { warn: true, text: `${q.name}: "${q.ask}"` };
    for (const [k, n] of Object.entries(q.need)) inv.remove(k, n);
    this.join(q, 'ally');
    q.state = 'cheer'; q.t = 1.6; q.anim('Yes', 0.2);
    return { text: `${q.name}: "Godt arbejde — jeg er med." — han er din allierede (${SKILLS.mads.name})`, good: true, xp: 40 };
  }

  // Force, step 1: bind the unconscious with a rope (they stay out until you wake them).
  bind(q, inv) {
    if (q.state !== 'out') return null;
    if (inv.count('rope') < 1) return { warn: true, text: 'Du skal bruge et reb for at binde dem' };
    inv.remove('rope', 1);
    q.state = 'bound';
    q.side = 'captive';
    return { text: `${q.name} er bundet. Væk dem (E) og før dem til en fangepæl i din lejr.`, good: true };
  }

  // Step 2: wake them; they get up and follow you on the rope. Only one at a time.
  wake(q) {
    if (this.list.some((p) => p.state === 'led')) return { warn: true, text: 'Du fører allerede en fange' };
    q.state = 'getup'; q.t = 2.4;
    return { text: `${q.name} vågner — bundet og i reb bag dig.`, good: true };
  }

  // Step 3: tie them to a captive post; after a while they're your træl.
  stake(q, post) {
    q.state = 'staked';
    q.t = BREAK;
    q.stake = post;
    q.pos.set(post.x + Math.sin(post.rot) * 0.9, 0, post.z + Math.cos(post.rot) * 0.9);
    post.captive = q;
    return { text: `${q.name} er bundet til pælen. Om et minut er de din træl.`, good: true };
  }

  makeThrall(q) {
    const post = q.stake;
    if (post) post.captive = null;
    q.stake = null;
    q.side = 'thrall';
    q.state = 'work';
    q.role = 'gather';
    q.post = q.pos.clone();
    q.hp = q.maxHp;
    this.onThrall?.(q);
  }

  join(q, side) {
    q.side = side;
    q.loyalty = 60;
    q.role = 'follow';
    q.post = q.pos.clone();
    q.hp = q.maxHp;
    q.meal = MEAL;
    this.onJoin?.(q);
  }

  setRole(q, role, at) {
    if (role === 'follow' && q.side !== 'ally') return false;
    q.role = role;
    q.job = null;
    q.carrying = false;
    if (role !== 'follow') q.post = at.clone();
    return true;
  }

  serialize() {
    return {
      n: this.raiderN,
      list: this.list.map((q) => ({ k: q.key, name: q.name, look: q.lookKey, side: q.side, state: ['getup', 'cheer'].includes(q.state) ? (q.side === 'captive' ? 'led' : 'work') : q.state, l: Math.round(q.loyalty), role: q.role, post: q.post && [+q.post.x.toFixed(2), +q.post.z.toFixed(2)], pos: [+q.pos.x.toFixed(2), +q.pos.z.toFixed(2)], fed: q.fed, meal: Math.round(q.meal), t: Math.round(q.t), searched: q.searched ? 1 : 0, sit: q.sit ? 1 : 0, yaw: +(q.campYaw ?? 0).toFixed(2) })),
    };
  }

  restore(data) {
    if (!data) return;
    const list = Array.isArray(data) ? data : data.list;
    // Old saves (D-023): "bound" people become trælle.
    for (const o of list ?? []) {
      if (o.side === 'bound') o.side = 'thrall';
      let q = this.list.find((p) => p.key === o.k);
      if (!q && o.look) {
        q = new Person(this, o.k, o.name, o.look, new THREE.Vector3(o.pos[0], 0, o.pos[1]), { side: o.side, sit: !!o.sit, campYaw: o.yaw });
        this.list.push(q);
      }
      if (!q) continue;
      const state = ['out', 'standup', 'attack'].includes(o.state) ? 'return' : o.state === 'staked' ? 'led' : o.state;
      Object.assign(q, { side: o.side, state, loyalty: o.l ?? 0, role: o.role, fed: o.fed, meal: o.meal ?? MEAL, searched: !!o.searched });
      if (o.post) q.post = new THREE.Vector3(o.post[0], this.island.heightAt(o.post[0], o.post[1]), o.post[1]);
      if (o.pos && (q.follower || ['bound', 'led', 'dead'].includes(state))) q.pos.set(o.pos[0], this.island.heightAt(o.pos[0], o.pos[1]), o.pos[1]);
      if (state === 'dead') q.t = o.t ?? 0;
      q.place();
    }
    // Raiders from an old save that no longer exist in the list are dropped; keep numbering going.
    if (!Array.isArray(data)) this.raiderN = Math.max(this.raiderN, data.n ?? 0);
    const keys = new Set((list ?? []).map((o) => o.k));
    if (!Array.isArray(data)) for (const q of [...this.list]) if (q.side === 'hostile' && q.key.startsWith('raider') && !keys.has(q.key)) this.remove(q);
    if (Array.isArray(data)) {
      // Old saves keyed raiders 'rask' / 'vibe'; map them onto the first two raiders.
      for (const [old, i] of [['rask', 0], ['vibe', 1]]) { const o = list.find((x) => x.k === old); const q = this.list.find((p) => p.key === `raider${i}`); if (o && q && o.side !== 'hostile') { Object.assign(q, { side: o.side === 'bound' ? 'thrall' : o.side, state: o.state === 'flee' ? 'return' : 'work', role: o.role ?? 'gather' }); if (q.follower && o.pos) { q.pos.set(o.pos[0], 0, o.pos[1]); q.post = q.pos.clone(); } q.place(); } }
    }
  }
}
