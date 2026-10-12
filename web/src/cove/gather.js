// Gathering in the cove: aim at a plant or thing within reach, swing the machete or pick it up.
// Palms and bamboo take several cuts and fall over; bushes and big leaves give fibre and leaves;
// stones, driftwood and coconuts are picked up; washed-up crates and barrels hold supplies.
// The finds go into the inventory strip at the bottom of the screen.
import * as THREE from 'three';
import { cloneModel } from '../assets.js';
import { sfx } from './sound.js';

export const ITEMS = {
  wood: { name: 'Træ', model: 'item/wood' },
  palm_leaf: { name: 'Palmeblade', model: 'item/palm_leaf' },
  fiber: { name: 'Fibre', model: 'item/fiber' },
  bamboo: { name: 'Bambus', model: 'item/bamboo_poles' },
  stone: { name: 'Sten', model: 'item/stone' },
  coconut: { name: 'Kokosnødder', model: 'item/coconut' },
  banana: { name: 'Bananer', model: 'item/bananas' },
  rope: { name: 'Reb', model: 'item/rope' },
};

// cut: machete hits needed; give: items when done; fall: topples over; fx: chip colour.
const KINDS = {
  palm: { label: 'Hug palmen', cut: 5, give: { wood: 3, palm_leaf: 2 }, fall: 2.6, coconuts: [1, 3], fx: '#9a7448', hit: ['wood1', 'wood2', 'chop'] },
  palm_young: { label: 'Hug den unge palme', cut: 2, give: { palm_leaf: 2, wood: 1 }, fall: 1.4, fx: '#6f9a32', hit: ['chop', 'slice'] },
  bamboo: { label: 'Hug bambus', cut: 3, give: { bamboo: 3 }, fall: 2.2, fx: '#9fb848', hit: ['wood1', 'chop'] },
  banana: { label: 'Hug bananplanten', cut: 2, give: { banana: 1, palm_leaf: 1 }, fx: '#7fb33a', hit: ['slice', 'slice2'] },
  treefern: { label: 'Hug træbregnen', cut: 2, give: { fiber: 2, wood: 1 }, fall: 1.4, fx: '#6a9e2e', hit: ['chop', 'slice'] },
  bush: { label: 'Hug busken', cut: 2, give: { fiber: 2 }, fx: '#4f8a2a', hit: ['slice', 'slice2'] },
  leafy: { label: 'Hug planten', cut: 1, give: { fiber: 1 }, fx: '#5f9a30', hit: ['slice', 'slice2'] },
  cover: { label: 'Skær', cut: 1, give: { fiber: 1 }, fx: '#7aa83a', hit: ['slice', 'slice2'] },
  canopy: { label: 'For stort til macheten', cut: 0, fx: '#7d6a50', hit: ['wood_heavy'] },
  stone: { label: 'Saml sten', pick: true, give: { stone: 2 } },
  drift: { label: 'Saml drivtømmer', pick: true, give: { wood: 2 } },
  coconut: { label: 'Saml kokosnød', pick: true, give: { coconut: 1 } },
  crate: { label: 'Åbn kassen', pick: true, give: { rope: 1, banana: 2 }, open: true },
  barrel: { label: 'Åbn tønden', pick: true, give: { rope: 1, coconut: 2 }, open: true },
};
const COVER_NAMES = { 'grass/': 'Skær græs', 'plant/fern': 'Skær bregner', 'plant/ear': 'Skær planten', 'cover/bromeliad': 'Skær bromeliaen', 'cover/flowers': 'Pluk blomster' };

export class Gather {
  constructor({ scene, camera, assets, flora, island, hands, mobile, ui }) {
    Object.assign(this, { scene, camera, assets, flora, island, hands, mobile, ui });
    this.inv = {};
    this.target = null;
    this.falling = [];
    this.shakes = [];
    this.chips = new Chips(scene);
    this.tmp = new THREE.Matrix4();
    hands.onHit = () => this.hit();
    hands.onPick = () => this.collect();
    this.icons = makeIcons(assets);
    this.buildUi();
  }

