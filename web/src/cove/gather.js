// Gathering in the cove. A swing sweeps an arc in front of you (about 120°, a couple of metres)
// and cuts everything in it — a swathe of grass, a few bushes, the palm you stand next to.
// Palms and bamboo take several cuts and fall over; big rainforest trees need the stone axe.
// Stones, driftwood, coconuts and piles are picked up; washed-up crates and barrels hold supplies
// (one of them a canvas backpack). What doesn't fit in your load is left in a pile on the ground.
// Cut plants grow back after a while. Progress is saved in the browser.
import * as THREE from 'three';
import { cloneModel } from '../assets.js';
import { sfx } from './sound.js';
import { ITEMS, RECIPES, Inventory, BASE_KG, SLOW_AT } from './inventory.js';
import { PIECES, PIECE } from './build.js';

// cut: hits with { machete, axe } (0 = can't); give: items; fall: seconds to topple;
// regrow: seconds until it's back (0 = never).
const KINDS = {
  palm: { label: 'Palme', cut: { machete: 5, axe: 3 }, give: { wood: 3, palm_leaf: 2 }, fall: 2.6, coconuts: [1, 3], fx: '#9a7448', hit: ['wood1', 'wood2', 'chop'], regrow: 900 },
  palm_young: { label: 'Ung palme', cut: { machete: 2, axe: 2 }, give: { palm_leaf: 2, wood: 1 }, fall: 1.4, fx: '#6f9a32', hit: ['chop', 'slice'], regrow: 400 },
  canopy: { label: 'Regnskovstræ', cut: { machete: 0, axe: 8 }, give: { wood: 6 }, fall: 3.4, fx: '#7d6a50', hit: ['wood_heavy', 'wood1'], regrow: 1500 },
  bamboo: { label: 'Bambus', cut: { machete: 3, axe: 2 }, give: { bamboo: 3 }, fall: 2.2, fx: '#9fb848', hit: ['wood1', 'chop'], regrow: 500 },
  banana: { label: 'Bananplante', cut: { machete: 2, axe: 2 }, give: { banana: 1, palm_leaf: 1 }, fx: '#7fb33a', hit: ['slice', 'slice2'], regrow: 400 },
  treefern: { label: 'Træbregne', cut: { machete: 2, axe: 2 }, give: { fiber: 2, wood: 1 }, fall: 1.4, fx: '#6a9e2e', hit: ['chop', 'slice'], regrow: 400 },
  bush: { label: 'Busk', cut: { machete: 2, axe: 2 }, give: { fiber: 2 }, fx: '#4f8a2a', hit: ['slice', 'slice2'], regrow: 300 },
  leafy: { label: 'Planter', cut: { machete: 1, axe: 1 }, give: { fiber: 1 }, fx: '#5f9a30', hit: ['slice', 'slice2'], regrow: 200 },
  cover: { label: 'Græs', cut: { machete: 1, axe: 1 }, give: { fiber: 1 }, fx: '#7aa83a', hit: ['slice', 'slice2'], regrow: 150 },
  stone: { label: 'Saml sten', pick: true, give: { stone: 2 }, regrow: 600 },
  drift: { label: 'Saml drivtømmer', pick: true, give: { wood: 2 }, regrow: 900 },
  coconut: { label: 'Saml kokosnød', pick: true, give: { coconut: 1 } },
  pile: { label: 'Saml bunken', pick: true },
  crate: { label: 'Åbn kassen', pick: true, open: true },
  barrel: { label: 'Åbn tønden', pick: true, open: true },
  shelter: { label: 'Dit læ', pick: false },
};
// What the camp's crates and barrels hold, in the order they were placed.
const LOOT = { crate: [{ rope: 2, banana: 2 }, { fiber: 4 }, { bag_canvas: 1, rope: 1 }], barrel: [{ coconut: 3 }, { rope: 1 }, { coconut: 2 }] };
const REACH = 2.6, ARC = Math.cos((70 * Math.PI) / 180);
const SAVE_KEY = 'tideborn-cove-save-1';

export class Gather {
  constructor({ scene, camera, assets, flora, island, hands, mobile, tools, building, creatures, vitals }) {
    Object.assign(this, { scene, camera, assets, flora, island, hands, mobile, tools, build: building, creatures, vitals });
    building.changed = () => { this.dirty = true; };
    creatures.hasFood = (sp) => sp.tame.food.some((f) => this.inv.count(f) > 0);
    this.inv = new Inventory();
    this.target = null;
    this.falling = [];
    this.shakes = [];
    this.cut = new Map(); // node id → time it was used up (for regrowth and saving)
    this.coverCut = new Map(); // ground-cover id → time
    this.piles = [];
    this.shelters = [];
    this.chips = new Chips(scene);
    this.clock = 0;
    this.warned = 0;
    hands.onHit = () => this.hit();
    hands.onPick = () => this.collect();
    this.icons = makeIcons(assets, PIECES);
    let lootI = { crate: 0, barrel: 0 };
    for (const n of [...flora.byId.values()].sort((a, b) => a.id - b.id)) if (LOOT[n.kind]) n.loot = LOOT[n.kind][lootI[n.kind]++ % LOOT[n.kind].length];
    this.ui = new GatherUi(this);
    this.inv.listeners.push(() => { this.ui.render(); this.equip(); this.dirty = true; });
    this.load();
    this.equip();
  }

  get tool() { return this.inv.tool === 'stone_axe' ? 'axe' : 'machete'; }

