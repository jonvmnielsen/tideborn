// DOM overlay: inventory chips, context action button, floating pickups, hints.
import * as THREE from 'three';

const ITEM_ICON = { wood: 'ui/wood.webp', stone: 'ui/stone.webp' };
const ITEM_NAME = { wood: 'Træ', stone: 'Sten' };

export class Hud {
  constructor() {
    this.el = document.getElementById('hud');
    this.counts = { wood: document.getElementById('cWood'), stone: document.getElementById('cStone') };
    this.action = document.getElementById('action');
    this.actionIcon = document.getElementById('actionIcon');
    this.actionLabel = document.getElementById('actionLabel');
    this.hintEl = document.getElementById('hint');
    this.savedEl = document.getElementById('saved');
    this.floaterRoot = document.getElementById('floaters');
    this.floaters = [];
    this.lastActionKey = null;
    this.v = new THREE.Vector3();
  }

  show() {
    this.el.hidden = false;
  }

  setInventory(inv, bumpItem) {
    for (const k of Object.keys(this.counts)) this.counts[k].textContent = inv[k] ?? 0;
    if (bumpItem) {
      const chip = this.el.querySelector(`.chip[data-item="${bumpItem}"]`);
      chip.classList.remove('bump');
      void chip.offsetWidth;
      chip.classList.add('bump');
    }
  }

  setAction(target, busy) {
    const key = target ? target.kind : busy ? 'busy' : 'none';
    if (key === this.lastActionKey) return;
    this.lastActionKey = key;
    if (target) {
      this.action.disabled = false;
      this.actionIcon.src = target.k.icon;
      this.actionLabel.textContent = target.k.label;
    } else if (!busy) {
      this.action.disabled = true;
      this.actionIcon.src = 'ui/tree.webp';
      this.actionLabel.textContent = 'Gå hen til et træ';
    }
  }

  hint(text) {
    if (!text) {
      this.hintEl.classList.remove('show');
      return;
    }
    this.hintEl.textContent = text;
    this.hintEl.classList.add('show');
  }

  flashSaved() {
    this.savedEl.textContent = 'Gemt';
    this.savedEl.classList.add('show');
    clearTimeout(this.savedTimer);
    this.savedTimer = setTimeout(() => this.savedEl.classList.remove('show'), 1200);
  }

  floater(pos, item, amount) {
    const el = document.createElement('div');
    el.className = 'floater';
    el.innerHTML = `<img src="${ITEM_ICON[item]}" alt=""><span>+${amount} ${ITEM_NAME[item]}</span>`;
    this.floaterRoot.appendChild(el);
    this.floaters.push({ el, pos: pos.clone(), t: 0, dur: 1.1, drift: (Math.random() - 0.5) * 30 });
  }

  update(dt, camera) {
    const w = window.innerWidth, h = window.innerHeight;
    for (let i = this.floaters.length - 1; i >= 0; i--) {
      const f = this.floaters[i];
      f.t += dt;
      const p = f.t / f.dur;
      if (p >= 1) {
        f.el.remove();
        this.floaters.splice(i, 1);
        continue;
      }
      this.v.copy(f.pos).project(camera);
      const x = (this.v.x * 0.5 + 0.5) * w + f.drift * p;
      const y = (-this.v.y * 0.5 + 0.5) * h - 70 * p - 20;
      const o = p < 0.7 ? 1 : 1 - (p - 0.7) / 0.3;
      f.el.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%) scale(${0.9 + 0.2 * Math.min(1, p * 5)})`;
      f.el.style.opacity = o;
    }
  }
}
