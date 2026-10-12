// First-person arms (D-018): "PSX First Person Arms" by drillimpact (CC0) — a viewmodel rig
// made for first person, with animations by its author. The machete (or the stone axe) sits in
// the right hand bone. Clips: knife_idle (holding), knife_hit_01/02 (alternating cuts; `onHit`
// fires mid-cut), knife_draw (taking a tool out), grab.L (the left hand picks something up while
// the right keeps the tool). A little walk sway on top.
import * as THREE from 'three';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';

const HIT_AT = { knife_hit_01: 0.32, knife_hit_02: 0.34 };
const PICK_AT = 0.36;

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
    this.socket = new THREE.Group(); // tool mount in the hand (tuned so the grip sits in the fist)
    this.hand.add(this.socket);
    this.socket.position.set(0, 0.075, 0.012);
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
    a.reset().setEffectiveWeight(1).fadeIn(fade).play();
    if (this.current && this.current !== a) this.current.fadeOut(fade);
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
    obj.position.copy(obj.userData.grip ?? new THREE.Vector3()).negate();
    obj.quaternion.identity();
    obj.traverse((o) => { if (o.isMesh) o.frustumCulled = false; });
    this.socket.add(obj);
    if (this.current) { this.oneShot = this.play('knife_draw', 0.1); this.state = { name: 'draw', t: 0 }; }
  }

  get busy() { return this.state.name !== 'idle'; }

  swing() {
    if (this.busy) return false;
    const name = this.cut++ % 2 ? 'knife_hit_02' : 'knife_hit_01';
    this.oneShot = this.play(name, 0.06);
    this.state = { name: 'swing', clip: name, t: 0, hit: false };
    return true;
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
    this.play(name, 0);
    this.current.time = t;
    this.mixer.update(0);
    this.fit();
    this.state = { name: 'pose', t };
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
    this.mixer.update(step);
    this.fit();
    if (st.name === 'swing' && !st.hit && st.t > HIT_AT[st.clip]) { st.hit = true; this.onHit?.(); }
    if (st.name === 'pickup' && !st.hit && st.t > PICK_AT) { st.hit = true; this.onPick?.(); }
    // Walk sway and breathing, and on narrow screens pull the arms back a little.
    const walk = Math.min(1, speed / 3), now = performance.now() / 1000;
    const narrow = THREE.MathUtils.clamp(1.5 - this.camera.aspect, 0, 1);
    // The rig was framed for a wider view: lift it so the hand and tool sit in our picture.
    this.holder.position.set(Math.cos(bob) * 0.012 * walk - narrow * 0.19, 0.075 + narrow * 0.02 - Math.abs(Math.sin(bob)) * 0.016 * walk + Math.sin(now * 1.6) * 0.003, -0.01 + narrow * 0.03);
    this.holder.rotation.set(0, 0, Math.cos(bob) * 0.012 * walk);
  }
}
