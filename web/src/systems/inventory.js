// Item counts. Used for the player and for every storage chest.
import { ITEMS } from '../data/items.js';

export class Inventory {
  constructor(items = {}) {
    this.items = { ...items };
    this.listeners = new Set();
  }
  count(id) {
    return this.items[id] ?? 0;
  }
  has(id, n = 1) {
    return this.count(id) >= n;
  }
  hasTool(tool) {
    return Object.keys(this.items).some((id) => this.items[id] > 0 && ITEMS[id]?.tool === tool);
  }
  canAfford(cost) {
    return Object.entries(cost).every(([id, n]) => this.count(id) >= n);
  }
  add(id, n = 1) {
    const max = ITEMS[id]?.stack ?? 99;
    const before = this.count(id);
    // Tools never stack past one; resources cap at a generous limit.
    const after = ITEMS[id]?.tags?.includes('tool') ? Math.min(1, before + n) : Math.min(max * 9, before + n);
    this.items[id] = after;
    this.emit(id);
    return after - before;
  }
  remove(id, n = 1) {
    if (this.count(id) < n) return false;
    this.items[id] -= n;
    if (this.items[id] <= 0) delete this.items[id];
    this.emit(id);
    return true;
  }
  pay(cost) {
    if (!this.canAfford(cost)) return false;
    for (const [id, n] of Object.entries(cost)) this.remove(id, n);
    return true;
  }
  list() {
    return Object.entries(this.items).filter(([, n]) => n > 0);
  }
  onChange(fn) {
    this.listeners.add(fn);
  }
  emit(id) {
    for (const fn of this.listeners) fn(id);
  }
  serialize() {
    return { ...this.items };
  }
}
