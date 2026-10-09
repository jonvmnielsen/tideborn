// The castaway: KayKit barbarian. Walks on terrain and floors, collides with the world,
// and plays an action animation for gathering, eating, sleeping.
import * as THREE from 'three';
import { damp, angleDelta } from './util.js';

const ALWAYS_HIDDEN = ['1H_Axe_Offhand', 'Barbarian_Round_Shield', '2H_Axe', 'Mug'];
const HEIGHT = 1.9;
export const RADIUS = 0.42;
const WALK = 3.2, RUN = 6.2;

const ACTIONS = {
  chop:     { clip: '1H_Melee_Attack_Chop', speed: 1.35, impact: 0.42 },
  pickup:   { clip: 'PickUp',               speed: 1.4,  impact: 0.5 },
  interact: { clip: 'Interact',             speed: 1.2,  impact: 0.5 },
  eat:      { clip: 'Use_Item',             speed: 1.2,  impact: 0.6 },
  build:    { clip: 'Interact',             speed: 1.5,  impact: 0.4 },
};

export class Player {
  constructor(scene, gltf, world) {
    this.world = world;
    this.root = gltf.scene;
    this.root.name = 'player';
    this.axeMesh = null;
    this.root.traverse((o) => {
      if (ALWAYS_HIDDEN.includes(o.name)) o.visible = false;
      if (o.name === '1H_Axe') this.axeMesh = o;
      if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; }
    });
    const box = new THREE.Box3().setFromObject(this.root);
    this.root.scale.setScalar(HEIGHT / (box.max.y - box.min.y));
    scene.add(this.root);

    this.mixer = new THREE.AnimationMixer(this.root);
    this.actions = {};
    for (const clip of gltf.animations) this.actions[clip.name] = this.mixer.clipAction(clip);
    for (const n of ['1H_Melee_Attack_Chop', 'PickUp', 'Interact', 'Use_Item', 'Cheer', 'Death_A', 'Jump_Full_Short']) {
      const a = this.actions[n];
      if (a) { a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; }
    }
    this.current = null;
    this.play('Idle', 0);