  equip() {
    const want = this.inv.tool ?? 'machete';
    if (this.held !== want) { this.held = want; this.hands.setTool(this.tools[want] ?? this.tools.machete); }
  }

  cycleTool() {
    const owned = ['machete', 'stone_axe'].filter((t) => this.inv.count(t) > 0);
    if (owned.length < 2) { this.toast('Du har kun macheten — lav en stenøkse', true); return; }
    this.inv.tool = owned[(owned.indexOf(this.inv.tool) + 1) % owned.length];
    this.inv.changed();
    this.toast(ITEMS[this.inv.tool].name, false, this.inv.tool);
  }

  // ---- what's in front of you -------------------------------------------------------------
  inArc(x, z, r, reach = REACH) {
    const p = this.camera.position, f = this.flat();
    const dx = x - p.x, dz = z - p.z, d = Math.hypot(dx, dz);
    const edge = Math.max(0, d - r);
    if (edge > reach) return null;
    const cos = d < 0.01 ? 1 : (dx * f.x + dz * f.y) / d;
    if (cos < ARC && edge > 0.3) return null;
    return { edge, cos };
  }

  flat() {
    const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(this.camera.quaternion);
    return new THREE.Vector2(fwd.x, fwd.z).normalize();
  }

  radius(n) { return n.kind === 'canopy' ? (n.key.includes('giant') ? 1.4 : 0.7) : n.col?.r ?? 0.3; }

  // The prompt: a thing to pick up you're looking at, else the nearest thing a swing would cut.
  aim() {
    const p = this.camera.position;
    let pick = null, cut = null, bp = Infinity, bc = Infinity;
    for (const n of this.flora.nodesNear(p.x, p.z)) {
      const k = KINDS[n.kind];
      if (!k) continue;
      const a = this.inArc(n.x, n.z, this.radius(n), k.pick ? 2.1 : REACH);
      if (!a) continue;
      const score = a.edge + (1 - a.cos) * 3;
      if (k.pick && score < bp && a.cos > 0.85) { bp = score; pick = n; }
      if (k.cut && score < bc) { bc = score; cut = n; }
    }
    this.target = pick ?? cut;
    this.pickTarget = pick;
    this.carcass = pick ? null : this.creatures.carcassNear(p, this.flat());
    if (this.carcass) { this.pickTarget = null; this.target = null; }
    this.animal = pick || this.carcass ? null : this.creatures.animalNear(p, this.flat());
    if (this.animal) { this.target = null; }
  }

  // Feed a wild animal one of the foods it likes; enough feedings and it's yours.
  feed(c) {
    const food = c.sp.tame.food.find((f) => this.inv.count(f) > 0);
    if (!food) return;
    this.inv.remove(food, 1);
    const r = c.feed();
    sfx('pickup', { vol: 0.5, rate: 0.7 });
    if (r === 'tamed') { this.toast(`${c.sp.name}en stoler på dig — du kalder den ${c.name}. ${c.sp.tame.use}.`, false, null); sfx('pickup2', { vol: 0.7, rate: 0.8 }); }
    else this.toast(`${c.sp.name}en spiser af din hånd (${c.trust}/${c.sp.tame.feeds})`, false, food);
    this.dirty = true;
  }

  animalLoad(c) { return Object.entries(c.storage ?? {}).reduce((a, [id, n]) => a + (ITEMS[id]?.kg ?? 0) * n, 0); }

  // Stations you're standing by (a burning campfire within 4 m).
  near() {
    const p = this.camera.position, out = new Set();
    for (const q of this.build.pieces) if (q.id === 'campfire' && Math.hypot(q.x - p.x, q.z - p.z) < 4) out.add('campfire');
    return out;
  }

  eat(id) {
    const f = ITEMS[id]?.food;
    if (!f || !this.inv.count(id)) return;
    this.inv.remove(id, 1);
    this.vitals.heal(f);
    sfx('pickup', { vol: 0.5, rate: 0.8 });
    this.toast(`Spiste ${ITEMS[id].name.toLowerCase()} (+${f} liv)`, false, id);
  }

  // You blacked out: everything but tools and bags stays in a pile where you fell.
  dropAll() {
    const drop = {};
    for (const [id, n] of Object.entries(this.inv.items)) if (n > 0 && !ITEMS[id]?.tool && !ITEMS[id]?.bag) drop[id] = n;
    for (const [id, n] of Object.entries(drop)) this.inv.remove(id, n);
    if (Object.keys(drop).length) { const p = this.camera.position; this.dropPile(drop, { x: p.x, z: p.z }); }
  }

  // Click / action button: pick up what you look at, otherwise swing.
  act() {
    const b = this.build;
    if (b.mode?.id) {
      const id = b.mode.id, r = b.commit(this.inv);
      if (r) { this.toast(r.text, r.warn, r.warn ? null : `b:${id}`); if (!r.warn) sfx('wood_heavy', { vol: 0.5 }); }
      if (r && !r.warn && !b.canPay(id, this.inv)) { b.stop(); this.toast('Du har ikke materialer til flere', true); }
      return;
    }
    if (b.mode?.tear) {
      const r = b.removeMarked(this.inv);
      this.toast(r.text, r.warn);
      if (!r.warn) sfx('wood_heavy', { vol: 0.45, rate: 1.2 });
      return;
    }
    if (this.pickTarget) { if (this.hands.pickup()) this.pending = this.pickTarget; return; }
    if (this.carcass) { if (this.hands.pickup()) this.pending = { carcass: this.carcass }; return; }
    if (this.animal) return this.useAnimal(this.animal);
    if (b.useTarget) return this.use(b.useTarget);
    if (this.hands.swing()) sfx(['swish', 'swish2'], { vol: 0.35 });
  }

