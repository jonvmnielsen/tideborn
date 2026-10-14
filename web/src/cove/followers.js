// People of the cove and the follower layer (D-023, Docs/FOLLOWERS_RULES.md). Two ways to get
// people on your side, and the way you got them is for good:
//   Ally (earn)  — rescue Ida, who lies hurt on the far beach (bring her food), or help Mads fix his
//                  boat (bring rope and wood). Allies start at loyalty 60 and can reach 95; only an
//                  ally will walk with you (and fight what attacks you).
//   Bound (force) — the two raiders on the west headland attack anyone who comes near their camp.
//                  Beat one down and bind them with a rope before they get up. Bound start at 25,
//                  can reach 65, and work 50 % harder for food alone — but if they go hungry and
//                  their loyalty falls below 15, they run back to the raiders.
// Roles: Følg (allies), Saml (gathers near where you posted them and puts it in the nearest chest),
// Vagt (guards their post and fights animals and raiders that come near; a bound guard also keeps
// animals away), Hvil. Every few minutes each follower eats — from a chest near their post, or from
// your bag when they walk with you — and loyalty follows whether they were fed.
import * as THREE from 'three';
import { makeCastaway } from './npc.js';

const MEAL = 300;            // seconds between meals
const FOOD = ['meat_cooked', 'banana', 'coconut', 'meat'];
const LOOK = {
  ida: { outfit: 'char/peasant_f', body: 'char/body_female', parts: ['char/hair_long', 'char/eyebrows_female'], hair: '#3a2418' },
  mads: { outfit: 'char/ranger', parts: ['char/hair_beard', 'char/eyebrows'], hair: '#2a1e16' },
  jens: { outfit: 'char/peasant', parts: ['char/hair_beard', 'char/hair_parted', 'char/eyebrows'], hair: '#5a3a22' },
  rask: { outfit: 'char/ranger', parts: ['char/hair_buzzed', 'char/eyebrows'], hair: '#1a1410' },
  vibe: { outfit: 'char/ranger_f', body: 'char/body_female', parts: ['char/hair_buns', 'char/eyebrows_female'], hair: '#6a2a14' },
};
export const ROLE_NAMES = { follow: 'Følger dig', gather: 'Samler', guard: 'Vagt', rest: 'Hviler' };
const _v = new THREE.Vector3();

class Person {
  constructor(world, key, name, at, setup) {
    this.w = world;
    this.key = key;
    this.name = name;
    this.char = makeCastaway(world.assets, LOOK[key]);
    world.scene.add(this.char.root);
    this.pos = at.clone();
    this.yaw = 0;
    this.hp = 70;
    this.speed = 0;
    this.t = 0;
    this.loyalty = 0;
    this.post = at.clone();
    this.meal = MEAL * (0.5 + Math.random() * 0.5);
    Object.assign(this, setup);
    this.place();
  }

  get ceiling() { return this.side === 'ally' ? 95 : this.side === 'bound' ? 65 : 0; }
  get follower() { return this.side === 'ally' || this.side === 'bound'; }
  anim(name, fade = 0.3) { this.char.play(name, fade); }

  // Hit by a follower (raiders only take it; the others are on your side or not fighting).
  hurt(n) { if (this.side === 'hostile' && this.state !== 'down' && this.state !== 'standup') this.w.hit(this, n); return false; }
  get reach() { return 1.3; }

