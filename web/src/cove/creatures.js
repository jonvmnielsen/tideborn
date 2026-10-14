// Land animals of the cove (D-021): real, known animals with skinned models and their own clips
// (Quaternius, CC0). Each species is data — how big, how fast, how tough, how it behaves:
//   prey      grazes and wanders near its home; bolts when you come close or hit it
//   hostile   wanders; hunts you when you come within its range (wider at night), bites, gives up
//             when you get far from its home or it is badly hurt
//   territorial  like prey, but charges if you come too close, then turns away
// A swing that catches an animal in its arc hurts it (it flinches, bleeds a little); at 0 it falls
// over and lies as a carcass you can butcher (E / tap) for meat and hide. Dead animals come back
// after a while, somewhere near their home.
import * as THREE from 'three';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';

export const SPECIES = {
  doe: { name: 'Hind', model: 'animal/doe', height: 1.35, hp: 50, walk: 1.3, run: 7.5, kind: 'prey', scare: 13, loot: { meat: 3, hide: 2 }, herd: 4,
    tame: { food: ['banana', 'coconut'], feeds: 4, carry: 60, use: 'Pakdyr: bærer 60 kg for dig' } },
  stag: { name: 'Kronhjort', model: 'animal/stag', height: 2.0, hp: 90, walk: 1.3, run: 7, kind: 'territorial', scare: 9, charge: 6, damage: 14, loot: { meat: 5, hide: 3 },
    tame: { food: ['banana', 'coconut'], feeds: 7, carry: 140, use: 'Stærkt pakdyr: bærer 140 kg' } },
  fox: { name: 'Ræv', model: 'animal/fox', height: 0.55, hp: 25, walk: 1.6, run: 6.5, kind: 'prey', scare: 9, loot: { meat: 1, hide: 1 } },
};

const UP = new THREE.Vector3(0, 1, 0);
const NAMES = ['Freja', 'Ronja', 'Sigga', 'Kvik', 'Luna', 'Tove', 'Birk', 'Odin', 'Mynte', 'Saga', 'Rap', 'Loke'];
const _v = new THREE.Vector3();

function clipNamed(clips, ...names) {
  for (const n of names) { const c = clips.find((k) => k.name.toLowerCase() === n); if (c) return c; }
  for (const n of names) { const c = clips.find((k) => k.name.toLowerCase().includes(n)); if (c) return c; }
  return null;
}