  // ---- targeting -----------------------------------------------------------------------------
  aim() {
    const cam = this.camera, p = cam.position;
    const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(cam.quaternion);
    const flat = new THREE.Vector2(fwd.x, fwd.z).normalize();
    let best = null, bestScore = Infinity;
    const consider = (x, z, r, reach, obj) => {
      const dx = x - p.x, dz = z - p.z, d = Math.hypot(dx, dz);
      const edge = Math.max(0, d - r);
      if (edge > reach) return;
      const cos = d < 0.01 ? 1 : (dx * flat.x + dz * flat.y) / d;
      if (cos < 0.72 && edge > 0.15) return;
      const score = edge + (1 - cos) * 3;
      if (score < bestScore) { bestScore = score; best = obj; }
    };
    for (const n of this.flora.nodesNear(p.x, p.z)) {
      const k = KINDS[n.kind];
      consider(n.x, n.z, n.kind === 'canopy' ? 1.0 : n.col?.r ?? 0.3, k.pick ? 2.0 : 2.3, n);
    }
    // Ground cover only counts when looking down at it.
    if (fwd.y < -0.25) for (const pl of this.flora.cover.near(p.x, p.z, 2.6)) consider(pl.x, pl.z, 0.2, 1.9, { kind: 'cover', key: pl.key, pl, x: pl.x, z: pl.z, y: pl.y });
    this.target = best;
  }

  label(t) {
    if (!t) return '';
    if (t.kind === 'cover') return Object.entries(COVER_NAMES).find(([k]) => t.key.startsWith(k))?.[1] ?? 'Skær';
    return KINDS[t.kind].label;
  }

  // Click / action button: pick up what's targeted, otherwise swing.
  act() {
    const t = this.target;
    if (t && KINDS[t.kind].pick) { if (this.hands.pickup()) this.pending = t; return; }
    if (this.hands.swing()) { this.pending = t; sfx(['swish', 'swish2'], { vol: 0.35 }); }
  }

  interact() {
    const t = this.target;
    if (t && KINDS[t.kind].pick && this.hands.pickup()) this.pending = t;
  }

  // ---- results -------------------------------------------------------------------------------
  hit() {
    const t = this.pending;
    this.pending = null;
    if (!t || t.gone) return;
    const k = KINDS[t.kind];
    if (k.pick) return;
    const at = new THREE.Vector3(t.x, (t.y ?? this.island.heightAt(t.x, t.z)) + (t.kind === 'cover' ? 0.25 : 1.0), t.z);
    sfx(k.hit, { vol: 0.55 });
    this.chips.burst(at, k.fx, t.kind === 'cover' ? 6 : 12);
    if (!k.cut) { this.toast('For stort — du skal bruge en økse', true); return; }
    t.hits = (t.hits ?? 0) + 1;
    if (t.handle) this.shakes.push({ t, age: 0 });
    if (t.hits < k.cut) return;
    // Spent: give the items and remove it.
    this.give(k.give);
    if (t.kind === 'cover') { this.flora.cover.remove(t.pl); return; }
    t.gone = true;
    if (t.col) this.flora.removeCollider(t.col);
    if (k.fall && t.handle) this.fell(t, k);
    else if (t.handle) this.flora.scatter.set(t.handle, null);
  }

  collect() {
    const t = this.pending;
    this.pending = null;
    if (!t || t.gone) return;
    const k = KINDS[t.kind];
    this.give(k.give);
    if (k.open) {
      // Opened crates stay; they just have nothing more in them.
      t.gone = true;
      sfx('crate', { vol: 0.5 });
      return;
    }
    sfx(['pickup', 'pickup2'], { vol: 0.6 });
    t.gone = true;
    if (t.col) this.flora.removeCollider(t.col);
    if (t.obj) t.obj.removeFromParent();
    if (t.handle) this.flora.scatter.set(t.handle, null);
  }

  give(items) {
    for (const [id, n] of Object.entries(items ?? {})) {
      this.inv[id] = (this.inv[id] ?? 0) + n;
      this.toast(`+${n} ${ITEMS[id].name}`, false, id);
    }
    this.renderInv();
  }

  // A cut palm (or bamboo) topples away from the player, then sinks; palms drop coconuts.
  fell(t, k) {
    const base = this.flora.scatter.original(t.handle).clone();
    this.flora.scatter.set(t.handle, null);
    const obj = cloneModel(this.assets, t.key);
    const pivot = new THREE.Group();
    pivot.position.setFromMatrixPosition(base);
    obj.applyMatrix4(base);
    obj.position.sub(pivot.position);
    pivot.add(obj);
    this.scene.add(pivot);
    const away = new THREE.Vector3(t.x - this.camera.position.x, 0, t.z - this.camera.position.z).normalize();
    const axis = new THREE.Vector3(away.z, 0, -away.x);
    this.falling.push({ pivot, axis, away, age: 0, dur: k.fall, t, k, dropped: false });
    sfx('treefall', { vol: t.kind === 'palm' ? 0.7 : 0.4, rate: t.kind === 'palm' ? 1 : 1.3 });
  }

