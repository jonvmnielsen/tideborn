// What the castaway carries (D-020, after ARK): you can always pick things up — nothing is
// refused. Resources are light (a log 0.5 kg, a handful of fibre 0.01 kg) and you carry 100 kg
// before it starts to tell; above 60 % of what you can carry you walk slower, above 100 % you
// trudge and can't run. Bags add to what you carry — a palm-leaf pouch and a bamboo basket can be
// made, a canvas backpack has to be found (washed up in a crate). The best bag you own is the one
// you wear. The panel (Tab / I, or the bag button on a phone) shows contents, load and recipes.

export const ITEMS = {
  wood: { name: 'Træ', model: 'item/wood', kg: 0.5 },
  palm_leaf: { name: 'Palmeblade', model: 'item/palm_leaf', kg: 0.05 },
  fiber: { name: 'Fibre', model: 'item/fiber', kg: 0.01 },
  bamboo: { name: 'Bambus', model: 'item/bamboo_poles', kg: 0.5 },
  stone: { name: 'Sten', model: 'item/stone', kg: 0.5 },
  coconut: { name: 'Kokosnødder', model: 'item/coconut', kg: 0.25 },
  banana: { name: 'Bananer', model: 'item/bananas', kg: 0.1 },
  rope: { name: 'Reb', model: 'item/rope', kg: 0.05 },
  machete: { name: 'Machete', model: 'props/machete', kg: 1, tool: 'machete' },
  stone_axe: { name: 'Stenøkse', model: 'props/stone_axe', kg: 2, tool: 'axe' },
  bag_leaf: { name: 'Palmebladstaske', model: 'item/bag_leaf', kg: 0.5, bag: 30 },
  bag_basket: { name: 'Bambuskurv', model: 'item/bag_basket', kg: 1.5, bag: 75 },
  bag_canvas: { name: 'Lærredsrygsæk', model: 'item/bag_canvas', kg: 1, bag: 150 },
  lean_to: { name: 'Læ (byggesæt)', model: 'build/lean_to', kg: 4, build: true }, // old saves; the lean-to is now built from the Byg tab
};

export const RECIPES = [
  { id: 'rope', n: 1, cost: { fiber: 4 }, note: 'Snoet af plantefibre' },
  { id: 'stone_axe', n: 1, cost: { stone: 1, wood: 1, rope: 1 }, note: 'Fælder de store træer' },
  { id: 'bag_leaf', n: 1, cost: { palm_leaf: 6, fiber: 4 }, note: '+30 kg at bære' },
  { id: 'bag_basket', n: 1, cost: { bamboo: 4, fiber: 6, rope: 1 }, note: '+75 kg at bære' },
];

export const BASE_KG = 100;
export const SLOW_AT = 0.6; // share of capacity where walking starts to slow

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

  // How heavily laden you are: 0 = free, 1 = at capacity, above 1 = overloaded.
  get burden() { return this.load / this.capacity; }

  // Walking speed factor from the load: full speed up to SLOW_AT, then down to 60 % at capacity;
  // overloaded you trudge at 35 % and can't run.
  get pace() {
    const b = this.burden;
    if (b <= SLOW_AT) return 1;
    if (b <= 1) return 1 - 0.4 * (b - SLOW_AT) / (1 - SLOW_AT);
    return 0.35;
  }

  // Everything is taken (returns what didn't fit — always nothing now, kept for callers).
  add(items) {
    for (const [id, n] of Object.entries(items)) if (n > 0) this.items[id] = this.count(id) + n;
    this.changed();
    return {};
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