  interact() {
    if (this.pickTarget) { if (this.hands.pickup()) this.pending = this.pickTarget; return; }
    if (this.carcass) { if (this.hands.pickup()) this.pending = { carcass: this.carcass }; return; }
    if (this.animal) return this.useAnimal(this.animal);
    if (this.build.useTarget) this.use(this.build.useTarget);
  }

  // Doors and gates open and close, a chest opens the bag panel beside it, a bed becomes home.
  use(p) {
    if (p.id === 'door' || p.id === 'gate') { this.build.toggle(p); sfx('wood1', { vol: 0.4, rate: p.open ? 0.8 : 1.1 }); return; }
    if (p.id === 'chest') { this.ui.chest = p; this.ui.toggle(true); sfx('crate', { vol: 0.4 }); return; }
    if (p.id === 'bed') { this.build.spawn = p; this.dirty = true; this.toast('Din seng — her vågner du', false, 'b:bed'); }
  }

  useAnimal(c) {
    if (c.tamed) { this.ui.chest = c; this.ui.toggle(true); return; }
    if (this.creatures.hasFood(c.sp)) { if (this.hands.pickup()) this.pending = { feed: c }; return; }
    this.toast(`${c.sp.name}en vil have ${c.sp.tame.food.map((f) => ITEMS[f].name.toLowerCase()).join(' eller ')}`, true);
  }

  startBuild(id) {
    this.build.start(id);
    this.toast(this.mobile ? `${PIECE[id].name}: sigt og tryk Byg` : `${PIECE[id].name}: klik for at bygge · R drejer · Esc stopper`, false, `b:${id}`);
  }

  // ---- a swing lands: everything in the arc takes a cut ------------------------------------
  hit() {
    const p = this.camera.position, tool = this.tool;
    const gained = {}, sounds = new Set();
    let bursts = 0, tooBig = false;
    const add = (items) => { for (const [id, n] of Object.entries(items ?? {})) gained[id] = (gained[id] ?? 0) + n; };
    for (const n of this.flora.nodesNear(p.x, p.z)) {
      const k = KINDS[n.kind];
      if (!k?.cut || n.gone || !this.inArc(n.x, n.z, this.radius(n))) continue;
      const need = n.key.includes('giant') && tool === 'axe' ? 14 : k.cut[tool];
      if (!need) { tooBig = true; sounds.add(k.hit); continue; }
      sounds.add(k.hit);
      if (bursts++ < 6) this.chips.burst(new THREE.Vector3(n.x, n.y + (n.kind === 'leafy' || n.kind === 'bush' ? 0.5 : 1.0), n.z), k.fx, 10);
      n.hits = (n.hits ?? 0) + 1;
      if (n.handle && n.hits < need) this.shakes.push({ t: n, age: 0 });
      if (n.hits < need) continue;
      add(n.key.includes('giant') ? { wood: 12 } : k.give);
      this.spend(n);
      if (k.fall && n.handle) this.fell(n, k); else if (n.handle) this.flora.scatter.set(n.handle, null);
    }
    // Ground cover: the whole swathe goes.
    const swathe = this.flora.cover.near(p.x, p.z, REACH + 0.4).filter((pl) => this.inArc(pl.x, pl.z, 0.15, REACH));
    for (const pl of swathe.slice(0, 40)) {
      add(pl.key.startsWith('cover/flowers') ? {} : KINDS.cover.give);
      if (bursts++ < 10) this.chips.burst(new THREE.Vector3(pl.x, pl.y + 0.25, pl.z), KINDS.cover.fx, 4);
      this.coverCut.set(pl.id, this.clock);
      this.flora.cover.removed.add(pl.id);
    }
    if (swathe.length) { this.flora.cover.drop(swathe.slice(0, 40)); sounds.add(KINDS.cover.hit); }
    // Animals in the arc.
    for (const c of this.creatures.inArc(p, this.flat(), REACH + 0.3, ARC)) {
      const killed = c.hurt(tool === 'axe' ? 26 : 18, p);
      this.chips.burst(c.pos.clone().add(new THREE.Vector3(0, c.sp.height * 0.55, 0)), '#8a1e1a', 10);
      sfx(['flesh1', 'flesh2', 'flesh3'], { vol: 0.6 });
      if (killed) this.toast(`${c.sp.name} er nede — flå den med E`, false);
    }
    for (const s of [...sounds].slice(0, 2)) sfx(s, { vol: 0.55 });
    if (tooBig && this.clock - this.warned > 3) { this.warned = this.clock; this.toast('For stort til macheten — lav en stenøkse', true); }
    if (Object.keys(gained).length) this.receive(gained);
  }

  spend(n) {
    n.gone = true;
    this.cut.set(n.id, this.clock);
    if (n.col) this.flora.removeCollider(n.col);
    this.dirty = true;
  }

