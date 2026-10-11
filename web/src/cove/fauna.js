// Animal life for the cove (D-013): macaws and parrots flying over the jungle, gulls circling the
// lagoon, butterflies around the player, crabs scuttling at the waterline and schools of reef fish
// in the shallows. Each species is one instanced mesh per model part; wings flap and fish tails
// beat in the vertex shader (per-instance phase from gl_InstanceID), paths are moved on the CPU.
import * as THREE from 'three';
import { meshParts } from '../assets.js';
import { prepareModel } from './facets.js';

const time = { value: 0 };
const UP = new THREE.Vector3(0, 1, 0);

// Wings rotate up and down about the body's long axis; `glide` lets gulls hold their wings
// still for stretches. Fish bend toward the tail instead.
function animate(material, kind, { freq = 10, amp = 0.7, glide = 0, pivot = 0.05 } = {}) {
  const key = `fauna-${kind}-${freq}-${amp}-${glide}-${pivot}`;
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uTime = time;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nuniform float uTime;')
      .replace('#include <begin_vertex>', `#include <begin_vertex>
{
  float ph = float(gl_InstanceID) * 2.399;
  ${kind === 'fish' ? `
  float tail = smoothstep(0.05, -0.2, position.z);
  transformed.x += sin(uTime * ${freq.toFixed(2)} + ph + position.z * 14.0) * ${amp.toFixed(3)} * tail;` : `
  float flap = sin(uTime * ${freq.toFixed(2)} + ph);
  ${glide > 0 ? `flap *= smoothstep(-0.2, 0.4, sin(uTime * 0.45 + ph * 0.7)) * 0.85 + 0.15;` : ''}
  float a = flap * ${amp.toFixed(3)};
  float ax = abs(position.x), k = max(ax - ${pivot.toFixed(3)}, 0.0);
  transformed.x = sign(position.x) * (min(ax, ${pivot.toFixed(3)}) + k * cos(a));
  transformed.y += k * sin(a);`}
}`);
  };
  material.customProgramCacheKey = () => key;
}

class Flock {
  constructor(parent, assets, key, count, anim) {
    const scene = assets[key].scene;
    prepareModel(scene);
    this.parts = meshParts(scene).map((p) => {
      const material = p.material.clone();
      // Birds and butterflies flap only the wing mesh; fish bend the whole body.
      if (anim && (anim.kind === 'fish' || material.name === 'lowpoly_wing')) animate(material, anim.kind, anim);
      const im = new THREE.InstancedMesh(p.geometry, material, count);
      im.castShadow = false;
      im.frustumCulled = false;
      im.name = `fauna:${key}`;
      parent.add(im);
      return { im, local: p.matrix };
    });
    this.count = count;
    this.m = new THREE.Matrix4();
    this.m2 = new THREE.Matrix4();
    this.q = new THREE.Quaternion();
    this.s = new THREE.Vector3(1, 1, 1);
  }

  // Place instance i at p, facing along velocity v (+z forward), banked by `bank` radians.
  set(i, p, v, bank = 0, scale = 1) {
    const look = this.m.lookAt(p, this.s.copy(p).sub(v), UP);
    this.q.setFromRotationMatrix(look);
    if (bank) this.q.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), bank));
    this.m.compose(p, this.q, this.s.setScalar(scale));
    for (const part of this.parts) part.im.setMatrixAt(i, this.m2.multiplyMatrices(this.m, part.local));
  }

  done() { for (const part of this.parts) part.im.instanceMatrix.needsUpdate = true; }
}