  step(dt, dir, speed) {
    const W = this.w;
    this.speed += (speed - this.speed) * Math.min(1, dt * 6);
    if (this.speed < 0.05) return;
    for (const turn of [0, 0.5, -0.5, 1.1, -1.1, 1.8, -1.8]) {
      const a = Math.atan2(dir.x, dir.z) + turn;
      const nx = this.pos.x + Math.sin(a) * this.speed * dt, nz = this.pos.z + Math.cos(a) * this.speed * dt;
      if (W.island.heightAt(nx, nz) < -0.3 || W.blocked(nx, nz, 0.3, this.pos.y)) continue;
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

  // A punch at the target; damage lands mid-swing.
  swing(dt, target, dmg, onHit) {
    if (this.punch == null) { this.punch = 0; this.anim(Math.random() < 0.5 ? 'Punch_Jab' : 'Punch_Cross', 0.1); }
    this.punch += dt;
    this.face(target.x, target.z, dt, 10);
    if (!this.landed && this.punch > 0.35) { this.landed = true; onHit(dmg); }
    if (this.punch > 0.9) { this.punch = null; this.landed = false; }
  }

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
        if (this.t < 0) { this.state = 'cheer'; this.t = 1.6; this.anim('Yes', 0.2); }
        break;
      case 'cheer': if (this.t < 0) this.state = 'work'; break;
      case 'ambient': this.ambient(dt); break;
      case 'camp':
        // Raiders: idle round their fire; anyone close to the camp is attacked.
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
      case 'down':
        if (this.t < 0) { this.state = 'standup'; this.t = 2.4; this.anim('LayToIdle', 0.1); }
        break;
      case 'standup':
        if (this.t < 0) { this.hp = 40; this.state = P.alive && dist < 12 ? 'attack' : 'return'; }
        break;
      case 'flee':
        if (this.goTo(dt, this.post.x, this.post.z, 1.5, true)) { this.state = 'camp'; }
        break;
      case 'work': this.work(dt, ctx, dist, dx, dz); break;
    }
    if (this.follower && this.state === 'work') this.upkeep(dt, ctx);
    this.place();
  }

  ambient(dt) {
    const path = this.path;
    if (this.wait > 0) { this.wait -= dt; this.anim(this.wait > 1.5 ? 'Idle_Talking_Loop' : 'Idle_Loop'); return; }
    const [tx, tz] = path[(this.leg + 1) % path.length];
    if (this.goTo(dt, tx, tz, 0.4)) { this.leg = (this.leg + 1) % path.length; this.wait = 3 + Math.random() * 4; }
  }

  // Following, gathering, guarding or resting.
  work(dt, ctx, dist, dx, dz) {
    const W = this.w, P = ctx.player;
    // Anything attacking you (when walking with you) or coming near the post (guard) gets punched.
    const threat = this.role === 'follow' || this.role === 'guard' ? W.threatNear(this.role === 'follow' ? P : this.post, this.role === 'follow' ? 10 : 16) : null;
    if (threat && P.alive) {
      const tp = threat.pos;
      if (Math.hypot(tp.x - this.pos.x, tp.z - this.pos.z) > (threat.reach ?? 1.4) * 0.8 + 0.6 && this.punch == null) this.goTo(dt, tp.x, tp.z, 1.2, true);
      else this.swing(dt, tp, this.side === 'bound' ? 9 : 8, (n) => threat.hurt?.(n, this.pos));
      return;
    }
    this.punch = null;
    if (this.role === 'follow') {
      if (!P.alive) { this.anim('Idle_Loop'); return; }
      if (dist > 60) this.pos.copy(W.spot(new THREE.Vector3(P.x, 0, P.z), 4));
      // Each follower has its own place behind you, so they don't stand in one another.
      const k = this.w.list.filter((q) => q.follower && q.role === 'follow').indexOf(this);
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
    if (j.phase === 'go') { if (this.goTo(dt, j.x, j.z, 1.4)) { j.phase = 'chop'; j.t = 14; } }
    else if (j.phase === 'chop') { this.anim('TreeChopping_Loop'); this.face(j.x, j.z, dt); j.t -= dt; if (j.t < 0) { j.phase = 'back'; this.carrying = true; } }
    else if (j.phase === 'back') {
      if (this.goTo(dt, this.post.x, this.post.z, 1.0)) {
        this.carrying = false;
        const k = this.side === 'bound' ? 1.5 : 1;
        W.deliver(this, { wood: Math.round(2 * k), fiber: Math.round(3 * k), palm_leaf: Math.round(1 * k), bamboo: Math.round(1 * k) });
        this.job = null;
      }
    }
  }

  // Meals: from a chest near the post, or your bag when they walk with you.
  upkeep(dt, ctx) {
    this.meal -= dt;
    if (this.meal > 0) return;
    this.meal = MEAL;
    const got = this.w.takeFood(this, ctx);
    this.loyalty = Math.max(0, Math.min(this.ceiling, this.loyalty + (got ? 6 : -12)));
    this.w.onMeal?.(this, got);
    if (this.side === 'bound' && this.loyalty < 15) this.w.escape(this);
  }
}

export class People {
  constructor({ scene, assets, island, flora, building, camp }) {
    Object.assign(this, { scene, assets, island, flora, building });
    this.list = [];
    const I = island, at = (x, z) => new THREE.Vector3(x, I.heightAt(x, z), z);
    // Jens walks the beach by the camp (ambient); Mads mends his boat and wants help.
    const jens = new Person(this, 'jens', 'Jens', at(camp.x + 8, camp.z - 9), { side: 'neutral', state: 'ambient', path: [[camp.x + 8, camp.z - 9], [camp.x + 34, camp.z - 11], [camp.x + 22, camp.z - 16]], leg: 0, wait: 2 });
    const mx = camp.x + 3.5, mz = camp.z - 2.5;
    const mads = new Person(this, 'mads', 'Mads', at(mx, mz), { side: 'neutral', state: 'mending', need: { rope: 2, wood: 6 }, ask: 'Hjælp mig med at få båden tæt — 2 reb og 6 træ — så går jeg med dig.' });
    mads.yaw = -2.2;
    // Ida lies hurt among the rocks on the far (east) beach.
    const ix = 95, iz = I.shoreZ(95) - 5;
    const ida = new Person(this, 'ida', 'Ida', at(ix, iz), { side: 'neutral', state: 'injured', need: { food: 3 }, ask: 'Ida er udmattet og såret. Hun har brug for mad — giv hende tre måltider.' });
    ida.yaw = 1.2;
    // The raiders' camp on the west headland: a lean-to and a fire.
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
    const rask = new Person(this, 'rask', 'Rask', at(rx + 2, rz + 1.5), { side: 'hostile', state: 'camp', campYaw: -0.6 });
    const vibe = new Person(this, 'vibe', 'Vibe', at(rx - 1.8, rz + 1), { side: 'hostile', state: 'camp', sit: true, campYaw: 0.8 });
    rask.yaw = rask.campYaw; vibe.yaw = vibe.campYaw;
    this.list.push(jens, mads, ida, rask, vibe);
    this.campProps(rx, rz);
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

  // Something growing near a post to work at.
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
    if (chest) { for (const [k, n] of Object.entries(items)) chest.storage[k] = (chest.storage[k] ?? 0) + n; this.onDeliver?.(person, items, chest); }
    else this.onDeliver?.(person, items, null);
  }

