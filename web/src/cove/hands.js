// First-person arms (D-018): "PSX First Person Arms" by drillimpact (CC0) — a viewmodel rig
// made for first person, with animations by its author. The machete (or the stone axe) sits in
// the right hand bone. Clips: knife_idle (holding), knife_hit_01/02 (alternating cuts; `onHit`
// fires mid-cut), knife_draw (taking a tool out), grab.L (the left hand picks something up while
// the right keeps the tool). A little walk sway on top.
//
// Like most first-person games (D-019) the arms are a "viewmodel": they live on layer 1 and are
// drawn in a second pass, after the world, with the depth cleared (they never cut into trees or
// walls) and through their own camera — its own field of view and a lens shift that keep the
// hand and tool small, down in the lower right corner, on any screen shape.
import * as THREE from 'three';
import { Pass } from 'three/addons/postprocessing/Pass.js';

export const VIEW_LAYER = 1;
// Viewmodel framing: `fov` = view angle across the screen's shorter side (degrees; wider = the
// arms look smaller), `shift` = where the picture is moved, in screen halves (+x right, −y down;
// x is scaled by the aspect on portrait screens, where the angle spans the width).
export const VIEW = { fov: 105, shift: [0.25, -0.38] };
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';

// The cut (D-020): our own motion on top of knife_idle — the PSX knife clips cut the other way.
// The arm draws back to the right, then sweeps in toward the middle and down, edge first, and
// comes back. Keys: [time, yaw (around the eye, + = left), pitch (+ = up), forearm roll (+ = tip
// to the right)]; the hit lands mid-sweep.
const CUT = [[0, 0, 0, 0], [0.17, -0.34, 0.1, 0.5], [0.33, 0.55, -0.26, -0.75], [0.62, 0, 0, 0]];
const CUT_HIT = 0.25;
const PICK_AT = 0.36;
const _q = new THREE.Quaternion(), _x = new THREE.Vector3(1, 0, 0), _y = new THREE.Vector3(0, 1, 0);

export class Hands {
  constructor(camera, assets, { machete }) {
    this.camera = camera;
    const src = assets['arm/psx'];
    this.rig = cloneSkinned(src.scene);
    this.rig.traverse((o) => {
      if (!o.isMesh) return;
      o.frustumCulled = false;
      o.castShadow = false;
      o.receiveShadow = false;
      // Pixel-art texture: keep it crisp.
      if (o.material.map) { o.material.map.magFilter = THREE.NearestFilter; o.material.map.needsUpdate = true; }
    });
    // The rig has its own "camera" bone (the eye the animations were made for; it looks along
    // its +x with +y up). Every frame the rig is placed so that bone sits exactly on our camera.
    this.eye = this.rig.getObjectByName('camera');
    this.rig.matrixAutoUpdate = false;
    this.holder = new THREE.Group();
    this.holder.add(this.rig);
    camera.add(this.holder);
    this.view = new THREE.PerspectiveCamera(60, 1, 0.01, 10);
    this.view.layers.set(VIEW_LAYER);
    camera.add(this.view);
    this.rig.traverse((o) => o.layers.set(VIEW_LAYER));
    this.hand = this.rig.getObjectByName('handR') ?? this.rig.getObjectByName('hand.R');
    this.mixer = new THREE.AnimationMixer(this.rig);
    this.clips = new Map(src.animations.map((c) => [c.name, c]));
    this.actions = new Map();
    for (const [name, clip] of this.clips) {
      const a = this.mixer.clipAction(clip);
      if (!/idle|relax/.test(name)) { a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; }
      this.actions.set(name, a);
    }
    this.mixer.addEventListener('finished', (e) => { if (e.action === this.oneShot) this.toIdle(); });
    // Tool mount: the centre of the hole the closed fingers make (measured from the finger joints
    // of the knife_idle pose). The handle runs across the fist, along the knuckle line, with the
    // blade coming out above the thumb and index finger (hand +z); tool +y → hand +z.
    this.socket = new THREE.Group();
    this.hand.add(this.socket);
    this.socket.position.set(-0.012, 0.085, 0);
    this.socket.quaternion.setFromAxisAngle(new THREE.Vector3(1, 0, 0), Math.PI / 2);
    // The knife clips hold a short knife flat across the body. A machete is held upright in front
    // of you, so after each animation frame the forearm is turned (supination, around its own
    // long axis) and the wrist cocked a little — the fist and the grip stay as animated.
    this.forearm = this.hand.parent;
    this.twist = { roll: 0.9, bend: -0.4 };
    // Turn about the handle (it is round, so free in the fist).
    this.turn = -0.5; // edge toward the middle of the screen, so it leads the cut
    this.rollAxis = this.hand.position.clone().normalize();
    // The knife clips hold the left arm out in front as a guard. Keep the view clear: the left arm
    // is folded away (its upper-arm bone scaled to nothing, so it vanishes into the shoulder
    // behind the eye) and only comes out to pick something up.
    this.leftArm = this.rig.getObjectByName('upper_armL') ?? this.rig.getObjectByName('upper_arm.L');
    this.leftShow = 0;
    this.base = [this.forearm.quaternion.clone(), this.hand.quaternion.clone(), this.leftArm.scale.clone()];
    this.machete = null;
    this.current = null;
    this.setTool(machete);
    this.onHit = null;
    this.onPick = null;
    this.cut = 0;
    this.oneShot = this.play('knife_draw', 0);
    this.state = { name: 'draw', t: 0 };
  }

