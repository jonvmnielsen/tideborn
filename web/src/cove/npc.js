// Fellow castaways: Quaternius characters put together from parts that share one 65-bone rig —
// an outfit (Modular Character Outfits), the head of a base character (Universal Base
// Characters; only the head and neck are kept, the outfit covers the rest), hair, beard and
// eyebrows — and animated with clips from the Universal Animation Library.
import * as THREE from 'three';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';

// Keep only the triangles of a skinned mesh that mostly follow the given bones (the head).
function keepBones(mesh, names) {
  const g = mesh.geometry.clone();
  const idx = g.attributes.skinIndex, w = g.attributes.skinWeight;
  const want = new Set(mesh.skeleton.bones.map((b, i) => (names.includes(b.name) ? i : -1)).filter((i) => i >= 0));
  const keep = (v) => {
    let s = 0;
    for (let k = 0; k < 4; k++) if (want.has(idx.getComponent(v, k))) s += w.getComponent(v, k);
    return s > 0.5;
  };
  const src = g.index ? g.index.array : [...Array(g.attributes.position.count).keys()];
  const out = [];
  for (let i = 0; i < src.length; i += 3) if (keep(src[i]) && keep(src[i + 1]) && keep(src[i + 2])) out.push(src[i], src[i + 1], src[i + 2]);
  g.setIndex(out);
  mesh.geometry = g;
}

// Re-bind a skinned mesh from another file to the master rig's bones (matched by name).
function rebind(mesh, bones) {
  const list = mesh.skeleton.bones.map((b) => bones.get(b.name) ?? b);
  mesh.bind(new THREE.Skeleton(list, mesh.skeleton.boneInverses), mesh.bindMatrix);
}

export function makeCastaway(assets, { outfit = 'char/peasant', body = 'char/body_male', parts = ['char/hair_beard', 'char/hair_parted', 'char/eyebrows'], hair = '#5a3a22' } = {}) {
  const root = cloneSkinned(assets[outfit].scene);
  const bones = new Map();
  root.traverse((o) => { if (o.isBone) bones.set(o.name, o); });
  let rigParent = null;
  root.traverse((o) => { if (o.isSkinnedMesh && !rigParent) rigParent = o.parent; });
  const add = (key, filter) => {
    const part = cloneSkinned(assets[key].scene);
    part.updateMatrixWorld(true);
    const meshes = [];
    part.traverse((o) => { if (o.isSkinnedMesh) meshes.push(o); });
    for (const m of meshes) {
      if (filter) filter(m);
      rebind(m, bones);
      rigParent.add(m);
    }
  };
  add(body, (m) => { if (/MI_Superhero/i.test(m.material.name) || m.skeleton.bones.length > 10) keepBones(m, ['Head', 'neck_01']); });
  // The free hair textures are grey (the paid version tints them in a shader): tint here.
  for (const p of parts) add(p, (m) => { m.material = m.material.clone(); m.material.color.set(hair); });
  root.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; } });
  const mixer = new THREE.AnimationMixer(root);
  const clips = new Map([...(assets['char/anims'].animations ?? []), ...(assets['char/anims2']?.animations ?? [])].map((c) => [c.name, c]));
  // The library's clips also move the root bone; drop root position so the character stays put.
  for (const c of clips.values()) c.tracks = c.tracks.filter((t) => !/^root\.position/.test(t.name));
  let current = null;
  const once = new Set(['Death01', 'LayToIdle', 'Punch_Jab', 'Punch_Cross', 'Hit_Chest', 'Hit_Head', 'Hit_Knockback', 'Yes', 'Consume', 'Interact', 'PickUp_Table', 'Chest_Open', 'Melee_Hook', 'Sword_Attack', 'Sitting_Enter', 'Sitting_Exit']);
  const play = (name, fade = 0.3) => {
    const clip = clips.get(name);
    if (!clip) return;
    const a = mixer.clipAction(clip);
    if (current === a) return;
    a.reset().setEffectiveWeight(1);
    if (once.has(name)) { a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; }
    if (fade > 0) a.fadeIn(fade);
    a.play();
    if (current) { if (fade > 0) current.fadeOut(fade); else current.stop(); }
    current = a;
  };
  return { root, mixer, play, clips, get current() { return current; } };
}
