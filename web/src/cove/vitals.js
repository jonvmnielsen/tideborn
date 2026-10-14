// The castaway's health (D-021). Bites and falls hurt; the screen edge flashes red and the bar
// (top left) drops. Health comes back slowly when nothing has hurt you for a while, faster when
// you eat. At 0 you black out: what you carried — except your tools and bag — stays in a pile
// where you fell, and you wake in your bed (or on the beach if you have none).
export class Vitals {
  constructor({ onDeath, onRespawn }) {
    this.max = 100;
    this.hp = 100;
    this.alive = true;
    this.since = 99; // seconds since you were last hurt
    this.onDeath = onDeath;
    this.onRespawn = onRespawn;
    const el = (tag, cls, parent = document.body, html = '') => { const e = document.createElement(tag); e.className = cls; e.innerHTML = html; parent.appendChild(e); return e; };
    this.bar = el('div', 'hp');
    this.fill = el('i', '', this.bar);
    this.label = el('span', '', this.bar);
    this.flash = el('div', 'hurt');
    this.death = el('div', 'death', document.body, '<h2>Du besvimede</h2><p>Det, du bar, ligger hvor du faldt.</p><button type="button">Vågn op</button>');
    this.death.hidden = true;
    this.death.querySelector('button').addEventListener('click', (e) => { e.stopPropagation(); this.respawn(); });
    this.render();
  }

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
    this.death.hidden = true;
    this.render();
    this.onRespawn?.();
  }

  update(dt) {
    this.since += dt;
    const o = parseFloat(this.flash.style.opacity || '0');
    if (o > 0) this.flash.style.opacity = String(Math.max(0, o - dt * 1.6));
    if (this.alive && this.since > 8 && this.hp < this.max) { this.hp = Math.min(this.max, this.hp + dt * 0.5); this.render(); }
  }

  render() {
    this.fill.style.width = `${(this.hp / this.max) * 100}%`;
    this.label.textContent = `${Math.ceil(this.hp)}`;
    this.bar.classList.toggle('low', this.hp < 30);
  }

  toJSON() { return { hp: Math.round(this.hp) }; }
  load_(d) { if (d?.hp) { this.hp = Math.max(20, d.hp); this.render(); } }
}