  play(name, fade = 0.12) {
    const a = this.actions.get(name);
    if (!a) return null;
    // A zero-length fade can leave the weight at 0 while time stands still (frozen poses), so
    // cut over directly then.
    a.reset().setEffectiveWeight(1);
    if (fade > 0) a.fadeIn(fade);
    a.play();
    if (this.current && this.current !== a) { if (fade > 0) this.current.fadeOut(fade); else this.current.stop(); }
    this.current = a;
    return a;
  }

  toIdle() {
    this.state = { name: 'idle', t: 0 };
    this.oneShot = null;
    this.play('knife_idle', 0.18);
  }

  // Swap what's in the right hand: the tool's handle point (userData.grip) goes into the fist.
  setTool(obj) {
    if (this.machete === obj) return;
    this.machete?.removeFromParent();
    this.machete = obj;
    obj.quaternion.setFromAxisAngle(_y, this.turn);
    obj.position.copy(obj.userData.grip ?? new THREE.Vector3()).applyQuaternion(obj.quaternion).negate();
    obj.traverse((o) => { o.layers.set(VIEW_LAYER); if (o.isMesh) o.frustumCulled = false; });
    this.socket.add(obj);
    if (this.current) { this.oneShot = this.play('knife_draw', 0.1); this.state = { name: 'draw', t: 0 }; }
  }

  get busy() { return this.state.name !== 'idle'; }

  swing() {
    if (this.busy) return false;
    this.cut++;
    this.state = { name: 'swing', t: 0, hit: false };
    return true;
  }

  // The cut's offsets at time t (smooth between keys; the sweep itself speeds up into the hit).
  cutAt(t) {
    for (let i = 1; i < CUT.length; i++) {
      const [t1] = CUT[i];
      if (t > t1 && i < CUT.length - 1) continue;
      const a = CUT[i - 1], b = CUT[i];
      let u = THREE.MathUtils.clamp((t - a[0]) / (b[0] - a[0]), 0, 1);
      u = i === 2 ? u * u * (3 - 2 * u) * 0.5 + u * u * 0.5 : u * u * (3 - 2 * u);
      return { yaw: a[1] + (b[1] - a[1]) * u, pitch: a[2] + (b[2] - a[2]) * u, roll: a[3] + (b[3] - a[3]) * u };
    }
  }

  pickup() {
    if (this.busy) return false;
    this.oneShot = this.play('grab.L', 0.1);
    this.state = { name: 'pickup', t: 0, hit: false };
    return true;
  }

  // Show one clip frozen at time t (tests / screenshots).
  pose(name, t) {
    this.freeze = true;
    if (name === 'cut') { this.state = { name: 'swing', t, hit: true }; this.play('knife_idle', 0); this.update(0); return; }
    this.leftShow = name.endsWith('.L') ? 1 : 0;
    this.play(name, 0);
    this.current.time = t;
    this.unadjust();
    this.mixer.update(0);
    this.adjust();
    this.fit();
    this.state = { name: 'pose', t };
  }

  // The mixer only writes bones whose animated value changed, so undo our turn first.
  unadjust() {
    this.forearm.quaternion.copy(this.base[0]);
    this.hand.quaternion.copy(this.base[1]);
    this.leftArm.scale.copy(this.base[2]);
  }

