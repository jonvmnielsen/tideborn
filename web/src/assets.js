// Loads every asset listed in public/assets/assets.lock.json (written by the
// game-assets sync script), keyed by its short name, e.g. "tree/pine_large_a".
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';

// Models → gltf; texture sets (kind "texture") → { diff, nor, … } THREE.Textures, tiling;
// sky light (kind "hdri") → equirectangular float texture.
export async function loadAssets(onProgress) {
  const lock = await (await fetch('assets/assets.lock.json')).json();
  const entries = Object.entries(lock.assets);
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const texLoader = new THREE.TextureLoader();
  const out = {};
  let done = 0;
  await Promise.all(
    entries.map(async ([key, info]) => {
      if (info.kind === 'texture') {
        const set = {};
        for (const [map, file] of Object.entries(info.files)) {
          const t = await texLoader.loadAsync(`assets/${file}`);
          t.wrapS = t.wrapT = THREE.RepeatWrapping;
          t.colorSpace = map === 'diff' ? THREE.SRGBColorSpace : THREE.NoColorSpace;
          set[map] = t;
        }
        out[key] = set;
      } else if (info.kind === 'hdri') {
        const t = await new RGBELoader().loadAsync(`assets/${info.file}`);
        t.mapping = THREE.EquirectangularReflectionMapping;
        out[key] = t;
      } else {
        const gltf = await loader.loadAsync(`assets/${info.file}`);
        gltf.scene.updateMatrixWorld(true);
        out[key] = gltf;
      }
      onProgress?.(++done / entries.length);
    }),
  );
  return out;
}

// Flatten a static model into mesh parts with transforms relative to its root.
export function meshParts(root) {
  root.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(root.matrixWorld).invert();
  const parts = [];
  root.traverse((o) => {
    if (o.isMesh) parts.push({ geometry: o.geometry, material: o.material, matrix: new THREE.Matrix4().multiplyMatrices(inv, o.matrixWorld) });
  });
  return parts;
}

export function modelBox(assets, key) {
  return new THREE.Box3().setFromObject(assets[key].scene);
}

// A pool of instances of one model. Each slot can be shown, hidden or moved later
// (used for forests where every tree can be chopped).
export class InstancePool {
  constructor(parent, assets, key, capacity, { castShadow = true, receiveShadow = true, material } = {}) {
    this.key = key;
    this.parts = meshParts(assets[key].scene).map((p) => {
      const im = new THREE.InstancedMesh(p.geometry, material ? material(p.material) : p.material, capacity);
      im.count = 0;
      im.castShadow = castShadow;
      im.receiveShadow = receiveShadow;
      im.frustumCulled = false; // instances span the whole island
      im.name = key;
      parent.add(im);
      return { im, local: p.matrix };
    });
    this.count = 0;
    this.capacity = capacity;
    this.tmp = new THREE.Matrix4();
    this.zero = new THREE.Matrix4().makeScale(0, 0, 0);
  }
  add(matrix) {
    if (this.count >= this.capacity) throw new Error(`pool ${this.key} full`);
    const i = this.count++;
    for (const p of this.parts) {
      p.im.setMatrixAt(i, this.tmp.multiplyMatrices(matrix, p.local));
      p.im.count = this.count;
      p.im.instanceMatrix.needsUpdate = true;
    }
    return i;
  }
  set(i, matrix) {
    for (const p of this.parts) {
      p.im.setMatrixAt(i, matrix ? this.tmp.multiplyMatrices(matrix, p.local) : this.zero);
      p.im.instanceMatrix.needsUpdate = true;
    }
  }
  finish() {
    for (const p of this.parts) p.im.computeBoundingSphere();
  }
}

export function cloneModel(assets, key, { castShadow = true, receiveShadow = true } = {}) {
  const obj = assets[key].scene.clone(true);
  obj.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = castShadow;
      o.receiveShadow = receiveShadow;
    }
  });
  return obj;
}

// Recolor a model's materials (KayKit uses one gradient atlas; multiplying keeps its shading).
export function tintedMaterial(color) {
  const cache = new Map();
  return (m) => {
    if (!cache.has(m)) {
      const c = m.clone();
      c.color = new THREE.Color(color);
      cache.set(m, c);
    }
    return cache.get(m);
  };
}