export class Fauna {
  constructor(parent, assets, island, { mobile = false } = {}) {
    this.island = island;
    this.mobile = mobile;
    const I = island;
    const rnd = (() => { let s = 99; return () => ((s = (Math.imul(s, 1664525) + 1013904223) >>> 0) / 4294967296); })();
    this.rnd = rnd;
    // Gulls circling over the lagoon.
    this.gulls = new Flock(parent, assets, 'fauna/gull', 9, { kind: 'bird', freq: 7, amp: 0.55, glide: 1 });
    this.gullPaths = Array.from({ length: 9 }, () => ({ cx: -120 + rnd() * 240, cz: 70 + rnd() * 90, r: 18 + rnd() * 40, h: 10 + rnd() * 22, w: (0.12 + rnd() * 0.1) * (rnd() < 0.5 ? -1 : 1), ph: rnd() * 6.28 }));
    // Macaws and parrots: small flocks crossing over the jungle canopy on long loops.
    this.macaws = new Flock(parent, assets, 'fauna/macaw', 10, { kind: 'bird', freq: 11, amp: 0.75 });
    this.parrots = new Flock(parent, assets, 'fauna/parrot_blue', 8, { kind: 'bird', freq: 12, amp: 0.75 });
    this.parrotFlocks = [
      { cx: -60, cz: -60, rx: 110, rz: 60, h: 24, w: 0.07, ph: 0 },
      { cx: 60, cz: -40, rx: 90, rz: 80, h: 21, w: -0.08, ph: 2 },
      { cx: -20, cz: 0, rx: 70, rz: 50, h: 18, w: 0.1, ph: 4 },
    ];
    this.parrotOffsets = Array.from({ length: 18 }, () => new THREE.Vector3((rnd() - 0.5) * 8, (rnd() - 0.5) * 3, (rnd() - 0.5) * 8));
    // Butterflies stay around the player.
    const nb = mobile ? 10 : 22;
    this.butterflies = [new Flock(parent, assets, 'fauna/butterfly_blue', Math.ceil(nb / 2), { kind: 'bird', freq: 26, amp: 1.0, pivot: 0.004 }), new Flock(parent, assets, 'fauna/butterfly_orange', Math.floor(nb / 2), { kind: 'bird', freq: 30, amp: 1.0, pivot: 0.004 })];
    this.flutters = Array.from({ length: nb }, () => ({ home: null, ph: rnd() * 100, sp: 0.6 + rnd() * 0.6 }));
    // Crabs on the wet sand.
    const nc = mobile ? 10 : 16;
    this.crabs = new Flock(parent, assets, 'fauna/crab', nc, null);
    this.crabState = Array.from({ length: nc }, () => {
      const x = -125 + rnd() * 250;
      return { x, z: I.shoreZ(x) - 1 - rnd() * 6, dir: rnd() * 6.28, go: 0, wait: rnd() * 3 };
    });
    // Reef fish schools in the shallows.
    const kinds = ['fauna/fish_yellow', 'fauna/fish_blue', 'fauna/fish_clown'];
    const per = mobile ? 7 : 12;
    this.schools = kinds.map((k, si) => {
      const flock = new Flock(parent, assets, k, per * 2, { kind: 'fish', freq: 9, amp: 0.025 });
      const centres = [0, 1].map((j) => {
        const x = -100 + rnd() * 200;
        return { cx: x, cz: I.shoreZ(x) + 14 + rnd() * 26, r: 4 + rnd() * 6, w: (0.25 + rnd() * 0.2) * (rnd() < 0.5 ? -1 : 1), ph: rnd() * 6.28 };
      });
      const offs = Array.from({ length: per * 2 }, () => new THREE.Vector3((rnd() - 0.5) * 3, -rnd() * 0.5, (rnd() - 0.5) * 3));
      return { flock, centres, offs, per, si };
    });
    this.p = new THREE.Vector3();
    this.v = new THREE.Vector3();
  }