  // The viewmodel camera: same place and direction as the eye, its own lens.
  frame() {
    const v = this.view, a = this.camera.aspect, half = THREE.MathUtils.degToRad(VIEW.fov / 2);
    // VIEW.fov spans the shorter side; three.js wants the vertical angle.
    v.fov = THREE.MathUtils.radToDeg(2 * (a >= 1 ? half : Math.atan(Math.tan(half) / a)));
    v.aspect = a;
    v.updateProjectionMatrix();
    v.projectionMatrix.elements[8] = -VIEW.shift[0] * Math.min(1, a); // less sideways on portrait
    v.projectionMatrix.elements[9] = -VIEW.shift[1];
    v.projectionMatrixInverse.copy(v.projectionMatrix).invert();
  }

  // Draw the arms over what is already in the target (world first, then this).
  draw(renderer, scene) {
    this.frame();
    const clear = renderer.autoClear, shadows = renderer.shadowMap.autoUpdate;
    renderer.autoClear = false;
    renderer.shadowMap.autoUpdate = false; // the world pass already made this frame's shadows
    renderer.clearDepth();
    renderer.render(scene, this.view);
    renderer.autoClear = clear;
    renderer.shadowMap.autoUpdate = shadows;
  }

  adjust() {
    this.base[0].copy(this.forearm.quaternion);
    this.base[1].copy(this.hand.quaternion);
    this.base[2].copy(this.leftArm.scale);
    this.leftArm.scale.multiplyScalar(Math.max(1e-3, this.leftShow));
    const { bend } = this.twist, roll = this.twist.roll + (this.swingRoll ?? 0);
    if (roll) this.forearm.quaternion.multiply(_q.setFromAxisAngle(this.rollAxis, roll));
    if (bend) this.hand.quaternion.multiply(_q.setFromAxisAngle(_x, bend));
  }

  // The rig is authored in glTF space looking along +z with +y up, its "camera" bone at the
  // eye. Turn it to face our camera's −z and move the eye bone onto the camera.
  fit() {
    this.rig.matrix.identity();
    this.rig.updateMatrixWorld(true);
    const e = new THREE.Vector3().setFromMatrixPosition(this.eye.matrixWorld).applyMatrix4(this.rig.matrixWorld.clone().invert());
    this.rig.matrix.makeRotationY(Math.PI).multiply(new THREE.Matrix4().makeTranslation(-e.x, -e.y, -e.z));
    this.rig.matrixWorldNeedsUpdate = true;
  }

  update(dt, { speed = 0, bob = 0 } = {}) {
    const st = this.state;
    const step = this.freeze ? 0 : dt;
    st.t += step;
    const cut = st.name === 'swing' ? this.cutAt(st.t) : null;
    this.swingRoll = cut?.roll ?? 0;
    if (!this.freeze) this.leftShow += ((st.name === 'pickup' ? 1 : 0) - this.leftShow) * Math.min(1, dt * 12);
    this.unadjust();
    this.mixer.update(step);
    this.adjust();
    this.fit();
    if (st.name === 'swing' && !st.hit && st.t > CUT_HIT) { st.hit = true; this.onHit?.(); }
    if (st.name === 'swing' && !this.freeze && st.t > CUT[CUT.length - 1][0]) { this.state = { name: 'idle', t: 0 }; this.swingRoll = 0; }
    if (st.name === 'pickup' && !st.hit && st.t > PICK_AT) { st.hit = true; this.onPick?.(); }
    // Walk sway and breathing.
    const walk = Math.min(1, speed / 3), now = performance.now() / 1000;
    this.holder.position.set(Math.cos(bob) * 0.012 * walk, 0.075 - Math.abs(Math.sin(bob)) * 0.016 * walk + Math.sin(now * 1.6) * 0.003, -0.01);
    this.holder.rotation.set(cut?.pitch ?? 0, cut?.yaw ?? 0, Math.cos(bob) * 0.012 * walk);
  }
}

// Composer pass for the viewmodel (after the world RenderPass, before bloom).
export class ViewmodelPass extends Pass {
  constructor(hands, scene) {
    super();
    this.hands = hands;
    this.scene = scene;
    this.needsSwap = false;
  }

  render(renderer, writeBuffer, readBuffer) {
    renderer.setRenderTarget(this.renderToScreen ? null : readBuffer);
    this.hands.draw(renderer, this.scene);
  }
}