class Creature {
  constructor(world, sp, id, home) {
    this.w = world;
    this.sp = sp;
    this.id = id;
    this.home = home.clone();
    const src = world.assets[sp.model];
    this.root = new THREE.Group();
    this.body = cloneSkinned(src.scene);
    this.body.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; } });
    this.body.scale.setScalar(world.scaleFor(sp));
    this.root.add(this.body);
    world.root.add(this.root);
    this.mixer = new THREE.AnimationMixer(this.body);
    const clips = src.animations ?? [];
    this.clips = {
      idle: clipNamed(clips, 'idle'), walk: clipNamed(clips, 'walk'), run: clipNamed(clips, 'run', 'gallop'),
      eat: clipNamed(clips, 'eat', 'eating'), attack: clipNamed(clips, 'attack'), death: clipNamed(clips, 'death', 'die'),
    };
    this.current = null;
    // How close its mouth gets: about a body length from its middle.
    this.reach = sp.reach ?? sp.height * 0.95 + 0.4;
    this.reset();
  }

  reset() {
    this.trust = 0;
    this.tamed = false;
    this.calm = 0;
    const p = this.w.spot(this.home, 10);
    this.pos = p;
    this.yaw = Math.random() * Math.PI * 2;
    this.hp = this.sp.hp;
    this.state = 'idle';
    this.t = Math.random() * 3;
    this.dead = false;
    this.butchered = false;
    this.fall = 0;
    this.flinch = 0;
    this.speed = 0;
    this.root.visible = true;
    this.body.rotation.set(0, 0, 0);
    this.play('idle');
  }

  play(name, fade = 0.25) {
    const clip = this.clips[name] ?? this.clips.idle;
    if (!clip) return;
    const a = this.mixer.clipAction(clip);
    if (this.current === a) return;
    a.reset().setEffectiveWeight(1);
    if (fade > 0) a.fadeIn(fade);
    a.play();
    if (this.current) { if (fade > 0) this.current.fadeOut(fade); else this.current.stop(); }
    this.current = a;
  }

  // Move toward a heading, sliding round trees, rocks and buildings; never into the sea.
  step(dt, dir, speed) {
    const W = this.w;
    this.speed += (speed - this.speed) * Math.min(1, dt * 5);
    if (this.speed < 0.05) return;
    let best = null;
    for (const turn of [0, 0.5, -0.5, 1.1, -1.1, 1.8, -1.8]) {
      const a = Math.atan2(dir.x, dir.z) + turn;
      const nx = this.pos.x + Math.sin(a) * this.speed * dt, nz = this.pos.z + Math.cos(a) * this.speed * dt;
      if (W.island.heightAt(nx, nz) < 0.25 || W.blocked(nx, nz, this.sp.height * 0.25)) continue;
      if (W.player && Math.hypot(nx - W.player.x, nz - W.player.z) < this.reach * 0.8 && Math.hypot(nx - W.player.x, nz - W.player.z) < Math.hypot(this.pos.x - W.player.x, this.pos.z - W.player.z)) continue;
      best = { a, nx, nz };
      break;
    }
    if (!best) { this.speed = 0; return; }
    this.pos.x = best.nx; this.pos.z = best.nz;
    let d = best.a - this.yaw;
    d = Math.atan2(Math.sin(d), Math.cos(d));
    this.yaw += d * Math.min(1, dt * 6);
  }

  update(dt, player) {
    const sp = this.sp, W = this.w;
    this.mixer.update(dt * (this.state === 'flee' || this.state === 'chase' ? 1.1 : 1));
    if (this.dead) {
      // Procedural fall onto its side (the clips have no death), then lie still.
      this.fall = Math.min(1, this.fall + dt * 2.2);
      this.body.rotation.z = (Math.PI / 2) * (1 - (1 - this.fall) ** 3);
      if (this.current) this.current.timeScale = Math.max(0, 1 - this.fall * 2);
      this.t += dt;
      if (this.t > (this.butchered ? 8 : 240)) { this.root.visible = false; }
      if (this.t > W.respawn) this.reset();
      this.place();
      return;
    }
    const dx = player.x - this.pos.x, dz = player.z - this.pos.z, dist = Math.hypot(dx, dz);
    const away = _v.set(-dx, 0, -dz).normalize();
    this.t -= dt;
    if (this.tamed) { this.updateTame(dt, player, dx, dz, dist); this.place(); return; }
    // Taming: walk (don't run) toward it with food it likes in your bag, and it lets you come close.
    this.calm = Math.max(0, this.calm - dt);
    const tolerant = sp.tame && player.alive && ((player.speed < 3.4 && W.hasFood?.(sp)) || this.calm > 0);
    this.flinch = Math.max(0, this.flinch - dt * 4);
    const fromHome = this.pos.distanceTo(this.home);
    const night = W.night?.() ?? false;
    switch (this.state) {
      case 'idle':
      case 'eat':
        if (this.t < 0) {
          const r = Math.random();
          if (r < 0.45) { this.state = 'walk'; this.goal = this.w.spot(this.home, 14); this.t = 6 + Math.random() * 6; this.play('walk'); }
          else { this.state = r < 0.8 && this.clips.eat ? 'eat' : 'idle'; this.t = 3 + Math.random() * 5; this.play(this.state); }
        }
        this.step(dt, UP, 0);
        break;
      case 'walk': {
        const g = _v.set(this.goal.x - this.pos.x, 0, this.goal.z - this.pos.z);
        if (g.length() < 0.8 || this.t < 0) { this.state = 'idle'; this.t = 2 + Math.random() * 3; this.play('idle'); break; }
        this.step(dt, g.normalize(), sp.walk);
        break;
      }
      case 'flee':
        this.step(dt, away, sp.run);
        if (this.t < 0 && dist > sp.scare * 1.6) { this.state = 'walk'; this.goal = this.w.spot(this.home, 14); this.t = 6; this.play('walk'); }
        break;
      case 'chase': {
        const to = _v.set(dx, 0, dz).normalize();
        if (dist < this.reach) {
          this.state = 'bite'; this.t = 0.55; this.bit = false; this.play(this.clips.attack ? 'attack' : 'idle', 0.1);
          break;
        }
        this.step(dt, to, sp.run);
        if (fromHome > (sp.leash ?? 40) || this.hp < sp.hp * 0.25 || (sp.kind === 'territorial' && this.t < 0)) { this.state = 'flee'; this.t = 4; this.play('run'); }
        break;
      }
      case 'bite': {
        // Lunge: a quick forward pitch; the damage lands at the peak.
        const u = 1 - this.t / 0.55;
        this.body.rotation.x = Math.sin(Math.min(1, u) * Math.PI) * -0.25;
        if (!this.bit && u > 0.45) { this.bit = true; if (dist < this.reach + 0.7) W.onBite?.(this, sp.damage ?? 10); }
        if (this.t < 0) {
          this.body.rotation.x = 0;
          if (sp.kind === 'territorial') { this.state = 'flee'; this.t = 3; this.play('run'); }
          else { this.state = 'chase'; this.t = 1.0; this.play('run'); }
        }
        break;
      }
    }
    // Senses.
    if (this.state !== 'flee' && this.state !== 'chase' && this.state !== 'bite' && player.alive) {
      const scare = tolerant ? 1.0 : sp.scare;
      if (sp.kind === 'prey' && (dist < scare || (!tolerant && W.panicNear(this)))) { this.state = 'flee'; this.t = 3 + Math.random() * 2; this.play('run'); }
      if (sp.kind === 'territorial' && !tolerant && dist < (sp.charge ?? 6) && !W.feared?.(this.pos.x, this.pos.z)) { this.state = 'chase'; this.t = 4; this.play('run'); }
      else if (sp.kind === 'territorial' && dist < scare) { this.state = 'flee'; this.t = 3; this.play('run'); }
      // A calm animal turns to look at you instead of wandering off.
      if (tolerant && dist < 8 && this.state === 'walk') { this.state = 'idle'; this.t = 3; this.play('idle'); }
      if (sp.kind === 'hostile' && dist < (night ? sp.sense * 1.6 : sp.sense) && fromHome < (sp.leash ?? 40)) { this.state = 'chase'; this.play('run'); }
    }
    if (!player.alive && (this.state === 'chase' || this.state === 'bite')) { this.state = 'walk'; this.goal = this.home; this.t = 8; this.play('walk'); }
    if ((this.state === 'walk' || this.state === 'flee' || this.state === 'chase') && this.speed > 0.1 && this.current?.getClip() !== (this.state === 'walk' ? this.clips.walk : this.clips.run)) this.play(this.state === 'walk' ? 'walk' : 'run');
    this.place();
  }

  // A tame animal follows you a few metres behind, or stays where you told it to.
  updateTame(dt, player, dx, dz, dist) {
    const sp = this.sp;
    if (this.mode === 'follow' && player.alive) {
      if (dist > 70) { const p = this.w.spot(new THREE.Vector3(player.x, 0, player.z), 4); this.pos.copy(p); }
      if (dist > 4.5) {
        const fast = dist > 9;
        this.step(dt, _v.set(dx, 0, dz).normalize(), fast ? sp.run * 0.8 : sp.walk * 1.4);
        this.play(fast ? 'run' : 'walk');
        this.state = 'follow';
        return;
      }
    }
    this.step(dt, UP, 0);
    if (this.state === 'follow' || this.t < 0) {
      this.state = Math.random() < 0.5 && this.clips.eat ? 'eat' : 'idle';
      this.t = 3 + Math.random() * 4;
      this.play(this.state);
    }
    // Face you when you're close.
    if (dist < 5) { let d = Math.atan2(dx, dz) - this.yaw; d = Math.atan2(Math.sin(d), Math.cos(d)); this.yaw += d * Math.min(1, dt * 2); }
  }

  // One feeding. Returns 'tamed' when this was the last one.
  feed() {
    this.trust += 1;
    this.calm = 40;
    this.state = 'eat';
    this.t = 2.5;
    this.play('eat');
    if (this.trust >= this.sp.tame.feeds) {
      this.tamed = true;
      this.mode = 'follow';
      this.name = NAMES[(this.id * 7 + Math.floor(Math.random() * 5)) % NAMES.length];
      this.storage = {};
      this.hp = this.sp.hp;
      return 'tamed';
    }
    return 'fed';
  }

  place() {
    const h = this.w.island.heightAt(this.pos.x, this.pos.z);
    this.pos.y = h;
    this.root.position.copy(this.pos);
    this.root.rotation.y = this.yaw;
    // A hit makes it jolt sideways.
    this.body.position.x = Math.sin(this.flinch * 20) * 0.06 * this.flinch;
  }

  hurt(n, from) {
    if (this.dead || this.tamed) return false;
    this.trust = 0;
    this.calm = 0;
    this.hp -= n;
    this.flinch = 1;
    if (this.hp <= 0) {
      this.dead = true;
      this.t = 0;
      this.state = 'dead';
      this.play('idle', 0.1);
      return true;
    }
    const sp = this.sp;
    if (sp.kind === 'prey') { this.state = 'flee'; this.t = 5; this.play('run'); }
    else if (sp.kind === 'territorial' || sp.kind === 'hostile') { this.state = 'chase'; this.t = 5; this.play('run'); }
    return false;
  }
}

