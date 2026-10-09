// The castaway: KayKit barbarian with walk/run/chop animations, collision against the island.
import * as THREE from 'three';
import { damp, angleDelta } from './util.js';

const HIDE = ['1H_Axe_Offhand', 'Barbarian_Round_Shield', '2H_Axe', 'Mug'];
const HEIGHT = 2.0; // meters
const RADIUS = 0.45;
const WALK = 3.0, RUN = 6.0;

export class Player {
  constructor(scene, gltf, world) {
    this.world = world;
    this.root = gltf.scene;
    this.root.name = 'player';
    this.root.traverse((o) => {
      if (HIDE.includes(o.name)) o.visible = false;
      if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; }
    });
    const box = new THREE.Box3().setFromObject(this.root);
    const h = box.max.y - box.min.y;
    this.root.scale.setScalar(HEIGHT / h);
    scene.add(this.root);

    this.mixer = new THREE.AnimationMixer(this.root);
    this.actions = {};
    for (const clip of gltf.animations) this.actions[clip.name] = this.mixer.clipAction(clip);
    for (const n of ['1H_Melee_Attack_Chop', 'PickUp', 'Cheer']) {
      const a = this.actions[n];
      if (a) { a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; }
    }
    this.current = null;
    this.play('Idle', 0);

    this.pos = new THREE.Vector3(world.spawn.x, world.spawn.y, world.spawn.z);
    this.vel = new THREE.Vector2();
    this.facing = world.spawn.facing;
    this.state = 'free';
    this.swingT = 0;
    this.swingHitDone = false;
    this.root.position.copy(this.pos);
    this.root.rotation.y = this.facing;
  }

  play(name, fade = 0.18, timeScale = 1) {
    const next = this.actions[name];
    if (!next) return;
    next.timeScale = timeScale;
    if (this.current === next) return;
    next.reset().setEffectiveWeight(1).play();
    if (this.current) next.crossFadeFrom(this.current, fade, false);
    this.current = next;
  }

  get busy() {
    return this.state !== 'free';
  }

  // Swing at a gather target. onHit fires at the impact frame; onDone when the swing ends.
  swing(target, onHit, onDone) {
    if (this.busy) return false;
    this.state = 'swing';
    this.swingTarget = target;
    this.onHit = onHit;
    this.onDone = onDone;
    this.swingT = 0;
    this.swingHitDone = false;
    const clip = this.actions['1H_Melee_Attack_Chop'];
    this.swingDur = clip.getClip().duration / 1.35;
    if (this.current === clip) clip.reset().play();
    else this.play('1H_Melee_Attack_Chop', 0.1, 1.35);
    this.vel.set(0, 0);
    return true;
  }

  cheer() {
    if (this.busy) return;
    this.state = 'cheer';
    if (this.current === this.actions.Cheer) this.actions.Cheer.reset().play();
    else this.play('Cheer', 0.15, 1.2);
    this.cheerT = this.actions.Cheer.getClip().duration / 1.2;
  }

  update(dt, move) {
    const world = this.world;
    if (this.state === 'swing') {
      this.swingT += dt;
      const t = this.swingTarget;
      const want = Math.atan2(t.x - this.pos.x, t.z - this.pos.z);
      this.facing += angleDelta(this.facing, want) * Math.min(1, dt * 14);
      if (!this.swingHitDone && this.swingT >= this.swingDur * 0.42) {
        this.swingHitDone = true;
        this.onHit?.();
      }
      if (this.swingT >= this.swingDur) {
        this.state = 'free';
        this.onDone?.();
      }
    } else if (this.state === 'cheer') {
      this.cheerT -= dt;
      if (this.cheerT <= 0 || move.mag > 0.2) {
        this.state = 'free';
      }
    }

    if (this.state === 'free') {
      const speed = move.mag < 0.65 ? WALK * Math.min(1, move.mag / 0.65) : RUN;
      const tx = move.x * (move.mag > 0 ? speed / move.mag : 0);
      const tz = move.z * (move.mag > 0 ? speed / move.mag : 0);
      this.vel.x = damp(this.vel.x, tx, 12, dt);
      this.vel.y = damp(this.vel.y, tz, 12, dt);
      const sp = this.vel.length();

      if (sp > 0.05) {
        this.moveBy(this.vel.x * dt, this.vel.y * dt);
        const want = Math.atan2(this.vel.x, this.vel.y);
        this.facing += angleDelta(this.facing, want) * Math.min(1, dt * 12);
      }
      if (sp > RUN * 0.72) this.play('Running_A', 0.2, sp / RUN);
      else if (sp > 0.35) this.play('Walking_A', 0.2, Math.max(0.6, sp / WALK) * 1.05);
      else this.play('Idle', 0.25);
    }

    const ground = world.heightAt(this.pos.x, this.pos.z);
    this.pos.y = damp(this.pos.y, ground, 18, dt);
    this.root.position.copy(this.pos);
    this.root.rotation.y = this.facing;
    this.mixer.update(dt);
  }

  moveBy(dx, dz) {
    const w = this.world;
    const ok = (x, z) => w.isWalkable(x, z) && w.isFree(x, z, RADIUS);
    let { x, z } = this.pos;
    if (ok(x + dx, z + dz)) { x += dx; z += dz; }
    else if (ok(x + dx, z)) { x += dx; }
    else if (ok(x, z + dz)) { z += dz; }
    // Gently push out of anything we ended up overlapping (e.g. a tree that regrew).
    for (const c of w.colliders) {
      const ddx = x - c.x, ddz = z - c.z, rr = RADIUS + c.r;
      const d2 = ddx * ddx + ddz * ddz;
      if (d2 < rr * rr && d2 > 1e-6) {
        const d = Math.sqrt(d2), push = (rr - d) * 0.5;
        const nx = x + (ddx / d) * push, nz = z + (ddz / d) * push;
        if (w.isWalkable(nx, nz)) { x = nx; z = nz; }
      }
    }
    this.pos.x = x;
    this.pos.z = z;
  }

  serialize() {
    return { x: +this.pos.x.toFixed(2), z: +this.pos.z.toFixed(2), f: +this.facing.toFixed(2) };
  }

  restore(s) {
    if (!s || !this.world.isWalkable(s.x, s.z) || !this.world.isFree(s.x, s.z, RADIUS)) return;
    this.pos.set(s.x, this.world.heightAt(s.x, s.z), s.z);
    this.facing = s.f ?? this.facing;
  }
}
