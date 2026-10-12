// First-person arms: the player's own arms (Quaternius Modular Character Outfits, peasant
// sleeves, same 65-bone rig as the Universal Animation Library) holding the machete. Only the
// arms mesh is drawn. Poses are keyframed in camera space — where the machete is and which way
// its blade and edge point — and the arms follow by two-bone IK, with the fingers closed around
// the grip. Animations: idle (breathing, walk bob), swing (wind-up, cut, recover; `onHit` fires
// at the moment of the cut) and pickup (the left hand reaches down and forward).
import * as THREE from 'three';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const GRIP = V(-0.004, 0.075, 0); // handle centre in the machete model

// A pose: grip point, blade direction (machete +y) and edge direction, all in camera space.
function pose(grip, up, edge, left = null) {
  const Y = up.clone().normalize();
  const X = edge.clone().negate().addScaledVector(Y, edge.dot(Y)).normalize(); // machete +x = spine side
  const Z = V(0, 0, 0).crossVectors(X, Y);
  const q = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, Z));
  return { grip, q, left };
}

const IDLE = pose(V(0.2, -0.25, -0.4), V(-0.2, 0.55, -0.8), V(-0.15, -0.8, -0.45));
const LEFT_REST = V(-0.3, -0.8, -0.05);
const SWING = [
  [0, IDLE],
  [0.15, pose(V(0.27, -0.06, -0.36), V(0.35, 0.9, 0.2), V(-0.3, 0.1, -0.95))],
  [0.29, pose(V(-0.08, -0.4, -0.5), V(-0.75, -0.25, -0.6), V(-0.45, -0.75, 0.1))],
  [0.58, IDLE],
];
const PICKUP = [
  [0, { ...IDLE, left: LEFT_REST }],
  [0.26, { ...pose(V(0.24, -0.36, -0.36), V(-0.1, 0.5, -0.85), V(-0.1, -0.85, -0.45)), left: V(-0.06, -0.19, -0.5) }],
  [0.62, { ...IDLE, left: LEFT_REST }],
];
const ease = (t) => t * t * (3 - 2 * t);

export class Hands {
  constructor(camera, assets, { machete }) {
    this.camera = camera;
    this.rig = cloneSkinned(assets['char/peasant'].scene);
    this.rig.traverse((o) => {
      if (!o.isMesh) return;
      o.visible = /Arms/.test(o.name);
      o.frustumCulled = false;
      o.castShadow = false;
      o.receiveShadow = true;
    });
    const bone = (n) => this.rig.getObjectByName(n);
    this.R = { upper: bone('upperarm_r'), lower: bone('lowerarm_r'), hand: bone('hand_r'), side: 'r' };
    this.L = { upper: bone('upperarm_l'), lower: bone('lowerarm_l'), hand: bone('hand_l'), side: 'l' };
    for (const arm of [this.R, this.L]) {
      arm.fingers = ['index', 'middle', 'ring', 'pinky'].map((f) => [1, 2, 3].map((i) => bone(`${f}_0${i}_${arm.side}`)));
      arm.thumb = [1, 2, 3].map((i) => bone(`thumb_0${i}_${arm.side}`));
      arm.lenA = arm.lower.position.length();
      arm.lenB = arm.hand.position.length();
    }
    // Rest rotations, restored every frame before solving (no drift).
    this.rest = new Map();
    this.rig.traverse((o) => { if (o.isBone) this.rest.set(o, o.quaternion.clone()); });

    // Turn the body to face the camera's forward (−z), then move it so the right shoulder sits
    // just below and beside the eye.
    camera.add(this.rig);
    this.rig.updateMatrixWorld(true);
    const inCam = (o) => camera.worldToLocal(o.getWorldPosition(V(0, 0, 0)));
    const right = inCam(this.R.hand).sub(inCam(this.L.hand)).setY(0).normalize();
    const fwd = V(0, 1, 0).cross(right);
    this.rig.quaternion.premultiply(new THREE.Quaternion().setFromUnitVectors(fwd, V(0, 0, -1)));
    this.rig.updateMatrixWorld(true);
    this.rig.position.add(V(0.17, -0.27, 0.02).sub(inCam(this.R.upper)));
    this.rig.updateMatrixWorld(true);

    // Which way the hand's knuckle line runs (index → pinky) in hand-bone space.
    for (const arm of [this.R, this.L]) {
      const hp = arm.hand.getWorldPosition(V(0, 0, 0));
      const inv = arm.hand.getWorldQuaternion(new THREE.Quaternion()).invert();
      const loc = (b) => b.getWorldPosition(V(0, 0, 0)).sub(hp).applyQuaternion(inv);
      arm.sideL = loc(arm.fingers[3][0]).sub(loc(arm.fingers[0][0])).setY(0).normalize();
    }

    this.machete = machete;
    camera.add(machete);
    this.state = { name: 'idle', t: 0 };
    this.onHit = null;
    this.onPick = null;
    this.bob = 0;
    this.moving = 0;
  }

