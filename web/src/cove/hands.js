// First-person arms (D-017): rigid faceted pieces from the asset forge — a fist closed around
// the tool's handle, an open left hand, forearms with rolled-up sleeves and upper arms. Nothing
// deforms. Poses are keyframed in camera space — where the tool's handle is and which way its
// blade and edge point; the fist rides on the handle and the arm follows by two-bone IK from a
// fixed shoulder. Animations: idle (breathing, walk sway), swing (wind-up, sweep, recover;
// `onHit` fires mid-sweep) and pickup (the left hand reaches down and forward).
import * as THREE from 'three';
import { prepareModel } from './facets.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const MACHETE_GRIP = V(-0.004, 0.075, 0); // handle centre in the machete model
const WRIST = V(0.1, 0, -0.03); // the fist's wrist, relative to the grip point (fist model)

// A pose: grip point, blade direction (machete +y) and edge direction, all in camera space.
function pose(grip, up, edge, left = null) {
  const Y = up.clone().normalize();
  const X = edge.clone().negate().addScaledVector(Y, edge.dot(Y)).normalize(); // machete +x = spine side
  const Z = V(0, 0, 0).crossVectors(X, Y);
  const q = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, Z));
  return { grip, q, left };
}

// Idle: the machete held upright in front, edge forward, hand low on the right.
const IDLE = pose(V(0.16, -0.21, -0.42), V(0.08, 1, -0.22), V(-0.25, 0, -1));
const LEFT_REST = V(-0.3, -0.8, -0.05);
// A wide, flat sweep from right to left: cuts everything in an arc in front of you.
const SWING = [
  [0, IDLE],
  [0.15, pose(V(0.28, -0.12, -0.32), V(0.55, 0.75, 0.35), V(-0.35, 0.05, -1))],
  [0.29, pose(V(-0.14, -0.34, -0.46), V(-0.8, -0.05, -0.6), V(-0.55, -0.15, 0.8))],
  [0.58, IDLE],
];
const PICKUP = [
  [0, { ...IDLE, left: LEFT_REST }],
  [0.26, { ...pose(V(0.22, -0.36, -0.38), V(0.15, 1, -0.1), V(-0.2, 0, -1)), left: V(-0.06, -0.19, -0.5) }],
  [0.62, { ...IDLE, left: LEFT_REST }],
];
const ease = (t) => t * t * (3 - 2 * t);

export class Hands {
  constructor(camera, assets, { machete }) {
    this.camera = camera;
    const piece = (key) => {
      const o = assets[key].scene.clone(true);
      prepareModel(o);
      o.traverse((m) => { if (m.isMesh) { m.castShadow = false; m.frustumCulled = false; } });
      return o;
    };
    // Arm segments are modelled along +y (from the joint nearest the hand).
    this.R = { upper: piece('arm/upperarm'), fore: piece('arm/forearm'), shoulder: V(0.17, -0.3, 0.06), pole: V(0.6, -0.7, 0.2) };
    this.L = { upper: piece('arm/upperarm'), fore: piece('arm/forearm'), shoulder: V(-0.17, -0.3, 0.06), pole: V(-0.6, -0.7, 0.2), hand: piece('arm/hand') };
    for (const a of [this.R, this.L]) { a.lenA = 0.27; a.lenB = 0.25; camera.add(a.upper, a.fore); }
    camera.add(this.L.hand);
    this.fist = piece('arm/fist');
    this.machete = null;
    this.setTool(machete);
    this.state = { name: 'idle', t: 0 };
    this.onHit = null;
    this.onPick = null;
  }

  // Swap what's in the right hand (object with userData.grip = handle point in its own space).
  // The fist sits on the handle, so it moves with the tool.
  setTool(obj) {
    if (this.machete === obj) return;
    this.machete?.removeFromParent();
    this.machete = obj;
    this.grip = obj.userData.grip ?? MACHETE_GRIP;
    this.fist.position.copy(this.grip);
    obj.add(this.fist);
    this.camera.add(obj);
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
    const sx = THREE.MathUtils.clamp(this.camera.aspect / 1.5, 0.35, 1);
    p.grip.x *= sx;
    p.grip.z *= 1 + (1 - sx) * 0.25;
    p.left.x *= sx;
    // Breathing and walking sway on top of every pose.
    const now = performance.now() / 1000;
    const walk = Math.min(1, speed / 3);
    p.grip.x += Math.cos(bob) * 0.012 * walk;
    p.grip.y += Math.abs(Math.sin(bob)) * 0.018 * walk + Math.sin(now * 1.6) * 0.004;
    p.grip.z += Math.sin(now * 1.1) * 0.003;

    // The tool (with the fist on its handle).
    this.machete.position.copy(p.grip).sub(this.grip.clone().applyQuaternion(p.q));
    this.machete.quaternion.copy(p.q);
    // Right arm: from the shoulder to the wrist of the fist.
    const wristR = this.grip.clone().add(WRIST).applyQuaternion(p.q).add(this.machete.position);
    this.arm(this.R, this.R.shoulder.clone().multiply(V(sx, 1, 1)), wristR);
    // Left arm: relaxed out of view, or reaching; the open hand points forward and down.
    const lsh = this.L.shoulder.clone().multiply(V(sx, 1, 1));
    this.arm(this.L, lsh, p.left);
    // Open hand model: fingers +y, palm facing −z. Fingers forward-down, palm facing down.
    const F = V(0.12, -0.5, -0.85).normalize(), palm = V(0, -0.9, 0.4);
    const Z = palm.negate().addScaledVector(F, -palm.dot(F)).normalize();
    this.L.hand.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(V(0, 0, 0).crossVectors(F, Z), F, Z));
    this.L.hand.position.copy(p.left);
  }

  // Two-bone IK in camera space, then lay the rigid segments along shoulder→elbow→wrist.
  arm(a, shoulder, wrist) {
    const d = THREE.MathUtils.clamp(wrist.distanceTo(shoulder), 0.05, a.lenA + a.lenB - 0.002);
    const dir = wrist.clone().sub(shoulder).normalize();
    const cosA = THREE.MathUtils.clamp((a.lenA ** 2 + d * d - a.lenB ** 2) / (2 * a.lenA * d), -1, 1);
    const pd = a.pole.clone();
    pd.addScaledVector(dir, -pd.dot(dir)).normalize();
    const elbow = shoulder.clone().addScaledVector(dir, cosA * a.lenA).addScaledVector(pd, Math.sqrt(1 - cosA * cosA) * a.lenA);
    const reach = shoulder.clone().addScaledVector(dir, d);
    this.lay(a.upper, elbow, shoulder, a.lenA);
    this.lay(a.fore, reach, elbow, a.lenB);
  }

  // Put a +y-modelled segment at `from`, pointing at `to`, stretched to length `len` (model ~len).
  lay(obj, from, to, len) {
    const dir = to.clone().sub(from);
    const L = dir.length();
    obj.position.copy(from);
    obj.quaternion.setFromUnitVectors(V(0, 1, 0), dir.normalize());
    obj.scale.set(1, L / len, 1);
  }
}