  collect() {
    const n = this.pending;
    this.pending = null;
    if (n?.feed) { if (!n.feed.dead && !n.feed.tamed) this.feed(n.feed); return; }
    if (n?.carcass) {
      if (n.carcass.butchered) return;
      sfx(['slice', 'slice2'], { vol: 0.6 });
      this.chips.burst(n.carcass.pos.clone().add(new THREE.Vector3(0, 0.4, 0)), '#7a1c18', 12);
      this.receive(this.creatures.butcher(n.carcass));
      return;
    }
    if (!n || n.gone) return;
    const k = KINDS[n.kind];
    if (k.open) {
      if (n.opened) { this.toast('Den er tom', true); return; }
      n.opened = true;
      this.cut.set(n.id, -1);
      sfx('crate', { vol: 0.5 });
      this.receive(n.loot ?? {}, n);
      return;
    }
    sfx(['pickup', 'pickup2'], { vol: 0.6 });
    const items = n.kind === 'pile' ? n.items : k.give;
    const left = this.inv.add(items);
    this.announce(items, left);
    if (n.kind === 'pile') {
      if (Object.keys(left).length) { n.items = left; this.dirty = true; return; }
      this.piles = this.piles.filter((p) => p !== n);
      n.gone = true;
      n.obj.removeFromParent();
      this.dirty = true;
      return;
    }
    if (Object.keys(left).length) { this.dropPile(left); }
    this.spend(n);
    if (n.obj) n.obj.removeFromParent();
    if (n.handle) this.flora.scatter.set(n.handle, null);
  }

  // Put items in the inventory; what doesn't fit goes in a pile at your feet.
  receive(items) {
    const left = this.inv.add(items);
    this.announce(items, left);
    if (Object.keys(left).length) this.dropPile(left);
  }

  announce(items, left = {}) {
    for (const [id, n] of Object.entries(items)) {
      const got = n - (left[id] ?? 0);
      if (got > 0) this.toast(`+${got} ${ITEMS[id].name}`, false, id);
    }
    if (this.inv.burden > 1 && !this.warnedHeavy) { this.warnedHeavy = true; this.toast(`Du er overlæsset (${this.inv.load.toFixed(0)} / ${this.inv.capacity} kg) — du går langsomt og kan ikke løbe`, true); }
    if (this.inv.burden <= 1) this.warnedHeavy = false;
  }

  dropPile(items, at = null) {
    const p = this.camera.position, f = this.flat();
    const x = at?.x ?? p.x + f.x * 0.9, z = at?.z ?? p.z + f.y * 0.9;
    // Join a pile that's already there.
    const near = this.piles.find((q) => Math.hypot(q.x - x, q.z - z) < 1.5);
    if (near) { for (const [id, n] of Object.entries(items)) near.items[id] = (near.items[id] ?? 0) + n; this.dirty = true; return; }
    const y = this.island.heightAt(x, z);
    const g = new THREE.Group();
    Object.keys(items).slice(0, 3).forEach((id, i) => {
      const o = cloneModel(this.assets, ITEMS[id].model);
      o.position.set((i - 1) * 0.25, 0, (i % 2) * 0.2);
      o.rotation.y = i * 1.3;
      g.add(o);
    });
    g.position.set(x, y, z);
    this.scene.add(g);
    const n = this.flora.register('pile', x, y, z, { obj: g, id: `pile-${Date.now()}-${Math.random()}` });
    n.items = { ...items };
    this.piles.push(n);
    this.dirty = true;
  }

  // A cut tree topples away from the player, then sinks; palms drop coconuts.
  fell(n, k) {
    const base = this.flora.scatter.original(n.handle).clone();
    this.flora.scatter.set(n.handle, null);
    const obj = cloneModel(this.assets, n.key);
    const pivot = new THREE.Group();
    pivot.position.setFromMatrixPosition(base);
    obj.applyMatrix4(base);
    obj.position.sub(pivot.position);
    pivot.add(obj);
    this.scene.add(pivot);
    const away = new THREE.Vector3(n.x - this.camera.position.x, 0, n.z - this.camera.position.z).normalize();
    const axis = new THREE.Vector3(away.z, 0, -away.x);
    this.falling.push({ pivot, axis, away, age: 0, dur: k.fall, n, k, dropped: false });
    sfx('treefall', { vol: n.kind === 'palm' || n.kind === 'canopy' ? 0.7 : 0.4, rate: n.kind === 'canopy' ? 0.85 : n.kind === 'palm' ? 1 : 1.3 });
  }

  dropCoconuts(f) {
    const [lo, hi] = f.k.coconuts;
    const count = lo + Math.floor(Math.random() * (hi - lo + 1));
    const h = 7 * (f.n.scale ?? 1);
    for (let i = 0; i < count; i++) {
      const x = f.n.x + f.away.x * h + (Math.random() - 0.5) * 2, z = f.n.z + f.away.z * h + (Math.random() - 0.5) * 2;
      const y = this.island.heightAt(x, z);
      if (y < 0) continue;
      const o = cloneModel(this.assets, 'item/coconut');
      o.position.set(x, y - 0.03, z);
      o.rotation.set(Math.random(), Math.random() * 6, Math.random());
      this.scene.add(o);
      this.flora.register('item/coconut', x, y, z, { obj: o, id: `coco-${Date.now()}-${i}` });
    }
  }

  // ---- regrowth ------------------------------------------------------------------------------
  restore(n) {
    n.gone = false;
    n.hits = 0;
    this.cut.delete(n.id);
    if (n.col) this.flora.restoreCollider(n.col);
    if (n.handle) this.flora.scatter.set(n.handle, this.flora.scatter.original(n.handle));
    if (n.obj && !n.obj.parent) this.flora.root.add(n.obj);
  }

  regrow() {
    for (const [id, at] of this.cut) {
      const n = this.flora.byId.get(id), k = n && KINDS[n.kind];
      if (!k?.regrow || at < 0) continue;
      if (this.clock - at > k.regrow) this.restore(n);
    }
    let any = false;
    for (const [id, at] of this.coverCut) if (this.clock - at > KINDS.cover.regrow) { this.coverCut.delete(id); this.flora.cover.removed.delete(id); any = true; }
    if (any) this.flora.cover.refresh();
  }