  takeFood(person, ctx) {
    if (person.role === 'follow') { const f = FOOD.find((k) => ctx.inv.count(k) > 0); if (f) { ctx.inv.remove(f, 1); return f; } }
    const chest = this.chestNear(person.post);
    if (chest) { const f = FOOD.find((k) => (chest.storage[k] ?? 0) > 0); if (f) { chest.storage[f] -= 1; if (!chest.storage[f]) delete chest.storage[f]; return f; } }
    return null;
  }

  escape(p) {
    p.side = 'hostile';
    p.state = 'flee';
    p.post = this.raidCamp.clone();
    this.onEscape?.(p);
  }

  // Animals or raiders that are going for you (or near a post).
  threatNear(at, r) {
    const out = [];
    for (const c of this.creatures?.list ?? []) if (!c.dead && !c.tamed && (c.state === 'chase' || c.state === 'bite') && Math.hypot(c.pos.x - at.x, c.pos.z - at.z) < r) out.push(c);
    for (const q of this.list) if (q.side === 'hostile' && q.state === 'attack' && Math.hypot(q.pos.x - at.x, q.pos.z - at.z) < r) out.push(q);
    return out[0] ?? null;
  }

  // A bound guard keeps animals from charging near their post.
  feared(x, z) { return this.list.some((q) => q.side === 'bound' && q.role === 'guard' && Math.hypot(q.pos.x - x, q.pos.z - z) < 12); }

  update(dt, ctx) {
    for (const q of this.list) {
      const d = Math.hypot(q.pos.x - ctx.player.x, q.pos.z - ctx.player.z);
      q.char.root.visible = d < 150;
      if (d > 170 && !q.follower) continue;
      q.update(dt, ctx);
    }
  }

  // A hostile in the arc of your swing.
  inArc(p, f, reach, cosMin) {
    return this.list.filter((q) => {
      if (q.side !== 'hostile' || q.state === 'down' || q.state === 'standup') return false;
      const dx = q.pos.x - p.x, dz = q.pos.z - p.z, d = Math.hypot(dx, dz);
      if (d - 0.3 > reach) return false;
      return d < 0.6 || (dx * f.x + dz * f.y) / d > cosMin;
    });
  }

