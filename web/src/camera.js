// Third-person orbit camera. Right thumb / mouse drag turns it; it eases back
// behind the player while walking if you leave it alone.
import * as THREE from 'three';
import { clamp, angleDelta } from './util.js';

// [crown radius, height] per unit scale
const CROWN = {
  'nature/pine_large': [2.3, 7.5],
  'nature/pine_medium': [1.6, 5.9],
  'nature/pine_small': [1.15, 4.0],
  'nature/tree_cone_a': [0.29, 1.2],
  'nature/tree_cone_b': [0.35, 1.2],
};

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
  insideCanopy(x, y, z) {
    for (const n of this.world.nodesNear(x, z, 4)) {
      if (!n.def.fall || n.state !== 'ready' || n.type === 'dead') continue;
      const dims = CROWN[n.key] ?? [0.3, 1.2];
      const crownR = dims[0] * n.scale;
      const height = dims[1] * n.scale;
      if (y > n.y + height) continue;
      if (Math.hypot(x - n.x, z - n.z) < crownR * (1 - Math.max(0, (y - n.y) / height) * 0.7)) return true;
    }
    return false;
  }

  snapBehind(facing) {
    this.yaw = facing + Math.PI;
  }

  update(dt, player, look, zoom, moving) {
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
    if (moving && this.idle > 1.2) {
      const want = player.facing + Math.PI;
      this.yaw += angleDelta(this.yaw, want) * Math.min(1, dt * 0.9);
    }

    const k = 1 - Math.exp(-12 * dt);
    this.target.lerp(new THREE.Vector3(player.pos.x, player.pos.y + 1.7, player.pos.z), dt ? k : 1);
    const cp = Math.cos(this.pitch), sp = Math.sin(this.pitch);
    const { fx, fz } = this.basis();
    const cam = this.camera.position;
    let d = this.dist;
    // Pull in if the terrain is in the way between player and camera.
    for (let i = 0; i < 8; i++) {
      const x = this.target.x - fx * cp * d, z = this.target.z - fz * cp * d, y = this.target.y + sp * d;
      if (this.world.terrain.heightAt(x, z) + 0.6 < y && !this.insideCanopy(x, y, z)) break;
      d *= 0.82;
    }
    cam.set(this.target.x - fx * cp * d, this.target.y + sp * d, this.target.z - fz * cp * d);
    const ground = this.world.terrain.heightAt(cam.x, cam.z) + 0.7;
    if (cam.y < ground) cam.y = ground;
    this.camera.lookAt(this.target);
  }
}
