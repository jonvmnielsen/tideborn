// Loads the synced .glb files (see web/assets.json) and offers helpers for
// cloning and instancing them.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

const HEX = 'assets/kaykit-hexagon';
export const MANIFEST = {
  player: 'assets/player.glb',
  grass: `${HEX}/tiles/base/hex_grass.glb`,
  coast_a: `${HEX}/tiles/coast/hex_coast_a.glb`,
  coast_b: `${HEX}/tiles/coast/hex_coast_b.glb`,
  coast_c: `${HEX}/tiles/coast/hex_coast_c.glb`,
  coast_d: `${HEX}/tiles/coast/hex_coast_d.glb`,
  coast_e: `${HEX}/tiles/coast/hex_coast_e.glb`,
  tree_a: `${HEX}/decoration/nature/tree_single_a.glb`,
  tree_b: `${HEX}/decoration/nature/tree_single_b.glb`,
  stump_a: `${HEX}/decoration/nature/tree_single_a_cut.glb`,
  stump_b: `${HEX}/decoration/nature/tree_single_b_cut.glb`,
  forest_a_large: `${HEX}/decoration/nature/trees_a_large.glb`,
  forest_a_medium: `${HEX}/decoration/nature/trees_a_medium.glb`,
  forest_a_small: `${HEX}/decoration/nature/trees_a_small.glb`,
  forest_b_large: `${HEX}/decoration/nature/trees_b_large.glb`,
  forest_b_medium: `${HEX}/decoration/nature/trees_b_medium.glb`,
  forest_b_small: `${HEX}/decoration/nature/trees_b_small.glb`,
  rock_a: `${HEX}/decoration/nature/rock_single_a.glb`,
  rock_b: `${HEX}/decoration/nature/rock_single_b.glb`,
  rock_c: `${HEX}/decoration/nature/rock_single_c.glb`,
  rock_d: `${HEX}/decoration/nature/rock_single_d.glb`,
  rock_e: `${HEX}/decoration/nature/rock_single_e.glb`,
  mountain_a: `${HEX}/decoration/nature/mountain_a_grass_trees.glb`,
  mountain_b: `${HEX}/decoration/nature/mountain_b_grass_trees.glb`,
  mountain_c: `${HEX}/decoration/nature/mountain_c_grass_trees.glb`,
  hills_a: `${HEX}/decoration/nature/hills_a_trees.glb`,
  hills_b: `${HEX}/decoration/nature/hills_b_trees.glb`,
  hills_c: `${HEX}/decoration/nature/hills_c_trees.glb`,
  reed_a: `${HEX}/decoration/nature/waterplant_a.glb`,
  reed_b: `${HEX}/decoration/nature/waterplant_b.glb`,
  reed_c: `${HEX}/decoration/nature/waterplant_c.glb`,
  lily_a: `${HEX}/decoration/nature/waterlily_a.glb`,
  lily_b: `${HEX}/decoration/nature/waterlily_b.glb`,
  cloud_big: `${HEX}/decoration/nature/cloud_big.glb`,
  cloud_small: `${HEX}/decoration/nature/cloud_small.glb`,
  lumber: `${HEX}/decoration/props/resource_lumber.glb`,
  stonepile: `${HEX}/decoration/props/resource_stone.glb`,
  barrel: `${HEX}/decoration/props/barrel.glb`,
  crate: `${HEX}/decoration/props/crate_open.glb`,
  sack: `${HEX}/decoration/props/sack.glb`,
};

export async function loadAssets(onProgress) {
  const manager = new THREE.LoadingManager();
  const loader = new GLTFLoader(manager).setMeshoptDecoder(MeshoptDecoder);
  const entries = Object.entries(MANIFEST);
  let done = 0;
  const out = {};
  await Promise.all(
    entries.map(async ([key, url]) => {
      const gltf = await loader.loadAsync(url);
      gltf.scene.updateMatrixWorld(true);
      out[key] = gltf;
      done++;
      onProgress?.(done / entries.length);
    }),
  );
  return out;
}

// Flatten a static model into its mesh parts with transforms relative to the model root.
export function meshParts(root) {
  root.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(root.matrixWorld).invert();
  const parts = [];
  root.traverse((o) => {
    if (o.isMesh) {
      parts.push({ geometry: o.geometry, material: o.material, matrix: new THREE.Matrix4().multiplyMatrices(inv, o.matrixWorld) });
    }
  });
  return parts;
}

// Collects placements per model and builds one InstancedMesh per mesh part.
export class InstanceBatch {
  constructor(assets) {
    this.assets = assets;
    this.placements = new Map(); // key → { matrices: [], opts }
  }
  add(key, matrix, opts = {}) {
    if (!this.placements.has(key)) this.placements.set(key, { matrices: [], opts });
    this.placements.get(key).matrices.push(matrix.clone());
  }
  build(parent) {
    const tmp = new THREE.Matrix4();
    for (const [key, { matrices, opts }] of this.placements) {
      for (const part of meshParts(this.assets[key].scene)) {
        const im = new THREE.InstancedMesh(part.geometry, part.material, matrices.length);
        matrices.forEach((m, i) => im.setMatrixAt(i, tmp.multiplyMatrices(m, part.matrix)));
        im.instanceMatrix.needsUpdate = true;
        im.castShadow = opts.castShadow ?? true;
        im.receiveShadow = opts.receiveShadow ?? true;
        im.computeBoundingSphere();
        im.name = key;
        parent.add(im);
      }
    }
  }
}

export function cloneStatic(assets, key, { castShadow = true, receiveShadow = true } = {}) {
  const obj = assets[key].scene.clone(true);
  obj.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = castShadow;
      o.receiveShadow = receiveShadow;
    }
  });
  return obj;
}