  // ---- building ------------------------------------------------------------------------------
  startPlacing(id) { if (PIECE[id]) this.startBuild(id); }

  // Saves from before the building kit had lean-tos as a list of their own.
  addShelter(x, z, rot) {
    this.build.place('lean_to', { pos: { x, y: this.island.heightAt(x, z), z }, rot });
  }

  // ---- per frame -----------------------------------------------------------------------------
  update(dt) {
    this.clock += dt;
    this.aim();
    this.shakes = this.shakes.filter((s) => {
      s.age += dt;
      if (s.t.gone) return false;
      const base = this.flora.scatter.original(s.t.handle);
      const a = Math.sin(s.age * 45) * 0.035 * Math.max(0, 1 - s.age / 0.35);
      const pos = new THREE.Vector3().setFromMatrixPosition(base);
      const m = new THREE.Matrix4().makeTranslation(pos.x, pos.y, pos.z).multiply(new THREE.Matrix4().makeRotationZ(a)).multiply(new THREE.Matrix4().makeTranslation(-pos.x, -pos.y, -pos.z)).multiply(base);
      this.flora.scatter.set(s.t.handle, s.age < 0.35 ? m : base);
      return s.age < 0.35;
    });
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
    if ((this.regrowT = (this.regrowT ?? 0) + dt) > 5) { this.regrowT = 0; this.regrow(); }
    if (this.dirty && (this.saveT = (this.saveT ?? 0) + dt) > 2) { this.saveT = 0; this.save(); }
    this.ui.update();
  }

  // ---- saving --------------------------------------------------------------------------------
  save() {
    this.dirty = false;
    const data = {
      v: 1, clock: this.clock, inv: this.inv.toJSON(),
      cut: [...this.cut].filter(([id]) => typeof id === 'number'),
      cover: [...this.coverCut], opened: [...this.flora.byId.values()].filter((n) => n.opened).map((n) => n.id),
      piles: this.piles.map((p) => ({ x: p.x, z: p.z, items: p.items })), build: this.build.serialize(),
      vitals: this.vitals.toJSON(), dead: this.creatures.serialize(), tame: this.creatures.serializeTame(),
    };
    try { localStorage.setItem(SAVE_KEY, JSON.stringify(data)); } catch { /* private mode: no saving */ }
  }

  load() {
    let data = null;
    try { data = JSON.parse(localStorage.getItem(SAVE_KEY) ?? 'null'); } catch { data = null; }
    if (!data || data.v !== 1) return;
    this.clock = data.clock ?? 0;
    this.inv.load_(data.inv);
    for (const [id, at] of data.cut ?? []) {
      const n = this.flora.byId.get(id);
      if (!n) continue;
      this.cut.set(id, at);
      n.gone = true;
      if (n.col) this.flora.removeCollider(n.col);
      if (n.handle) this.flora.scatter.set(n.handle, null);
      if (n.obj) n.obj.removeFromParent();
    }
    for (const id of data.opened ?? []) { const n = this.flora.byId.get(id); if (n) { n.opened = true; this.cut.set(id, -1); } }
    for (const [id, at] of data.cover ?? []) { this.coverCut.set(id, at); this.flora.cover.removed.add(id); }
    this.flora.cover.refresh();
    for (const p of data.piles ?? []) this.dropPile(p.items, p);
    for (const s of data.shelters ?? []) this.addShelter(s.x, s.z, s.rot);
    this.build.restore(data.build);
    this.vitals.load_(data.vitals);
    this.creatures.restore(data.dead, data.tame);
    this.regrow();
    this.dirty = false;
  }

  reset() {
    try { localStorage.removeItem(SAVE_KEY); } catch { /* ignore */ }
    location.reload();
  }

  toast(text, warn, id) { this.ui.toast(text, warn, id); }
}

// ---- screen: crosshair, prompt, toasts, the bag panel --------------------------------------------
class GatherUi {
  constructor(g) {
    this.g = g;
    const el = (tag, cls, parent = document.body, html = '') => { const e = document.createElement(tag); e.className = cls; e.innerHTML = html; parent.appendChild(e); return e; };
    this.cross = el('div', 'cross');
    this.prompt = el('div', 'prompt');
    this.promptText = el('span', 'prompt-text', this.prompt);
    this.promptKey = el('span', 'prompt-key', this.prompt);
    this.bar = el('div', 'prompt-bar', this.prompt);
    this.barFill = el('i', '', this.bar);
    this.toasts = el('div', 'toasts');
    // Top right: the bag button with the load, and (phones) the tool button.
    this.hud = el('div', 'hud');
    this.toolBtn = el('button', 'hud-btn tool', this.hud);
    this.bagBtn = el('button', 'hud-btn bag', this.hud);
    const tap = (b, f) => { b.addEventListener('click', (e) => { e.stopPropagation(); f(); }); b.addEventListener('touchstart', (e) => { e.preventDefault(); e.stopPropagation(); f(); }, { passive: false }); };
    tap(this.bagBtn, () => this.toggle());
    tap(this.toolBtn, () => g.cycleTool());
    if (g.mobile) {
      this.act = el('button', 'act-btn', document.body, 'Hug');
      tap(this.act, () => g.act());
    }
    // While building: turn and stop (on phones these are the only way; on desktop R / Esc too).
    this.buildBar = el('div', 'build-bar');
    this.turnBtn = el('button', 'hud-btn', this.buildBar, '⟳ Drej');
    this.stopBtn = el('button', 'hud-btn', this.buildBar, '✕ Stop');
    tap(this.turnBtn, () => g.build.turn());
    tap(this.stopBtn, () => g.build.stop());
    this.tab = 'bag';
    this.panel = el('div', 'bagpanel');
    this.panel.hidden = true;
    this.panel.addEventListener('click', (e) => e.stopPropagation());
    this.panel.addEventListener('touchstart', (e) => e.stopPropagation(), { passive: true });
    this.render();
  }