  get busy() { return this.state.name !== 'idle'; }

  swing() { if (!this.busy) { this.state = { name: 'swing', t: 0, hit: false }; return true; } return false; }

  pickup() { if (!this.busy) { this.state = { name: 'pickup', t: 0, hit: false }; return true; } return false; }

  sample(keys, t) {
    let i = 0;
    while (i < keys.length - 2 && t > keys[i + 1][0]) i++;
    const [t0, a] = keys[i], [t1, b] = keys[i + 1];
    const u = ease(THREE.MathUtils.clamp((t - t0) / (t1 - t0), 0, 1));
    return {
      grip: a.grip.clone().lerp(b.grip, u),
      q: a.q.clone().slerp(b.q, u),
      left: a.left && b.left ? a.left.clone().lerp(b.left, u) : LEFT_REST.clone(),
    };
  }

  update(dt, { speed = 0, bob = 0 } = {}) {
    const st = this.state;
    if (!this.freeze) st.t += dt;
    let p;
    if (st.name === 'swing') {
      p = this.sample(SWING, st.t);
      if (!st.hit && st.t > 0.24) { st.hit = true; this.onHit?.(); }
      if (st.t > SWING[SWING.length - 1][0]) this.state = { name: 'idle', t: 0 };
    } else if (st.name === 'pickup') {
      p = this.sample(PICKUP, st.t);
      if (!st.hit && st.t > 0.26) { st.hit = true; this.onPick?.(); }
      if (st.t > PICKUP[PICKUP.length - 1][0]) this.state = { name: 'idle', t: 0 };
    } else {
      p = { grip: IDLE.grip.clone(), q: IDLE.q.clone(), left: LEFT_REST.clone() };
    }
    // Narrow (portrait) screens: bring the hands in toward the middle so they stay in view.
    const sx = THREE.MathUtils.clamp(this.camera.aspect / 1.5, 0.5, 1);
    p.grip.x *= sx;
    p.left.x *= sx;
    // Breathing and walking sway on top of every pose.
    const now = performance.now() / 1000;
    const walk = Math.min(1, speed / 3);
    p.grip.x += Math.cos(bob) * 0.012 * walk;
    p.grip.y += Math.abs(Math.sin(bob)) * 0.018 * walk + Math.sin(now * 1.6) * 0.004;
    p.grip.z += Math.sin(now * 1.1) * 0.003;

    this.machete.position.copy(p.grip).sub(GRIP.clone().applyQuaternion(p.q));
    this.machete.quaternion.copy(p.q);

    for (const [b, q] of this.rest) b.quaternion.copy(q);
    this.rig.updateMatrixWorld(true);
    const cam = this.camera;
    const toWorld = (v) => cam.localToWorld(v.clone());
    const dirWorld = (v) => v.clone().transformDirection(cam.matrixWorld);
    // Right hand around the handle: fingers point toward the edge, knuckles along the handle.
    const up = dirWorld(V(0, 1, 0).applyQuaternion(p.q));
    const F = dirWorld(V(-1, 0, 0).applyQuaternion(p.q));
    const S = up.clone().negate();
    const N = V(0, 0, 0).crossVectors(F, S).normalize(); // palm normal (right hand)
    const gripW = toWorld(p.grip);
    const wrist = gripW.clone().addScaledVector(F, -0.075).addScaledVector(N, -0.03);
    this.solve(this.R, wrist, toWorld(V(0.55, -0.75, 0.25)));
    this.orientHand(this.R, F, S);
    this.curl(this.R, F, N, [1.25, 1.35, 0.9], 0.6);
    // Left hand: relaxed at the side, or reaching for something.
    const lF = dirWorld(V(0.1, -0.55, -0.8).normalize());
    const lS = dirWorld(V(-1, 0, 0));
    this.solve(this.L, toWorld(p.left), toWorld(V(-0.7, -0.6, 0.2)));
    this.orientHand(this.L, lF, lS);
    this.curl(this.L, lF, V(0, 0, 0).crossVectors(lS, lF).normalize(), [0.35, 0.4, 0.3], 0.2);
  }

