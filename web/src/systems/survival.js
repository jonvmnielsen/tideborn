// Light survival: hunger drains slowly, an empty belly hurts, a full one heals.
export class Survival {
  constructor() {
    this.health = 100;
    this.hunger = 100;
  }
  update(dt, sleeping) {
    this.hunger = Math.max(0, this.hunger - dt * (sleeping ? 0.04 : 0.1));
    if (this.hunger <= 0) this.health = Math.max(0, this.health - dt * 0.8);
    else if (this.hunger > 40) this.health = Math.min(100, this.health + dt * (sleeping ? 1.5 : 0.4));
  }
  eat(amount) {
    this.hunger = Math.min(100, this.hunger + amount);
  }
  get dead() {
    return this.health <= 0;
  }
  serialize() {
    return { h: Math.round(this.health), f: Math.round(this.hunger) };
  }
  restore(s) {
    if (!s) return;
    this.health = Math.max(20, s.h ?? 100);
    this.hunger = s.f ?? 100;
  }
}