  update(dt) {
    this.aim();
    // Shake what was just hit.
    this.shakes = this.shakes.filter((s) => {
      s.age += dt;
      const base = this.flora.scatter.original(s.t.handle);
      if (s.t.gone) return false;
      const a = Math.sin(s.age * 45) * 0.035 * Math.max(0, 1 - s.age / 0.35);
      const pos = new THREE.Vector3().setFromMatrixPosition(base);
      const m = new THREE.Matrix4().makeTranslation(pos.x, pos.y, pos.z).multiply(new THREE.Matrix4().makeRotationZ(a)).multiply(new THREE.Matrix4().makeTranslation(-pos.x, -pos.y, -pos.z)).multiply(base);
      this.flora.scatter.set(s.t.handle, s.age < 0.35 ? m : base);
      return s.age < 0.35;
    });
    // Falling trees: accelerate, land with a small bounce, rest, sink away.
    this.falling = this.falling.filter((f) => {
      f.age += dt;
      const u = Math.min(1, f.age / f.dur);
      let ang = (Math.PI / 2 - 0.12) * u * u;
      if (u >= 1) ang = Math.PI / 2 - 0.12 - Math.abs(Math.sin((f.age - f.dur) * 9)) * 0.06 * Math.exp(-(f.age - f.dur) * 4);
      f.pivot.quaternion.setFromAxisAngle(f.axis, -ang);
      if (u >= 1 && !f.dropped) {
        f.dropped = true;
        sfx('wood_heavy', { vol: 0.6, rate: 0.8 });
        if (f.k.coconuts) this.dropCoconuts(f);
      }
      if (f.age > f.dur + 6) f.pivot.position.y -= dt * 0.6;
      if (f.age > f.dur + 9) { f.pivot.removeFromParent(); return false; }
      return true;
    });
    this.chips.update(dt);
    this.updateUi();
  }

  dropCoconuts(f) {
    const [lo, hi] = f.k.coconuts;
    const n = lo + Math.floor(Math.random() * (hi - lo + 1));
    const h = 7 * (f.t.scale ?? 1);
    for (let i = 0; i < n; i++) {
      const x = f.t.x + f.away.x * h + (Math.random() - 0.5) * 2, z = f.t.z + f.away.z * h + (Math.random() - 0.5) * 2;
      const y = this.island.heightAt(x, z);
      if (y < 0) continue;
      const o = cloneModel(this.assets, 'item/coconut');
      o.position.set(x, y - 0.03, z);
      o.rotation.set(Math.random(), Math.random() * 6, Math.random());
      this.scene.add(o);
      this.flora.register('item/coconut', x, y, z, { obj: o });
    }
  }

  // ---- UI ----------------------------------------------------------------------------------
  buildUi() {
    const el = (tag, cls, parent = document.body) => { const e = document.createElement(tag); e.className = cls; parent.appendChild(e); return e; };
    this.ui.cross = el('div', 'cross');
    this.ui.prompt = el('div', 'prompt');
    this.ui.promptText = el('span', 'prompt-text', this.ui.prompt);
    this.ui.promptKey = el('span', 'prompt-key', this.ui.prompt);
    this.ui.bar = el('div', 'prompt-bar', this.ui.prompt);
    this.ui.barFill = el('i', '', this.ui.bar);
    this.ui.inv = el('div', 'inv');
    this.ui.toasts = el('div', 'toasts');
    if (this.mobile) {
      this.ui.act = el('button', 'act-btn');
      this.ui.act.textContent = 'Hug';
      const go = (e) => { e.preventDefault(); e.stopPropagation(); this.act(); };
      this.ui.act.addEventListener('touchstart', go, { passive: false });
      this.ui.act.addEventListener('click', go);
    }
    this.renderInv();
  }

  updateUi() {
    const t = this.target;
    const k = t ? KINDS[t.kind] : null;
    this.ui.cross.classList.toggle('on', !!t);
    this.ui.prompt.hidden = !t;
    if (t) {
      this.ui.promptText.textContent = this.label(t);
      this.ui.promptKey.textContent = this.mobile ? '' : k.pick ? 'E / klik' : k.cut ? 'klik' : '';
      const show = !!k.cut && k.cut > 1;
      this.ui.bar.hidden = !show;
      if (show) this.ui.barFill.style.width = `${((t.hits ?? 0) / k.cut) * 100}%`;
    }
    if (this.ui.act) this.ui.act.textContent = t && k.pick ? (k.open ? 'Åbn' : 'Saml') : 'Hug';
  }