  get open() { return !this.panel.hidden; }

  toggle(force, tab) {
    this.panel.hidden = force !== undefined ? !force : !this.panel.hidden;
    if (tab) this.tab = tab;
    if (!this.open) this.chest = null;
    if (this.open) { document.exitPointerLock?.(); this.render(); }
    this.onToggle?.(this.open);
  }

  icon(id) { return this.g.icons[id] ? `<img src="${this.g.icons[id]}" alt="">` : ''; }

  cost(c) { const inv = this.g.inv; return Object.entries(c).map(([id, n]) => `<span class="${inv.count(id) >= n ? 'ok' : ''}">${this.icon(id)}${inv.count(id)}/${n}</span>`).join(''); }

  // The chest: everything in the bag on one side, the chest on the other; tap a stack to move it.
  renderChest() {
    const inv = this.g.inv, box = this.chest.storage, animal = this.chest.tamed ? this.chest : null;
    const cap = animal ? animal.sp.tame.carry : Infinity, load = animal ? this.g.animalLoad(animal) : 0;
    const bagItems = Object.entries(inv.items).filter(([id, n]) => n > 0 && id !== 'machete');
    const boxItems = Object.entries(box).filter(([, n]) => n > 0);
    const cell = (id, n, side) => `<div class="bp-item" data-move="${side}" data-id="${id}">${this.icon(id)}<b>${n}</b><span>${ITEMS[id]?.name ?? id}</span></div>`;
    this.panel.innerHTML = `
      <div class="bp-head"><h2>${animal ? `${animal.name} · ${animal.sp.name.toLowerCase()}` : 'Kiste'}</h2><button class="bp-close" type="button">Luk</button></div>
      ${animal ? `<div class="bp-load"><div class="bp-meter"><i style="width:${Math.min(100, (load / cap) * 100)}%"></i></div><span>Sadeltasker: ${load.toFixed(1)} / ${cap} kg</span></div>
      <div class="bp-tabs"><button data-mode="follow" class="${animal.mode === 'follow' ? 'on' : ''}">Følg mig</button><button data-mode="stay" class="${animal.mode === 'stay' ? 'on' : ''}">Bliv her</button></div>` : ''}
      <p class="bp-foot">Tryk på en bunke for at flytte den over.</p>
      <div class="bp-cols">
        <section><h3>Rygsæk · ${inv.load.toFixed(0)}/${inv.capacity} kg</h3><div class="bp-grid">${bagItems.map(([id, n]) => cell(id, n, 'in')).join('') || '<p class="bp-empty">Tom</p>'}</div></section>
        <section><h3>${animal ? 'I sadeltaskerne' : 'I kisten'}</h3><div class="bp-grid">${boxItems.map(([id, n]) => cell(id, n, 'out')).join('') || '<p class="bp-empty">Tom</p>'}</div></section>
      </div>`;
    this.panel.querySelector('.bp-close').onclick = () => this.toggle(false);
    for (const b of this.panel.querySelectorAll('[data-mode]')) b.onclick = () => { animal.mode = b.dataset.mode; this.g.dirty = true; this.g.toast(animal.mode === 'follow' ? `${animal.name} følger dig` : `${animal.name} bliver her`, false); this.render(); };
    for (const b of this.panel.querySelectorAll('[data-move]')) b.onclick = () => {
      const id = b.dataset.id;
      if (b.dataset.move === 'in') {
        let n = inv.count(id);
        if (animal) n = Math.min(n, Math.floor((cap - load + 1e-6) / Math.max(0.001, ITEMS[id]?.kg ?? 0)));
        if (n <= 0) { this.g.toast(`${animal.name} kan ikke bære mere`, true); return; }
        inv.remove(id, n); box[id] = (box[id] ?? 0) + n;
      }
      else { const n = box[id]; delete box[id]; inv.add({ [id]: n }); }
      this.g.dirty = true;
      sfx('pickup', { vol: 0.4 });
      this.render();
    };
  }

  renderBuild() {
    const inv = this.g.inv, b = this.g.build;
    return `<div class="bp-recipes bp-build">${PIECES.map((p) => `
      <div class="bp-rec${b.canPay(p.id, inv) ? '' : ' no'}">${this.icon(`b:${p.id}`)}<div><b>${p.name}</b>${p.note ? `<small>${p.note}</small>` : ''}
        <div class="bp-cost">${b.kit(p.id, inv) ? `<span class="ok">${this.icon('lean_to')}byggesæt</span>` : this.cost(p.cost)}</div></div>
        <button data-build="${p.id}" ${b.canPay(p.id, inv) ? '' : 'disabled'}>Byg</button></div>`).join('')}</div>
      <p class="bp-foot">Sigt med sigtekornet. Vægge, døre og tag sætter sig på fundamenternes kanter og hjørner; et loft er gulv på næste etage. <button class="bp-tear" type="button">Riv ned…</button></p>`;
  }

