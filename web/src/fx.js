// Small chip bursts when chopping wood or breaking stone.
import * as THREE from 'three';

export class Chips {
  constructor(scene, count = 48) {
    const geo = new THREE.IcosahedronGeometry(0.09, 0);
    this.items = [];
    for (let i = 0; i < count; i++) {
      const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, flatShading: true, roughness: 0.9 });
      const m = new THREE.Mesh(geo, mat);
      m.visible = false;
      m.castShadow = false;
      scene.add(m);
      this.items.push({ m, vel: new THREE.Vector3(), spin: new THREE.Vector3(), life: 0 });
    }
    this.next = 0;
  }

  burst(pos, color, n = 8, power = 1) {
    for (let i = 0; i < n; i++) {
      const p = this.items[this.next++ % this.items.length];
      p.m.material.color.set(color).offsetHSL(0, 0, (Math.random() - 0.5) * 0.12);
      p.m.position.copy(pos);
      p.m.scale.setScalar(0.7 + Math.random() * 0.9);
      const a = Math.random() * Math.PI * 2;
      const s = (1.6 + Math.random() * 2.2) * power;
      p.vel.set(Math.cos(a) * s, 3 + Math.random() * 3 * power, Math.sin(a) * s);
      p.spin.set(Math.random() * 10, Math.random() * 10, Math.random() * 10);
      p.life = 0.7 + Math.random() * 0.4;
      p.m.visible = true;
    }
  }

  update(dt, groundAt) {
    for (const p of this.items) {
      if (p.life <= 0) continue;
      p.life -= dt;
      p.vel.y -= 14 * dt;
      p.m.position.addScaledVector(p.vel, dt);
      const g = groundAt(p.m.position.x, p.m.position.z);
      if (p.m.position.y < g + 0.05) {
        p.m.position.y = g + 0.05;
        p.vel.multiplyScalar(0.4);
        p.vel.y = Math.abs(p.vel.y) * 0.3;
      }
      p.m.rotation.x += p.spin.x * dt;
      p.m.rotation.y += p.spin.y * dt;
      if (p.life < 0.25) p.m.scale.multiplyScalar(0.86);
      if (p.life <= 0) p.m.visible = false;
    }
  }
}
