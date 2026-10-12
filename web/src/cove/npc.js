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

export function makeCastaway(assets, { outfit = 'char/peasant', parts = ['char/hair_beard', 'char/hair_parted', 'char/eyebrows'], hair = '#5a3a22' } = {}) {
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
  add('char/body_male', (m) => { if (/MI_Superhero/i.test(m.material.name) || m.skeleton.bones.length > 10) keepBones(m, ['Head', 'neck_01']); });
  // The free hair textures are grey (the paid version tints them in a shader): tint here.
  for (const p of parts) add(p, (m) => { m.material = m.material.clone(); m.material.color.set(hair); });
  root.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; } });
  const mixer = new THREE.AnimationMixer(root);
  const clips = new Map((assets['char/anims'].animations ?? []).map((c) => [c.name, c]));
  // The library's clips also move the root bone; drop root position so the character stays put.
  for (const c of clips.values()) c.tracks = c.tracks.filter((t) => !/^root\.position/.test(t.name));
  let current = null;
  const play = (name, fade = 0.3) => {
    const clip = clips.get(name);
    if (!clip) return;
    const a = mixer.clipAction(clip);
    if (current === a) return;
    a.reset().fadeIn(fade).play();
    current?.fadeOut(fade);
    current = a;
  };
  return { root, mixer, play, clips };
}

// Two castaways at the camp: one walks the beach and back, one kneels by the boat mending it.
export class Castaways {
  constructor(scene, assets, island, camp) {
    this.island = island;
    this.walker = makeCastaway(assets);
    this.mender = makeCastaway(assets, { outfit: 'char/ranger', parts: ['char/hair_beard', 'char/eyebrows'], hair: '#2a1e16' });
    scene.add(this.walker.root, this.mender.root);
    const sx = camp.x + 3.5, sz = camp.z - 2.5;
    this.mender.root.position.set(sx, island.heightAt(sx, sz), sz);
    this.mender.root.rotation.y = -2.2;
    this.mender.play('Fixing_Kneeling', 0);
    this.path = [[camp.x + 8, camp.z - 9], [camp.x + 34, camp.z - 11], [camp.x + 22, camp.z - 16]];
    this.leg = 0;
    this.wait = 2;
    const [x, z] = this.path[0];
    this.walker.root.position.set(x, island.heightAt(x, z), z);
    this.walker.play('Idle_Loop', 0);
  }

  update(dt) {
    this.mender.mixer.update(dt);
    this.walker.mixer.update(dt);
    const w = this.walker.root;
    if (this.wait > 0) {
      this.wait -= dt;
      this.walker.play(this.wait > 1.5 ? 'Idle_Talking_Loop' : 'Idle_Loop');
      return;
    }
    const [tx, tz] = this.path[(this.leg + 1) % this.path.length];
    const dx = tx - w.position.x, dz = tz - w.position.z, d = Math.hypot(dx, dz);
    if (d < 0.3) { this.leg = (this.leg + 1) % this.path.length; this.wait = 3 + Math.random() * 4; return; }
    this.walker.play('Walk_Loop');
    const sp = 1.25 * dt;
    w.position.x += (dx / d) * sp;
    w.position.z += (dz / d) * sp;
    w.position.y = this.island.heightAt(w.position.x, w.position.z);
    const want = Math.atan2(dx, dz);
    let diff = want - w.rotation.y;
    diff = Math.atan2(Math.sin(diff), Math.cos(diff));
    w.rotation.y += diff * Math.min(1, dt * 5);
  }
}
