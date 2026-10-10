// Third-person orbit camera. Right thumb / mouse drag turns it; it eases back
// behind the player while walking if you leave it alone.
import * as THREE from 'three';
import { clamp, angleDelta } from './util.js';

export class OrbitCam {
  constructor(camera, world) {
    this.camera = camera;
    this.world = world;
    this.yaw = 0;          // 0 = looking north (−z)
    this.pitch = 0.42;     // radians above horizontal
    this.dist = 10;
    this.target = new THREE.Vector3();
    this.idle = 0;
  }

  // Ground-plane forward and right vectors for camera-relative movement.
  basis() {
    return {
      fx: -Math.sin(this.yaw), fz: -Math.cos(this.yaw),
      rx: Math.cos(this.yaw), rz: -Math.sin(this.yaw),
    };
  }

  // Is a point inside the crown of a standing tree? (keeps the camera out of foliage)
  // Crowns are read from the tree models: the leafy part starts ~30 % up the tree.
  insideCanopy(x, y, z) {
    for (const n of this.world.nodesNear(x, z, 7)) {
      if (!n.def.fall || n.state !== 'ready' || n.type === 'dead') continue;
      const sz = this.world.size(n.key);
      const height = sz.y * n.scale;
      const base = n.y + height * 0.3;
      if (y < base || y > n.y + height) continue;
      const crownR = Math.max(sz.x, sz.z) * n.scale * 0.32;
      if (Math.hypot(x - n.x, z - n.z) < crownR * (1 - ((y - base) / (height * 0.7)) * 0.6)) return true;
    }
    for (const c of this.world.canopies ?? []) {
      const base = c.y + c.height * 0.25;
      if (y > base && y < c.y + c.height && Math.hypot(x - c.x, z - c.z) < c.r) return true;
    }
    return false;
  }

  snapBehind(facing) {
    this.yaw = facing + Math.PI;
  }

  // focus: optional point to orbit instead of the player (the build cursor).
  update(dt, player, look, zoom, moving, focus = null) {
    const sens = 0.0055;
    if (look.dx || look.dy) {
      this.yaw -= look.dx * sens;
      this.pitch = clamp(this.pitch + look.dy * sens * 0.8, 0.08, 1.25);
      this.idle = 0;
    } else {
      this.idle += dt;
    }
    if (zoom) this.dist = clamp(this.dist * (1 + zoom * 0.1), 5, 24);
    // Drift back behind the player when walking and not steering the camera.
    if (moving && !focus && this.idle > 1.2) {
      const want = player.facing + Math.PI;
      this.yaw += angleDelta(this.yaw, want) * Math.min(1, dt * 0.9);
    }

    const k = 1 - Math.exp(-12 * dt);
    const aimAt = focus ? new THREE.Vector3(focus.x, focus.y + 1.0, focus.z) : new THREE.Vector3(player.pos.x, player.pos.y + 1.7, player.pos.z);
    this.target.lerp(aimAt, dt ? k : 1);
    const cp = Math.cos(this.pitch), sp = Math.sin(this.pitch);
    const { fx, fz } = this.basis();
    const cam = this.camera.position;
    let d = this.dist;
    // Pull in if the terrain is in the way between player and camera.
    for (let i = 0; i < 8; i++) {
      const x = this.target.x - fx * cp * d, z = this.target.z - fz * cp * d, y = this.target.y + sp * d;
      if (this.world.terrain.heightAt(x, z) + 0.6 < y && (focus || !this.insideCanopy(x, y, z))) break;
      d *= 0.82;
    }
    cam.set(this.target.x - fx * cp * d, this.target.y + sp * d, this.target.z - fz * cp * d);
    const ground = this.world.terrain.heightAt(cam.x, cam.z) + 0.7;
    if (cam.y < ground) cam.y = ground;
    this.camera.lookAt(this.target);
  }
}