    const s = world.spawn;
    this.pos = new THREE.Vector3(s.x, s.y, s.z);
    this.vel = new THREE.Vector2();
    this.facing = s.facing;
    this.state = 'free'; // free | action | dead | sleep | sit
    this.action = null;
    this.vy = 0;
    this.setTool(false);
  }

  setTool(visible) {
    if (this.axeMesh) this.axeMesh.visible = visible;
  }

  play(name, fade = 0.18, timeScale = 1, restart = false) {
    const next = this.actions[name];
    if (!next) return;
    next.timeScale = timeScale;
    if (this.current === next) {
      if (restart) next.reset().play();
      return;
    }
    next.reset().setEffectiveWeight(1).play();
    if (this.current) next.crossFadeFrom(this.current, fade, false);
    this.current = next;
  }

  get busy() {
    return this.state !== 'free';
  }

  // Start an action toward a world point. onImpact fires mid-animation, onDone at the end.
  perform(kind, at, onImpact, onDone) {
    if (this.state !== 'free') return false;
    const a = ACTIONS[kind];
    const clip = this.actions[a.clip];
    this.state = 'action';
    this.action = { kind, at, onImpact, onDone, t: 0, dur: clip.getClip().duration / a.speed, impactAt: a.impact, hit: false };
    this.play(a.clip, 0.1, a.speed, true);
    this.vel.set(0, 0);
    return true;
  }

  cheer() {
    if (this.state !== 'free') return;
    this.state = 'action';
    const c = this.actions.Cheer;
    this.action = { kind: 'cheer', t: 0, dur: c.getClip().duration / 1.2, impactAt: 2, hit: true };
    this.play('Cheer', 0.15, 1.2, true);
  }

  die() {
    this.state = 'dead';
    this.action = null;
    this.play('Death_A', 0.15, 1, true);
  }

  sleep(on) {
    if (on) {
      this.state = 'sleep';
      this.play('Lie_Idle', 0.4);
    } else if (this.state === 'sleep') {
      this.state = 'free';
    }
  }

  revive(x, z, facing) {
    this.pos.set(x, this.world.groundAt(x, z), z);
    this.facing = facing ?? this.facing;
    this.state = 'free';
    this.vel.set(0, 0);
    this.play('Idle', 0.1);
  }

  update(dt, moveX, moveZ, mag) {
    const w = this.world;
    if (this.state === 'action') {
      const a = this.action;
      a.t += dt;
      if (a.at) {
        const want = Math.atan2(a.at.x - this.pos.x, a.at.z - this.pos.z);
        this.facing += angleDelta(this.facing, want) * Math.min(1, dt * 14);
      }
      if (!a.hit && a.t >= a.dur * a.impactAt) {
        a.hit = true;
        a.onImpact?.();
      }
      if (a.t >= a.dur || (a.kind === 'cheer' && mag > 0.2)) {
        this.state = 'free';
        this.action = null;
        a.onDone?.();
      }
    }

    if (this.state === 'free') {
      const speed = mag < 0.6 ? WALK * Math.min(1, mag / 0.6) : RUN;
      const tx = mag > 0 ? (moveX / mag) * speed : 0;
      const tz = mag > 0 ? (moveZ / mag) * speed : 0;
      this.vel.x = damp(this.vel.x, tx, 12, dt);
      this.vel.y = damp(this.vel.y, tz, 12, dt);
      const sp = this.vel.length();
      if (sp > 0.05) {
        this.moveBy(this.vel.x * dt, this.vel.y * dt);
        this.facing += angleDelta(this.facing, Math.atan2(this.vel.x, this.vel.y)) * Math.min(1, dt * 12);
      }
      if (sp > RUN * 0.72) this.play('Running_A', 0.2, sp / RUN);
      else if (sp > 0.35) this.play('Walking_A', 0.2, Math.max(0.6, sp / WALK) * 1.05);
      else this.play('Idle', 0.25);
    }

    // Ground: terrain, or a floor/stair we can step onto.
    const ground = w.groundAt(this.pos.x, this.pos.z, this.pos.y);
    if (ground > this.pos.y) this.pos.y = damp(this.pos.y, ground, 20, dt);
    else {
      this.vy -= 22 * dt;
      this.pos.y = Math.max(ground, this.pos.y + this.vy * dt);
    }
    if (this.pos.y <= ground + 0.001) this.vy = 0;
    this.root.position.copy(this.pos);
    this.root.rotation.y = this.facing;
    this.mixer.update(dt);
  }

  moveBy(dx, dz) {
    const w = this.world;
    const y = this.pos.y;
    const ok = (x, z) => w.walkable(x, z, y) && !w.colliders.blocked(x, z, RADIUS, y) && w.groundAt(x, z, y) <= y + 1.1;
    let { x, z } = this.pos;
    if (ok(x + dx, z + dz)) { x += dx; z += dz; }
    else if (ok(x + dx, z)) { x += dx; }
    else if (ok(x, z + dz)) { z += dz; }
    const r = w.colliders.resolve(x, z, RADIUS, y);
    if (w.walkable(r.x, r.z, y)) { x = r.x; z = r.z; }
    this.pos.x = x;
    this.pos.z = z;
  }

  serialize() {
    return { x: +this.pos.x.toFixed(2), y: +this.pos.y.toFixed(2), z: +this.pos.z.toFixed(2), f: +this.facing.toFixed(2) };
  }

  restore(s) {
    if (!s) return;
    this.pos.set(s.x, Math.max(this.world.groundAt(s.x, s.z, (s.y ?? 0) + 0.1), s.y ?? -Infinity), s.z);
    this.facing = s.f ?? this.facing;
  }
}