  renderInv() {
    const ids = Object.keys(this.inv).filter((id) => this.inv[id] > 0);
    this.ui.inv.hidden = !ids.length;
    this.ui.inv.innerHTML = ids.map((id) => `<div class="slot" title="${ITEMS[id].name}"><img src="${this.icons[id] ?? ''}" alt=""><b>${this.inv[id]}</b><span>${ITEMS[id].name}</span></div>`).join('');
  }

  toast(text, warn = false, id = null) {
    const d = document.createElement('div');
    d.className = `toast${warn ? ' warn' : ''}`;
    d.innerHTML = `${id && this.icons[id] ? `<img src="${this.icons[id]}" alt="">` : ''}<span>${text}</span>`;
    this.ui.toasts.appendChild(d);
    setTimeout(() => d.classList.add('out'), 1600);
    setTimeout(() => d.remove(), 2200);
  }
}

// Wood chips / leaf bits flying from a cut.
class Chips {
  constructor(scene) {
    const geo = new THREE.TetrahedronGeometry(0.05);
    this.mesh = new THREE.InstancedMesh(geo, new THREE.MeshLambertMaterial({ flatShading: true }), 80);
    this.mesh.count = 0;
    this.mesh.frustumCulled = false;
    this.mesh.name = 'chips';
    scene.add(this.mesh);
    this.list = [];
    this.m = new THREE.Matrix4();
    this.c = new THREE.Color();
    for (let i = 0; i < 80; i++) this.mesh.setColorAt(i, this.c.set(0xffffff));
  }

  burst(at, color, n) {
    for (let i = 0; i < n; i++) {
      if (this.list.length >= 80) this.list.shift();
      this.list.push({ p: at.clone().add(new THREE.Vector3((Math.random() - 0.5) * 0.3, Math.random() * 0.3, (Math.random() - 0.5) * 0.3)), v: new THREE.Vector3((Math.random() - 0.5) * 3, 1.5 + Math.random() * 2.5, (Math.random() - 0.5) * 3), r: Math.random() * 6, age: 0, color: this.c.set(color).offsetHSL(0, 0, (Math.random() - 0.5) * 0.15).clone() });
    }
  }

  update(dt) {
    this.list = this.list.filter((c) => (c.age += dt) < 0.9);
    this.list.forEach((c, i) => {
      c.v.y -= 9.8 * dt;
      c.p.addScaledVector(c.v, dt);
      c.r += dt * 10;
      const s = 1 - c.age / 0.9;
      this.m.compose(c.p, new THREE.Quaternion().setFromEuler(new THREE.Euler(c.r, c.r * 0.7, 0)), new THREE.Vector3(s, s, s));
      this.mesh.setMatrixAt(i, this.m);
      this.mesh.setColorAt(i, c.color);
    });
    this.mesh.count = this.list.length;
    this.mesh.instanceMatrix.needsUpdate = true;
    if (this.mesh.instanceColor) this.mesh.instanceColor.needsUpdate = true;
  }
}

// Inventory icons: each item's model rendered once to a small transparent picture.
function makeIcons(assets) {
  const out = {};
  try {
    const size = 128;
    const r = new THREE.WebGLRenderer({ alpha: true, antialias: true, preserveDrawingBuffer: true });
    r.setSize(size, size, false);
    r.outputColorSpace = THREE.SRGBColorSpace;
    const scene = new THREE.Scene();
    scene.add(new THREE.HemisphereLight(0xffffff, 0x8a7a60, 2.2));
    const sun = new THREE.DirectionalLight(0xffffff, 2.2);
    sun.position.set(2, 4, 3);
    scene.add(sun);
    const cam = new THREE.PerspectiveCamera(30, 1, 0.01, 100);
    for (const [id, it] of Object.entries(ITEMS)) {
      if (!assets[it.model]) continue;
      const o = assets[it.model].scene.clone(true);
      o.traverse((m) => { if (m.isMesh) { m.material = m.material.clone(); m.material.flatShading = true; } });
      const box = new THREE.Box3().setFromObject(o);
      const c = box.getCenter(new THREE.Vector3()), s = box.getSize(new THREE.Vector3()).length();
      o.position.sub(c);
      const g = new THREE.Group();
      g.add(o);
      g.rotation.set(0.35, -0.6, 0);
      scene.add(g);
      cam.position.set(0, 0, s * 1.9);
      cam.lookAt(0, 0, 0);
      r.render(scene, cam);
      out[id] = r.domElement.toDataURL('image/png');
      scene.remove(g);
    }
    r.dispose();
    r.forceContextLoss?.();
  } catch { /* icons are optional */ }
  return out;
}