  update(t, dt, cam) {
    time.value = t;
    const I = this.island, p = this.p, v = this.v;
    // Gulls.
    this.gullPaths.forEach((g, i) => {
      const a = g.ph + t * g.w * 2.2;
      p.set(g.cx + Math.cos(a) * g.r, g.h + Math.sin(t * 0.3 + g.ph) * 2, g.cz + Math.sin(a) * g.r);
      v.set(-Math.sin(a) * Math.sign(g.w), 0, Math.cos(a) * Math.sign(g.w));
      this.gulls.set(i, p, v, -0.35 * Math.sign(g.w), 1.1);
    });
    this.gulls.done();
    // Parrot flocks: each bird follows its flock's loop with an offset.
    let mi = 0, pi = 0;
    for (let i = 0; i < 18; i++) {
      const f = this.parrotFlocks[i % 3], o = this.parrotOffsets[i];
      const a = f.ph + t * f.w + o.x * 0.004;
      p.set(f.cx + Math.cos(a) * f.rx + o.x, f.h + o.y + Math.sin(t * 0.8 + i) * 0.6, f.cz + Math.sin(a) * f.rz + o.z);
      v.set(-Math.sin(a) * f.rx * Math.sign(f.w), 0, Math.cos(a) * f.rz * Math.sign(f.w)).normalize();
      const bank = -0.25 * Math.sign(f.w);
      if (i % 9 < 5) this.macaws.set(mi++, p, v, bank);
      else this.parrots.set(pi++, p, v, bank);
    }
    this.macaws.done(); this.parrots.done();
    // Butterflies: drift around a home spot near the player; move home when left behind.
    this.flutters.forEach((b, i) => {
      if (!b.home || b.home.distanceTo(cam) > 22) {
        const a = this.rnd() * 6.28, d = 4 + this.rnd() * 12;
        const x = cam.x + Math.cos(a) * d, z = cam.z + Math.sin(a) * d;
        b.home = new THREE.Vector3(x, Math.max(0.2, I.heightAt(x, z)) + 0.6 + this.rnd() * 1.4, z);
      }
      const s = t * b.sp + b.ph;
      p.set(b.home.x + Math.sin(s * 0.9) * 2.2 + Math.sin(s * 2.3) * 0.5, b.home.y + Math.sin(s * 1.7) * 0.4, b.home.z + Math.cos(s * 0.7) * 2.2 + Math.cos(s * 2.9) * 0.5);
      v.set(Math.cos(s * 0.9) * 2 + Math.cos(s * 2.3) * 1.1, 0, -Math.sin(s * 0.7) * 1.5 - Math.sin(s * 2.9) * 1.4);
      const fl = this.butterflies[i % 2];
      fl.set(Math.floor(i / 2), p, v, Math.sin(s * 3) * 0.3, 1.3);
    });
    for (const f of this.butterflies) f.done();
    // Crabs: short sideways dashes, then a pause.
    this.crabState.forEach((c, i) => {
      if (c.wait > 0) { c.wait -= dt; if (c.wait <= 0) { c.go = 0.6 + this.rnd() * 1.5; c.dir += (this.rnd() - 0.5) * 2; } }
      else {
        c.go -= dt;
        const sx = Math.cos(c.dir), sz = Math.sin(c.dir);
        const nx = c.x + sx * dt * 1.4, nz = c.z + sz * dt * 1.4;
        const d = I.inland(nx, nz);
        if (d > 0.5 && d < 12) { c.x = nx; c.z = nz; } else c.dir += Math.PI;
        if (c.go <= 0) c.wait = 1 + this.rnd() * 4;
      }
      // Crabs walk sideways: face 90° off the direction of travel.
      p.set(c.x, I.heightAt(c.x, c.z) + (c.wait > 0 ? 0 : Math.abs(Math.sin(t * 18 + i)) * 0.015), c.z);
      v.set(-Math.sin(c.dir), 0, Math.cos(c.dir));
      this.crabs.set(i, p, v, 0, 1.2);
    });
    this.crabs.done();
    // Fish: two shoals per kind circling over the sand.
    for (const sc of this.schools) {
      sc.offs.forEach((o, i) => {
        const c = sc.centres[i < sc.per ? 0 : 1];
        const a = c.ph + t * c.w + o.x * 0.05;
        const x = c.cx + Math.cos(a) * c.r + o.x, z = c.cz + Math.sin(a) * c.r + o.z;
        const depth = -I.heightAt(x, z);
        p.set(x, -Math.min(Math.max(depth * 0.55, 0.25), 2.5) + o.y * 0.3, z);
        v.set(-Math.sin(a) * Math.sign(c.w), 0, Math.cos(a) * Math.sign(c.w));
        sc.flock.set(i, p, v, 0, 1.2);
      });
      sc.flock.done();
    }
  }
}