  render() {
    const inv = this.g.inv, kg = inv.load, cap = inv.capacity;
    this.bagBtn.innerHTML = `${this.icon(inv.bag ?? 'bag_leaf')}<span>${kg.toFixed(0)}/${cap} kg</span>`;
    this.bagBtn.classList.toggle('full', inv.burden > 1);
    this.bagBtn.classList.toggle('heavy', inv.burden > SLOW_AT && inv.burden <= 1);
    this.toolBtn.innerHTML = this.icon(inv.tool ?? 'machete');
    if (!this.open) return;
    if (this.chest) return this.renderChest();
    const items = Object.entries(inv.items).filter(([, n]) => n > 0);
    const bag = inv.bag ? ITEMS[inv.bag].name : 'Ingen taske';
    const near = this.g.near();
    this.panel.innerHTML = `
      <div class="bp-head"><div class="bp-tabs"><button data-tab="bag" class="${this.tab === 'bag' ? 'on' : ''}">Rygsæk</button><button data-tab="build" class="${this.tab === 'build' ? 'on' : ''}">Byg</button></div><button class="bp-close" type="button">Luk</button></div>
      ${this.tab === 'build' ? this.renderBuild() : `
      <div class="bp-load"><div class="bp-meter"><i style="width:${Math.min(100, (kg / cap) * 100)}%"></i></div><span>${kg.toFixed(1)} / ${cap} kg · ${bag}${inv.burden > 1 ? ' · overlæsset' : inv.burden > SLOW_AT ? ' · tungt' : ''}</span></div>
      <div class="bp-cols">
        <section><h3>Indhold</h3><div class="bp-grid">${items.map(([id, n]) => `
          <div class="bp-item${id === inv.tool ? ' held' : ''}" data-id="${id}">${this.icon(id)}<b>${n}</b><span>${ITEMS[id].name}</span>
            <div class="bp-acts">${ITEMS[id].tool ? `<button data-act="hold">${id === inv.tool ? 'I hånden' : 'Hold'}</button>` : ''}${ITEMS[id].build ? '<button data-act="build">Byg</button>' : ''}${ITEMS[id].food ? '<button data-act="eat">Spis</button>' : ''}${id !== 'machete' ? '<button data-act="drop">Læg</button>' : ''}</div></div>`).join('')}</div></section>
        <section><h3>Lav</h3><div class="bp-recipes">${RECIPES.map((r, i) => `
          <div class="bp-rec${inv.canMake(r, near) ? '' : ' no'}">${this.icon(r.id)}<div><b>${ITEMS[r.id].name}</b><small>${r.note}${r.station && !near.has(r.station) ? ' — stå ved et bål' : ''}</small>
            <div class="bp-cost">${Object.entries(r.cost).map(([id, n]) => `<span class="${inv.count(id) >= n ? 'ok' : ''}">${this.icon(id)}${inv.count(id)}/${n}</span>`).join('')}</div></div>
            <button data-make="${i}" ${inv.canMake(r, near) ? '' : 'disabled'}>Lav</button></div>`).join('')}</div></section>
      </div>
      <p class="bp-foot">Du kan bære ${BASE_KG} kg selv; tasker giver mere. Over ${Math.round(SLOW_AT * 100)} % går du langsommere, over 100 % kan du ikke løbe. <button class="bp-reset" type="button">Start forfra</button></p>`}`;
    this.panel.querySelector('.bp-close').onclick = () => this.toggle(false);
    this.panel.querySelector('.bp-reset')?.addEventListener('click', () => { if (confirm('Slet det gemte spil og start forfra?')) this.g.reset(); });
    for (const t of this.panel.querySelectorAll('[data-tab]')) t.onclick = () => { this.tab = t.dataset.tab; this.render(); };
    for (const t of this.panel.querySelectorAll('[data-build]')) t.onclick = () => { this.toggle(false); this.g.startBuild(t.dataset.build); };
    this.panel.querySelector('.bp-tear')?.addEventListener('click', () => { this.toggle(false); this.g.build.tearDown(); this.g.toast(this.g.mobile ? 'Riv ned: sigt og tryk Riv' : 'Riv ned: sigt og klik · Esc stopper', false); });
    for (const b of this.panel.querySelectorAll('[data-make]')) b.onclick = () => {
      const r = RECIPES[+b.dataset.make];
      if (inv.make(r, this.g.near())) { sfx('pickup2', { vol: 0.6 }); this.g.toast(`Lavet: ${ITEMS[r.id].name}`, false, r.id); if (ITEMS[r.id].tool) { inv.tool = r.id; inv.changed(); } }
    };
    for (const b of this.panel.querySelectorAll('[data-act]')) b.onclick = () => {
      const id = b.closest('[data-id]').dataset.id;
      if (b.dataset.act === 'hold') { inv.tool = id; inv.changed(); }
      if (b.dataset.act === 'drop') { inv.remove(id, 1); this.g.dropPile({ [id]: 1 }); }
      if (b.dataset.act === 'eat') this.g.eat(id);
      if (b.dataset.act === 'build') { this.toggle(false); this.g.startPlacing(id); }
    };
  }