export class Creatures {
  constructor({ scene, assets, island, flora, building }) {
    Object.assign(this, { assets, island, flora, building });
    this.root = new THREE.Group();
    this.root.name = 'creatures';
    scene.add(this.root);
    this.list = [];
    this.scales = new Map();
    this.respawn = 600;
    this.blood = null;
  }

  // Scale so the model stands `height` metres tall.
  scaleFor(sp) {
    if (!this.scales.has(sp.model)) {
      const o = cloneSkinned(this.assets[sp.model].scene);
      o.updateMatrixWorld(true);
      const box = new THREE.Box3().setFromObject(o, true);
      this.scales.set(sp.model, sp.height / Math.max(0.01, box.max.y - box.min.y));
    }
    return this.scales.get(sp.model);
  }

  blocked(x, z, r) {
    return this.flora.blocked(x, z, r) || this.building.blockedAt(x, z, r, this.island.heightAt(x, z));
  }

  // A herd-mate within 16 m is bolting.
  panicNear(c) {
    return this.list.some((o) => o !== c && !o.dead && o.state === 'flee' && o.sp.kind === 'prey' && o.pos.distanceTo(c.pos) < 16);
  }

  // The player can't walk through a living animal.
  blocksPlayer(x, z, r) {
    for (const c of this.list) if (!c.dead && Math.hypot(c.pos.x - x, c.pos.z - z) < r + c.sp.height * 0.32) return true;
    return false;
  }

