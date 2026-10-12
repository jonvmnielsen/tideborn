// What the castaway carries. Everything weighs something; without a bag you manage 8 kg in
// your arms and pockets. Bags raise that — a palm-leaf pouch and a bamboo basket can be made,
// a canvas backpack has to be found (washed up in a crate). The best bag you own is the one you
// wear. Tools (the machete, a stone axe) are carried too. The panel (Tab / I, or the bag button
// on a phone) shows the contents, the load and what you can make.

export const ITEMS = {
  wood: { name: 'Træ', model: 'item/wood', kg: 2 },
  palm_leaf: { name: 'Palmeblade', model: 'item/palm_leaf', kg: 0.4 },
  fiber: { name: 'Fibre', model: 'item/fiber', kg: 0.2 },
  bamboo: { name: 'Bambus', model: 'item/bamboo_poles', kg: 1.5 },
  stone: { name: 'Sten', model: 'item/stone', kg: 1.5 },
  coconut: { name: 'Kokosnødder', model: 'item/coconut', kg: 1 },
  banana: { name: 'Bananer', model: 'item/bananas', kg: 0.5 },
  rope: { name: 'Reb', model: 'item/rope', kg: 0.4 },
  machete: { name: 'Machete', model: 'props/machete', kg: 0.8, tool: 'machete' },
  stone_axe: { name: 'Stenøkse', model: 'props/stone_axe', kg: 1.6, tool: 'axe' },
  bag_leaf: { name: 'Palmebladstaske', model: 'item/bag_leaf', kg: 0.4, bag: 6 },
  bag_basket: { name: 'Bambuskurv', model: 'item/bag_basket', kg: 1.5, bag: 14 },
  bag_canvas: { name: 'Lærredsrygsæk', model: 'item/bag_canvas', kg: 1, bag: 24 },
  lean_to: { name: 'Læ (byggesæt)', model: 'build/lean_to', kg: 6, build: true },
};

export const RECIPES = [
  { id: 'rope', n: 1, cost: { fiber: 4 }, note: 'Snoet af plantefibre' },
  { id: 'stone_axe', n: 1, cost: { stone: 1, wood: 1, rope: 1 }, note: 'Fælder de store træer' },
  { id: 'bag_leaf', n: 1, cost: { palm_leaf: 6, fiber: 4 }, note: '+6 kg at bære' },
  { id: 'bag_basket', n: 1, cost: { bamboo: 4, fiber: 6, rope: 1 }, note: '+14 kg at bære' },
  { id: 'lean_to', n: 1, cost: { bamboo: 6, palm_leaf: 10, rope: 2 }, note: 'Et læ at sove under' },
];

export const BASE_KG = 8;

export class Inventory {
  constructor() {
    this.items = { machete: 1 };
    this.tool = 'machete';
    this.listeners = [];
  }

  count(id) { return this.items[id] ?? 0; }

  get bag() {
    let best = null;
    for (const id of Object.keys(this.items)) if (ITEMS[id]?.bag && this.count(id) > 0 && (!best || ITEMS[id].bag > ITEMS[best].bag)) best = id;
    return best;
  }

  get capacity() { return BASE_KG + (this.bag ? ITEMS[this.bag].bag : 0); }

  get load() {
    let kg = 0;
    for (const [id, n] of Object.entries(this.items)) kg += (ITEMS[id]?.kg ?? 0) * n;
    return kg;
  }

  // How many of `id` still fit.
  room(id) {
    const kg = ITEMS[id].kg;
    return kg > 0 ? Math.max(0, Math.floor((this.capacity - this.load + 1e-6) / kg)) : Infinity;
  }

  // Adds what fits; returns what didn't.
  add(items) {
    const left = {};
    for (const [id, n] of Object.entries(items)) {
      const take = Math.min(n, this.room(id));
      if (take > 0) this.items[id] = this.count(id) + take;
      if (n - take > 0) left[id] = n - take;
    }
    this.changed();
    return left;
  }

  remove(id, n = 1) {
    this.items[id] = Math.max(0, this.count(id) - n);
    if (!this.items[id]) delete this.items[id];
    if (id === this.tool && !this.count(id)) this.tool = this.count('machete') ? 'machete' : null;
    this.changed();
  }

  canMake(r) { return Object.entries(r.cost).every(([id, n]) => this.count(id) >= n); }

  make(r) {
    if (!this.canMake(r)) return false;
    for (const [id, n] of Object.entries(r.cost)) this.items[id] -= n;
    for (const id of Object.keys(r.cost)) if (!this.items[id]) delete this.items[id];
    // Made things are never refused for weight: you're holding it, you just can't pick up more.
    this.items[r.id] = this.count(r.id) + r.n;
    this.changed();
    return true;
  }

  changed() { for (const f of this.listeners) f(); }

  toJSON() { return { items: this.items, tool: this.tool }; }

  load_(data) {
    if (!data) return;
    this.items = { ...data.items };
    this.tool = data.tool ?? 'machete';
    this.changed();
  }
}