  update() {
    const g = this.g, b = g.build, t = g.target;
    const k = t ? KINDS[t.kind] : null;
    this.buildBar.hidden = !b.mode || this.open;
    if (b.mode) {
      const plan = b.ghost?.plan, m = b.marked;
      this.cross.classList.add('on');
      this.prompt.hidden = this.open;
      this.promptText.textContent = b.mode.tear ? (m ? `Riv ned: ${PIECE[m.id].name}` : 'Sigt på det, du vil rive ned') : plan?.ok ? `Byg: ${PIECE[b.mode.id].name}` : plan?.reason ?? 'Sigt på jorden';
      this.prompt.classList.toggle('bad', b.mode.id ? !plan?.ok : !m);
      this.promptKey.textContent = g.mobile ? '' : 'klik';
      this.bar.hidden = true;
      if (this.act) this.act.textContent = b.mode.tear ? 'Riv' : 'Byg';
      return;
    }
    this.prompt.classList.remove('bad');
    if (g.carcass) {
      this.cross.classList.add('on');
      this.prompt.hidden = this.open;
      this.promptText.textContent = `Flå: ${g.carcass.sp.name}`;
      this.promptKey.textContent = g.mobile ? '' : 'E';
      this.bar.hidden = true;
      if (this.act) this.act.textContent = 'Flå';
      return;
    }
    if (g.animal) {
      const c = g.animal, food = g.creatures.hasFood(c.sp);
      this.cross.classList.add('on');
      this.prompt.hidden = this.open;
      this.promptText.textContent = c.tamed ? `${c.name} — sadeltasker` : food ? `Giv ${c.sp.name.toLowerCase()}en mad (${c.trust}/${c.sp.tame.feeds})` : `${c.sp.name} — spiser ${c.sp.tame.food.map((f) => ITEMS[f].name.toLowerCase()).join(' / ')}`;
      this.promptKey.textContent = g.mobile ? '' : 'E';
      this.bar.hidden = c.tamed || !c.trust;
      if (!this.bar.hidden) this.barFill.style.width = `${(c.trust / c.sp.tame.feeds) * 100}%`;
      if (this.act) this.act.textContent = c.tamed ? 'Tasker' : 'Fodr';
      return;
    }
    const u = !g.pickTarget && b.useTarget;
    if (u) {
      this.cross.classList.add('on');
      this.prompt.hidden = this.open;
      this.promptText.textContent = u.id === 'chest' ? 'Åbn kisten' : u.id === 'bed' ? (b.spawn === u ? 'Din seng' : 'Gør sengen til dit hjem') : `${u.open ? 'Luk' : 'Åbn'} ${u.id === 'door' ? 'døren' : 'porten'}`;
      this.promptKey.textContent = g.mobile ? '' : 'E';
      this.bar.hidden = true;
      if (this.act) this.act.textContent = u.id === 'bed' ? 'Sov' : u.id === 'chest' || !u.open ? 'Åbn' : 'Luk';
      return;
    }
    this.cross.classList.toggle('on', !!t);
    this.prompt.hidden = !t || this.open;
    if (t) {
      const need = k.cut ? (t.key.includes('giant') && g.tool === 'axe' ? 14 : k.cut[g.tool]) : 0;
      let label = k.pick ? (t.kind === 'pile' ? `Saml bunken (${Object.values(t.items).reduce((a, b) => a + b, 0)})` : k.label) : need ? `Hug: ${k.label}` : `${k.label} — kræver en økse`;
      if (k.open && t.opened) label = 'Tom';
      this.promptText.textContent = label;
      this.promptKey.textContent = g.mobile ? '' : k.pick ? 'E' : need ? 'klik' : '';
      const show = need > 1 && !k.pick;
      this.bar.hidden = !show;
      if (show) this.barFill.style.width = `${((t.hits ?? 0) / need) * 100}%`;
    }
    if (this.act) this.act.textContent = g.pickTarget ? (KINDS[g.pickTarget.kind].open ? 'Åbn' : 'Saml') : 'Hug';
  }

  toast(text, warn = false, id = null) {
    const d = document.createElement('div');
    d.className = `toast${warn ? ' warn' : ''}`;
    d.innerHTML = `${id ? this.icon(id) : ''}<span>${text}</span>`;
    this.toasts.appendChild(d);
    while (this.toasts.children.length > 5) this.toasts.firstChild.remove();
    setTimeout(() => d.classList.add('out'), 1800);
    setTimeout(() => d.remove(), 2400);
  }
}

// Wood chips / leaf bits flying from a cut.
class Chips {
  constructor(scene) {
    const geo = new THREE.TetrahedronGeometry(0.05);
    this.mesh = new THREE.InstancedMesh(geo, new THREE.MeshLambertMaterial({ flatShading: true }), 120);
    this.mesh.count = 0;
    this.mesh.frustumCulled = false;
    this.mesh.name = 'chips';
    scene.add(this.mesh);
    this.list = [];
    this.m = new THREE.Matrix4();
    this.c = new THREE.Color();
    for (let i = 0; i < 120; i++) this.mesh.setColorAt(i, this.c.set(0xffffff));
  }

  burst(at, color, n) {
    for (let i = 0; i < n; i++) {
      if (this.list.length >= 120) this.list.shift();
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

// Item icons: each item's model rendered once to a small transparent picture.
function makeIcons(assets, pieces = []) {
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
    const list = [...Object.entries(ITEMS), ...pieces.map((p) => [`b:${p.id}`, { model: p.model, piece: true }])];
    for (const [id, it] of list) {
      if (!assets[it.model]) continue;
      const o = assets[it.model].scene.clone(true);
      o.traverse((m) => { if (m.isMesh) { m.material = m.material.clone(); m.material.flatShading = true; } });
      const box = new THREE.Box3().setFromObject(o);
      const c = box.getCenter(new THREE.Vector3()), s = box.getSize(new THREE.Vector3()).length();
      o.position.sub(c);
      const g = new THREE.Group();
      g.add(o);
      g.rotation.set(it.piece ? 0.45 : 0.35, -0.6, it.tool ? -0.8 : 0);
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
