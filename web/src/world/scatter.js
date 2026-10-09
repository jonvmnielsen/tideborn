// Chunked instancing: models placed across the island are batched per 64 m chunk,
// so the camera and shadow frustums can skip whole chunks. Every placement keeps a
// handle, so single trees can be hidden (felled) and shown again (regrown).
import * as THREE from 'three';
import { meshParts } from '../assets.js';

const CHUNK = 64;

export class Scatter {
  constructor(parent, assets) {
    this.parent = parent;
    this.assets = assets;
    this.groups = new Map(); // `${chunk}|${key}` → { key, matrices: [], opts, meshes }
    this.built = false;
    this.tmp = new THREE.Matrix4();
  }

  chunkOf(x, z) {
    return `${Math.floor(x / CHUNK)},${Math.floor(z / CHUNK)}`;
  }

  // Returns a handle { g, i } for later set().
  add(key, matrix, opts = {}, hidden = false) {
    const e = new THREE.Vector3().setFromMatrixPosition(matrix);
    const gk = `${this.chunkOf(e.x, e.z)}|${key}${opts.tint ? '|' + opts.tint : ''}`;
    let g = this.groups.get(gk);
    if (!g) {
      g = { key, opts, matrices: [], hidden: new Set(), meshes: null };
      this.groups.set(gk, g);
    }
    g.matrices.push(matrix.clone());
    if (hidden) g.hidden.add(g.matrices.length - 1);
    return { g, i: g.matrices.length - 1 };
  }

  build() {
    const tintCache = new Map();
    for (const g of this.groups.values()) {
      const parts = meshParts(this.assets[g.key].scene);
      g.meshes = parts.map((p) => {
        let mat = p.material;
        if (g.opts.tint) {
          const ck = `${mat.uuid}|${g.opts.tint}`;
          if (!tintCache.has(ck)) {
            const m = mat.clone();
            m.color = new THREE.Color(g.opts.tint);
            tintCache.set(ck, m);
          }
          mat = tintCache.get(ck);
        }
        const im = new THREE.InstancedMesh(p.geometry, mat, g.matrices.length);
        g.matrices.forEach((m, i) => im.setMatrixAt(i, this.tmp.multiplyMatrices(g.hidden.has(i) ? this.hiddenMatrix(m) : m, p.matrix)));
        im.instanceMatrix.needsUpdate = true;
        im.castShadow = g.opts.castShadow ?? true;
        im.receiveShadow = g.opts.receiveShadow ?? true;
        im.computeBoundingSphere();
        // Leave room for trees swaying or falling within the chunk.
        im.boundingSphere.radius += 6;
        im.name = g.key;
        this.parent.add(im);
        return { im, local: p.matrix };
      });
    }
    this.built = true;
  }

  // matrix = null hides the instance (shrinks it in place, keeping chunk bounds intact).
  set(handle, matrix) {
    const { g, i } = handle;
    const m = matrix ?? this.hiddenMatrix(g.matrices[i]);
    for (const p of g.meshes) {
      p.im.setMatrixAt(i, this.tmp.multiplyMatrices(m, p.local));
      p.im.instanceMatrix.needsUpdate = true;
    }
  }

  original(handle) {
    return handle.g.matrices[handle.i];
  }

  hiddenMatrix(m) {
    const p = new THREE.Vector3().setFromMatrixPosition(m);
    return new THREE.Matrix4().compose(p, new THREE.Quaternion(), new THREE.Vector3(1e-4, 1e-4, 1e-4));
  }
}

export function placement(x, y, z, rotY, scale) {
  return new THREE.Matrix4().compose(
    new THREE.Vector3(x, y, z),
    new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), rotY),
    new THREE.Vector3(scale, scale, scale),
  );
}
