// First-person walker for the cove. Desktop: click to capture the mouse, WASD + Shift.
// Touch: left half = move stick, right half = look. A held tool sways with the steps.
import * as THREE from 'three';

const EYE = 1.68, WALK = 3.0, RUN = 5.6;
// On a mount: mount = { eye, walk, run, radius } (set by gather.js while you ride).

export class FirstPerson {
  constructor(camera, dom, { ground, blocked, depthAt }) {
    this.camera = camera;
    this.dom = dom;
    this.ground = ground;
    this.blocked = blocked;
    this.depthAt = depthAt;
    this.pos = new THREE.Vector3();
    this.yaw = 0;
    this.pitch = 0;
    this.keys = new Set();
    this.move = { x: 0, y: 0 };
    this.bob = 0;
    this.speed = 0;
    this.pace = 1; // load factor from the inventory (1 = free, lower = laden)
    this.enabled = false;
    camera.rotation.order = 'YXZ';

    addEventListener('keydown', (e) => this.keys.add(e.code));
    addEventListener('keyup', (e) => this.keys.delete(e.code));
    addEventListener('blur', () => this.keys.clear());
    dom.addEventListener('mousemove', (e) => {
      if (document.pointerLockElement !== dom) return;
      this.look(e.movementX, e.movementY, 0.0022);
    });

    // Touch: one finger per half of the screen.
    this.touches = new Map();
    const start = (e) => {
      for (const t of e.changedTouches) {
        const side = t.clientX < innerWidth / 2 ? 'move' : 'look';
        this.touches.set(t.identifier, { side, x0: t.clientX, y0: t.clientY, x: t.clientX, y: t.clientY });
      }
      e.preventDefault();
    };
    const moveT = (e) => {
      for (const t of e.changedTouches) {
        const s = this.touches.get(t.identifier);
        if (!s) continue;
        if (s.side === 'look') this.look(t.clientX - s.x, t.clientY - s.y, 0.0048);
        s.x = t.clientX; s.y = t.clientY;
      }
      this.updateStick();
      e.preventDefault();
    };
    const end = (e) => {
      for (const t of e.changedTouches) this.touches.delete(t.identifier);
      this.updateStick();
    };
    dom.addEventListener('touchstart', start, { passive: false });
    dom.addEventListener('touchmove', moveT, { passive: false });
    dom.addEventListener('touchend', end);
    dom.addEventListener('touchcancel', end);
  }

  updateStick() {
    const s = [...this.touches.values()].find((t) => t.side === 'move');
    if (!s) { this.move.x = this.move.y = 0; this.stick?.(null); return; }
    const dx = s.x - s.x0, dy = s.y - s.y0, l = Math.hypot(dx, dy), R = 60;
    const k = Math.min(1, l / R) / (l || 1);
    this.move.x = dx * k; this.move.y = -dy * k;
    this.stick?.({ x0: s.x0, y0: s.y0, dx: (dx / (l || 1)) * Math.min(l, R), dy: (dy / (l || 1)) * Math.min(l, R) });
  }

  look(dx, dy, sens) {
    this.yaw -= dx * sens;
    this.pitch = THREE.MathUtils.clamp(this.pitch - dy * sens, -1.35, 1.35);
  }

  place(x, z, yaw, feet) {
    this.pos.set(x, this.ground(x, z, feet) + this.eye, z);
    this.yaw = yaw;
  }

  get eye() { return this.mount?.eye ?? EYE; }

  // A tool held in the right hand, low in view (e.g. the machete).
  hold(obj) {
    this.tool = new THREE.Group();
    this.tool.add(obj);
    this.camera.add(this.tool);
    this.tool.position.set(0.34, -0.46, -0.62);
  }

  update(dt) {
    let fx = 0, fz = 0;
    const k = this.keys;
    if (k.has('KeyW') || k.has('ArrowUp')) fz += 1;
    if (k.has('KeyS') || k.has('ArrowDown')) fz -= 1;
    if (k.has('KeyD') || k.has('ArrowRight')) fx += 1;
    if (k.has('KeyA') || k.has('ArrowLeft')) fx -= 1;
    fx += this.move.x; fz += this.move.y;
    const l = Math.hypot(fx, fz);
    if (l > 1) { fx /= l; fz /= l; }
    const M = this.mount, EYE = this.eye, WALK = M?.walk ?? 3.0, RUN = M?.run ?? 5.6;
    const run = (M || this.pace > 0.5) && (M || (this.canRun?.() ?? true)) && (k.has('ShiftLeft') || k.has('ShiftRight') || Math.hypot(this.move.x, this.move.y) > 0.95);
    this.sprinting = !M && run && Math.hypot(fx, fz) > 0.1;
    const depth = this.depthAt(this.pos.x, this.pos.z);
    const wade = 1 - Math.min(0.6, Math.max(0, depth) * 0.5);
    const want = (run ? RUN : WALK) * Math.min(1, Math.hypot(fx, fz)) * wade * (M ? 1 : this.pace);
    this.speed += (want - this.speed) * Math.min(1, dt * 8);
    if (l > 0.01) {
      const s = Math.sin(this.yaw), c = Math.cos(this.yaw);
      const vx = (-s * fz + c * fx) / Math.max(1, Math.hypot(fx, fz));
      const vz = (-c * fz - s * fx) / Math.max(1, Math.hypot(fx, fz));
      const nx = this.pos.x + vx * this.speed * dt, nz = this.pos.z + vz * this.speed * dt;
      // Slide along obstacles; stop at chest-deep water.
      const feet = this.pos.y - EYE;
      const ok = (x, z) => !this.blocked(x, z, M?.radius ?? 0.35, feet) && this.depthAt(x, z) < (M ? 0.9 : 1.15)
        // a mount's chest is ahead of you: that has to fit too
        && (!M?.ahead || !this.blocked(x + vx * M.ahead, z + vz * M.ahead, M.radius, feet));
      if (ok(nx, nz)) { this.pos.x = nx; this.pos.z = nz; }
      else if (ok(nx, this.pos.z)) this.pos.x = nx;
      else if (ok(this.pos.x, nz)) this.pos.z = nz;
      this.bob += dt * this.speed * 2.1;
    }
    const gy = Math.max(this.ground(this.pos.x, this.pos.z, this.pos.y - EYE), -1.0) + EYE;
    this.pos.y += (gy - this.pos.y) * Math.min(1, dt * 12);
    const bobY = Math.sin(this.bob * 2) * 0.035 * Math.min(1, this.speed / WALK);
    this.camera.position.set(this.pos.x, this.pos.y + bobY, this.pos.z);
    this.camera.rotation.set(this.pitch, this.yaw, 0);
    if (this.tool) {
      const sw = Math.min(1, this.speed / WALK);
      this.tool.position.set(0.34 + Math.cos(this.bob) * 0.015 * sw, -0.46 + Math.abs(Math.sin(this.bob)) * 0.02 * sw, -0.62);
    }
  }
}