  // Someone in front of you to talk to, rescue, bind or give orders.
  personNear(p, f, reach = 3.0) {
    let best = null, bd = Infinity;
    for (const q of this.list) {
      if (q.side === 'hostile' && q.state !== 'down') continue;
      const dx = q.pos.x - p.x, dz = q.pos.z - p.z, d = Math.hypot(dx, dz);
      if (d > reach + 0.4) continue;
      const cos = (dx * f.x + dz * f.y) / Math.max(0.01, d);
      if (cos < 0.6 && d > 1) continue;
      if (d < bd) { bd = d; best = q; }
    }
    return best;
  }

  // Your swing lands on a raider.
  hit(q, n) {
    q.hp -= n;
    if (q.hp <= 0) { q.state = 'down'; q.t = 45; q.punch = null; q.anim('Death01', 0.1); return true; }
    q.anim(Math.random() < 0.5 ? 'Hit_Chest' : 'Hit_Head', 0.05);
    q.punch = null;
    if (q.state === 'camp' || q.state === 'return') q.state = 'attack';
    return false;
  }

  // Earn: hand over what they asked for. Returns a message.
  give(q, inv) {
    if (q.need.food) {
      const f = FOOD.find((k) => inv.count(k) > 0);
      if (!f) return { warn: true, text: 'Du har ingen mad at give' };
      inv.remove(f, 1);
      q.fed = (q.fed ?? 0) + 1;
      if (q.fed < q.need.food) return { text: `${q.name} spiser (${q.fed}/${q.need.food})`, item: f };
      this.join(q, 'ally');
      q.state = 'getup'; q.t = 2.4;
      return { text: `${q.name} kommer på benene: "Tak. Jeg står i gæld til dig." — hun er din allierede`, good: true };
    }
    const missing = Object.entries(q.need).filter(([k, n]) => inv.count(k) < n);
    if (missing.length) return { warn: true, text: `${q.name}: "${q.ask}"` };
    for (const [k, n] of Object.entries(q.need)) inv.remove(k, n);
    this.join(q, 'ally');
    q.state = 'cheer'; q.t = 1.6; q.anim('Yes', 0.2);
    return { text: `${q.name}: "Godt arbejde — jeg er med." — han er din allierede`, good: true };
  }

  // Force: bind a beaten raider with a rope.
  bind(q, inv) {
    if (q.state !== 'down') return null;
    if (inv.count('rope') < 1) return { warn: true, text: 'Du skal bruge et reb for at binde dem' };
    inv.remove('rope', 1);
    this.join(q, 'bound');
    q.state = 'getup'; q.t = 2.4;
    return { text: `${q.name} er bundet. Bundne arbejder hårdt for mad, men stikker af, hvis de sulter.`, good: true };
  }

  join(q, side) {
    q.side = side;
    q.loyalty = side === 'ally' ? 60 : 25;
    q.role = side === 'ally' ? 'follow' : 'gather';
    q.post = q.pos.clone();
    q.hp = 70;
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
    return this.list.map((q) => ({ k: q.key, side: q.side, state: q.state === 'getup' || q.state === 'cheer' ? 'work' : q.state, l: Math.round(q.loyalty), role: q.role, post: q.post && [+q.post.x.toFixed(2), +q.post.z.toFixed(2)], pos: [+q.pos.x.toFixed(2), +q.pos.z.toFixed(2)], fed: q.fed, meal: Math.round(q.meal) }));
  }

  restore(list) {
    for (const o of list ?? []) {
      const q = this.list.find((p) => p.key === o.k);
      if (!q) continue;
      Object.assign(q, { side: o.side, state: o.state === 'down' || o.state === 'standup' || o.state === 'attack' ? 'return' : o.state, loyalty: o.l ?? 0, role: o.role, fed: o.fed, meal: o.meal ?? MEAL });
      if (o.post) q.post = new THREE.Vector3(o.post[0], this.island.heightAt(o.post[0], o.post[1]), o.post[1]);
      if (o.pos && q.follower) q.pos.set(o.pos[0], this.island.heightAt(o.pos[0], o.pos[1]), o.pos[1]);
      q.place();
    }
  }
}
