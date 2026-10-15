// The castaway's progression (D-025). Everything you do gives experience: gathering, hunting,
// fighting, knocking people out and taking them in, building, crafting, taming. Each level gives
// a point to spend on one of six stats:
//   Liv          +10 max health
//   Udholdenhed  +10 max stamina (sprinting and swinging use stamina)
//   Bæreevne     +10 units you can carry
//   Slagkraft    +5 % melee damage
//   Fart         +2.5 % walking and running speed
//   Samling      +6 % yield when gathering
// The bars top left show health, stamina and experience with your level.
export const STATS = {
  health: { label: 'Liv', per: '+10 liv', icon: '❤' },
  stamina: { label: 'Udholdenhed', per: '+10 udholdenhed', icon: '⚡' },
  carry: { label: 'Bæreevne', per: '+10 units', icon: '⛁' },
  melee: { label: 'Slagkraft', per: '+5 % skade', icon: '⚔' },
  speed: { label: 'Fart', per: '+2,5 % fart', icon: '➶' },
  gather: { label: 'Samling', per: '+6 % udbytte', icon: '✿' },
};

// Experience for the next level: grows steadily, so early levels come quickly.
export const need = (level) => Math.round(40 + 30 * Math.pow(level - 1, 1.45));

export class Character {
  constructor({ onLevel } = {}) {
    this.level = 1;
    this.xp = 0;
    this.points = 0;
    this.stats = Object.fromEntries(Object.keys(STATS).map((k) => [k, 0]));
    this.stamina = this.maxStamina;
    this.rest = 0; // seconds since stamina was last used
    this.onLevel = onLevel;
    this.listeners = [];
  }

  need() { return need(this.level); }

  get maxHp() { return 100 + 10 * this.stats.health; }
  get maxStamina() { return 100 + 10 * this.stats.stamina; }
  get carryBonus() { return 10 * this.stats.carry; }
  get meleeMul() { return 1 + 0.05 * this.stats.melee; }
  get speedMul() { return 1 + 0.025 * this.stats.speed; }
  get gatherMul() { return 1 + 0.06 * this.stats.gather; }

  // Gathered amounts get the gathering bonus; the fraction is a chance of one more.
  boost(items) {
    const out = {};
    for (const [k, n] of Object.entries(items)) { const v = n * this.gatherMul; out[k] = Math.floor(v) + (Math.random() < v % 1 ? 1 : 0); }
    return out;
  }

  gain(xp) {
    if (!(xp > 0)) return;
    this.xp += xp;
    let up = 0;
    while (this.xp >= need(this.level)) { this.xp -= need(this.level); this.level += 1; this.points += 1; up += 1; }
    if (up) this.onLevel?.(this.level, up);
    this.changed();
  }

  spend(stat) {
    if (this.points < 1 || !(stat in this.stats)) return false;
    this.points -= 1;
    this.stats[stat] += 1;
    if (stat === 'stamina') this.stamina += 10;
    this.changed();
    return true;
  }

  // Stamina: use returns whether there was enough (a swing still happens when tired, just weaker).
  use(n) {
    this.rest = 0;
    const had = this.stamina >= n;
    this.stamina = Math.max(0, this.stamina - n);
    return had;
  }

  update(dt, sprinting) {
    if (sprinting) { this.stamina = Math.max(0, this.stamina - 11 * dt); this.rest = 0; }
    else this.rest += dt;
    if (this.rest > 0.8) this.stamina = Math.min(this.maxStamina, this.stamina + 22 * dt);
  }

  changed() { for (const f of this.listeners) f(); }

  toJSON() { return { level: this.level, xp: Math.round(this.xp), points: this.points, stats: this.stats }; }

  load_(d) {
    if (!d) return;
    Object.assign(this, { level: d.level ?? 1, xp: d.xp ?? 0, points: d.points ?? 0 });
    Object.assign(this.stats, d.stats ?? {});
    this.stamina = this.maxStamina;
    this.changed();
  }
}
