// What the castaway carries (D-020, D-025): counted in units, not kilograms. You carry 100 units,
// bags and the Bæreevne stat add more. Nothing is refused: above 60 % of what you can carry you
// walk slower, above 100 % you trudge and can't run. A palm-leaf pouch, a bamboo basket and a hide
// pack can be made; a canvas backpack has to be found (washed up in a crate). The best bag you own
// is the one you wear. The panel (Tab / I, or the bag button on a phone) shows contents and recipes.

export const ITEMS = {
  wood: { name: 'Træ', model: 'item/wood', w: 1 },
  palm_leaf: { name: 'Palmeblade', model: 'item/palm_leaf', w: 0.2 },
  fiber: { name: 'Fibre', model: 'item/fiber', w: 0.1 },
  bamboo: { name: 'Bambus', model: 'item/bamboo_poles', w: 1 },
  stone: { name: 'Sten', model: 'item/stone', w: 1 },
  coconut: { name: 'Kokosnødder', model: 'item/coconut', w: 0.5, food: 12 },
  banana: { name: 'Bananer', model: 'item/bananas', w: 0.2, food: 8 },
  meat: { name: 'Råt kød', model: 'item/meat', w: 0.5, food: 6 },
  meat_cooked: { name: 'Stegt kød', model: 'item/meat_cooked', w: 0.5, food: 30 },
  hide: { name: 'Skind', model: 'item/hide', w: 1 },
  rope: { name: 'Reb', model: 'item/rope', w: 0.2 },
  machete: { name: 'Machete', model: 'props/machete', w: 3, tool: 'machete' },
  stone_axe: { name: 'Stenøkse', model: 'props/stone_axe', w: 4, tool: 'axe' },
  club: { name: 'Kølle', model: 'props/club', w: 4, tool: 'club' },
  bag_leaf: { name: 'Palmebladstaske', model: 'item/bag_leaf', w: 1, bag: 30 },
  bag_basket: { name: 'Bambuskurv', model: 'item/bag_basket', w: 2, bag: 60 },
  bag_hide: { name: 'Skindrygsæk', model: 'item/bag_hide', w: 2, bag: 90 },
  bag_canvas: { name: 'Lærredsrygsæk', model: 'item/bag_canvas', w: 2, bag: 120 },
  lean_to: { name: 'Læ (byggesæt)', model: 'build/lean_to', w: 8, build: true }, // old saves; the lean-to is now built from the Byg tab
};

export const RECIPES = [
  { id: 'rope', n: 1, cost: { fiber: 4 }, note: 'Snoet af plantefibre' },
  { id: 'stone_axe', n: 1, cost: { stone: 1, wood: 1, rope: 1 }, note: 'Fælder de store træer' },
  { id: 'club', n: 1, cost: { wood: 3, stone: 1, rope: 1 }, note: 'Slår folk bevidstløse i stedet for at dræbe' },
  { id: 'bag_leaf', n: 1, cost: { palm_leaf: 6, fiber: 4 }, note: '+30 units' },
  { id: 'bag_basket', n: 1, cost: { bamboo: 4, fiber: 6, rope: 1 }, note: '+60 units' },
  { id: 'bag_hide', n: 1, cost: { hide: 4, rope: 2, fiber: 4 }, note: '+90 units' },
  { id: 'meat_cooked', n: 1, cost: { meat: 1 }, station: 'campfire', note: 'Steg det ved et bål' },
];

export const BASE_UNITS = 100;
export const SLOW_AT = 0.6; // share of capacity where walking starts to slow

export class Inventory {
  constructor() {
    this.bonus = () => 0; // extra units from the character's Bæreevne
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

  get capacity() { return BASE_UNITS + this.bonus() + (this.bag ? ITEMS[this.bag].bag : 0); }

  get load() {
    let u = 0;
    for (const [id, n] of Object.entries(this.items)) u += (ITEMS[id]?.w ?? 0) * n;
    return u;
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

  // `near` = the stations you stand by (e.g. 'campfire').
  canMake(r, near = new Set()) { return (!r.station || near.has(r.station)) && Object.entries(r.cost).every(([id, n]) => this.count(id) >= n); }

  make(r, near) {
    if (!this.canMake(r, near)) return false;
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