  // A free spot on land within r of c.
  spot(c, r) {
    for (let i = 0; i < 20; i++) {
      const a = Math.random() * Math.PI * 2, d = Math.sqrt(Math.random()) * r;
      const x = c.x + Math.cos(a) * d, z = c.z + Math.sin(a) * d;
      if (this.island.heightAt(x, z) > 0.4 && this.island.slopeAt(x, z) < 0.6 && !this.blocked(x, z, 0.5)) return new THREE.Vector3(x, this.island.heightAt(x, z), z);
    }
    return c.clone();
  }

  add(kind, home, n = 1) {
    for (let i = 0; i < n; i++) this.list.push(new Creature(this, SPECIES[kind], this.list.length, home));
  }

  update(dt, player) {
    this.player = player;
    for (const c of this.list) {
      const d = Math.hypot(c.pos.x - player.x, c.pos.z - player.z);
      c.root.visible = c.root.visible && d < 140;
      if (d > 160 && !c.dead) continue; // far away: frozen
      c.update(dt, player);
      if (d < 140 && !(c.dead && c.t > (c.butchered ? 8 : 240))) c.root.visible = true;
    }
  }

  // Animals caught by a swing from p facing f (a flat unit vector) within reach and the arc.
  inArc(p, f, reach, cosMin) {
    return this.list.filter((c) => {
      if (c.dead || c.tamed) return false;
      const dx = c.pos.x - p.x, dz = c.pos.z - p.z, d = Math.hypot(dx, dz);
      const r = c.sp.height * 0.45;
      if (d - r > reach) return false;
      return d < r + 0.3 || (dx * f.x + dz * f.y) / d > cosMin;
    });
  }

