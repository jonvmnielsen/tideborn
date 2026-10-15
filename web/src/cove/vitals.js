// The castaway's health, stamina and level on screen (D-021, D-025). Bites, blows and falls hurt;
// the screen edge flashes red. Health comes back slowly when nothing has hurt you for a while,
// faster when you eat. At 0 you black out: what you carried — except tools and bag — stays in a
// pile where you fell, and you wake in your bed (or on the beach). Top left: health, stamina and
// the experience bar with your level (a "+" shows when you have points to spend: C / the panel).
export class Vitals {
  constructor({ character, onDeath, onRespawn, onOpenCharacter }) {
    this.char = character;
    this.hp = character.maxHp;
    this.alive = true;
    this.since = 99; // seconds since you were last hurt
    this.onDeath = onDeath;
    this.onRespawn = onRespawn;
    const el = (tag, cls, parent = document.body, html = '') => { const e = document.createElement(tag); e.className = cls; e.innerHTML = html; parent.appendChild(e); return e; };
    this.box = el('div', 'vitals');
    this.levelBtn = el('button', 'lvl', this.box);
    this.levelBtn.addEventListener('click', (e) => { e.stopPropagation(); onOpenCharacter?.(); });
    this.levelBtn.addEventListener('touchstart', (e) => { e.preventDefault(); e.stopPropagation(); onOpenCharacter?.(); }, { passive: false });
    const bars = el('div', 'bars', this.box);
    this.bar = el('div', 'hp', bars);
    this.fill = el('i', '', this.bar);
    this.label = el('span', '', this.bar);
    this.stam = el('div', 'stam', bars);
    this.stamFill = el('i', '', this.stam);
    this.xpBar = el('div', 'xp', bars);
    this.xpFill = el('i', '', this.xpBar);
    this.flash = el('div', 'hurt');
    this.death = el('div', 'death', document.body, '<h2>Du besvimede</h2><p>Det, du bar, ligger hvor du faldt.</p><button type="button">Vågn op</button>');
    this.death.hidden = true;
    this.death.querySelector('button').addEventListener('click', (e) => { e.stopPropagation(); this.respawn(); });
    character.listeners.push(() => this.render());
    this.render();
  }

  get max() { return this.char.maxHp; }

  hurt(n) {
    if (!this.alive) return;
    this.hp = Math.max(0, this.hp - n);
    this.since = 0;
    this.flash.style.opacity = String(Math.min(0.85, 0.35 + n / 30));
    this.render();
    if (this.hp <= 0) {
      this.alive = false;
      this.death.hidden = false;
      document.exitPointerLock?.();
      this.onDeath?.();
    }
  }

  heal(n) { if (this.alive) { this.hp = Math.min(this.max, this.hp + n); this.render(); } }

  respawn() {
    this.hp = this.max * 0.6;
    this.alive = true;
    this.since = 99;
    this.char.stamina = this.char.maxStamina;
    this.death.hidden = true;
    this.render();
    this.onRespawn?.();
  }

  update(dt) {
    this.since += dt;
    const o = parseFloat(this.flash.style.opacity || '0');
    if (o > 0) this.flash.style.opacity = String(Math.max(0, o - dt * 1.6));
    if (this.alive && this.since > 8 && this.hp < this.max) this.hp = Math.min(this.max, this.hp + dt * 0.5);
    this.render();
  }

  render() {
    const c = this.char;
    this.fill.style.width = `${(this.hp / this.max) * 100}%`;
    this.label.textContent = `${Math.ceil(this.hp)} / ${this.max}`;
    this.bar.classList.toggle('low', this.hp < this.max * 0.3);
    this.stamFill.style.width = `${(c.stamina / c.maxStamina) * 100}%`;
    this.stam.classList.toggle('empty', c.stamina < 5);
    this.xpFill.style.width = `${Math.min(100, (c.xp / (c.need?.() ?? 1)) * 100)}%`;
    const lv = `${c.level}${c.points ? '<b>+</b>' : ''}`;
    if (lv !== this.lv) { this.lv = lv; this.levelBtn.innerHTML = lv; }
  }

  toJSON() { return { hp: Math.round(this.hp) }; }
  load_(d) { if (d?.hp) { this.hp = Math.min(this.max, Math.max(20, d.hp)); this.render(); } }
}