  // Two-bone IK: elbow on the side of `pole`.
  solve(arm, target, pole) {
    const a = arm.upper.getWorldPosition(V(0, 0, 0));
    const d = THREE.MathUtils.clamp(target.distanceTo(a), 0.05, arm.lenA + arm.lenB - 0.002);
    const dir = target.clone().sub(a).normalize();
    const cosA = THREE.MathUtils.clamp((arm.lenA ** 2 + d * d - arm.lenB ** 2) / (2 * arm.lenA * d), -1, 1);
    const pd = pole.clone().sub(a);
    pd.addScaledVector(dir, -pd.dot(dir)).normalize();
    const elbow = a.clone().addScaledVector(dir, cosA * arm.lenA).addScaledVector(pd, Math.sqrt(1 - cosA * cosA) * arm.lenA);
    this.aim(arm.upper, arm.lower, elbow);
    this.aim(arm.lower, arm.hand, a.clone().addScaledVector(dir, d));
  }

  // Rotate `bone` so that its child `child` lies toward `target` (world).
  aim(bone, child, target) {
    const bp = bone.getWorldPosition(V(0, 0, 0));
    const from = child.getWorldPosition(V(0, 0, 0)).sub(bp).normalize();
    const to = target.clone().sub(bp).normalize();
    const q = new THREE.Quaternion().setFromUnitVectors(from, to);
    this.setWorldQ(bone, q.multiply(bone.getWorldQuaternion(new THREE.Quaternion())));
  }

  setWorldQ(bone, qw) {
    const parent = bone.parent.getWorldQuaternion(new THREE.Quaternion());
    bone.quaternion.copy(parent.invert().multiply(qw));
    bone.updateMatrixWorld(true);
  }

  // Hand frame: bone +y = fingers (F), the knuckle line (index → pinky) = S.
  orientHand(arm, F, S) {
    const Sl = arm.sideL, Yl = V(0, 1, 0), Zl = V(0, 0, 0).crossVectors(Sl, Yl);
    const Sw = S.clone().addScaledVector(F, -S.dot(F)).normalize(), Zw = V(0, 0, 0).crossVectors(Sw, F);
    const local = new THREE.Matrix4().makeBasis(Sl, Yl, Zl);
    const world = new THREE.Matrix4().makeBasis(Sw, F, Zw);
    const q = new THREE.Quaternion().setFromRotationMatrix(world.multiply(local.transpose()));
    this.setWorldQ(arm.hand, q);
  }

  // Close the fingers toward the palm (rotate about F × N), each joint by its own angle.
  curl(arm, F, N, angles, thumb) {
    const axis = V(0, 0, 0).crossVectors(F, N).normalize().multiplyScalar(this.curlSign ?? -1);
    for (const chain of arm.fingers) chain.forEach((b, i) => {
      if (!b) return;
      const q = new THREE.Quaternion().setFromAxisAngle(axis, angles[i]);
      this.setWorldQ(b, q.multiply(b.getWorldQuaternion(new THREE.Quaternion())));
    });
    arm.thumb.forEach((b, i) => {
      if (!b || i === 0) return;
      const q = new THREE.Quaternion().setFromAxisAngle(axis, thumb);
      this.setWorldQ(b, q.multiply(b.getWorldQuaternion(new THREE.Quaternion())));
    });
  }
}