  // A carcass in front of you to butcher.
  carcassNear(p, f, reach = 2.4) {
    let best = null, bd = Infinity;
    for (const c of this.list) {
      if (!c.dead || c.butchered || c.fall < 1) continue;
      const dx = c.pos.x - p.x, dz = c.pos.z - p.z, d = Math.hypot(dx, dz);
      if (d > reach + c.sp.height * 0.4) continue;
      const cos = (dx * f.x + dz * f.y) / Math.max(0.01, d);
      if (cos < 0.6 && d > 1) continue;
      if (d < bd) { bd = d; best = c; }
    }
    return best;
  }

  // A living animal right in front of you: a tame one, or a wild one you could feed.
  animalNear(p, f, reach = 2.8) {
    let best = null, bd = Infinity;
    for (const c of this.list) {
      if (c.dead || (!c.tamed && !c.sp.tame)) continue;
      const dx = c.pos.x - p.x, dz = c.pos.z - p.z, d = Math.hypot(dx, dz);
      if (d > reach + c.sp.height * 0.4) continue;
      const cos = (dx * f.x + dz * f.y) / Math.max(0.01, d);
      if (cos < 0.7 && d > 1.2) continue;
      if (d < bd) { bd = d; best = c; }
    }
    return best;
  }

  get tamed() { return this.list.filter((c) => c.tamed && !c.dead); }

  butcher(c) {
    c.butchered = true;
    c.t = 0;
    return { ...c.sp.loot };
  }

  serialize() { return this.list.map((c) => (c.dead ? [c.id, Math.round(c.t), c.butchered ? 1 : 0] : null)).filter(Boolean); }

  serializeTame() {
    return this.list.filter((c) => c.tamed || c.trust > 0).map((c) => ({ id: c.id, trust: c.trust, tamed: c.tamed ? 1 : 0, name: c.name, mode: c.mode, x: +c.pos.x.toFixed(2), z: +c.pos.z.toFixed(2), s: c.storage }));
  }

  restore(list, tame) {
    for (const [id, t, b] of list ?? []) {
      const c = this.list[id];
      if (!c) continue;
      c.dead = true; c.t = t; c.butchered = !!b; c.fall = 1; c.state = 'dead';
    }
    for (const o of tame ?? []) {
      const c = this.list[o.id];
      if (!c || c.dead) continue;
      c.trust = o.trust ?? 0;
      if (o.tamed) Object.assign(c, { tamed: true, name: o.name, mode: o.mode ?? 'follow', storage: o.s ?? {} });
      if (o.x !== undefined && o.tamed) { c.pos.set(o.x, this.island.heightAt(o.x, o.z), o.z); c.place(); }
    }
  }
}
