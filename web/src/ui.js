// DOM overlay: meters, clock, context action, build palette, inventory/crafting sheet.
import * as THREE from 'three';
import { ITEMS, itemName, itemIcon } from './data/items.js';
import { RECIPES } from './data/recipes.js';
import { PIECES } from './data/build.js';

const $ = (id) => document.getElementById(id);

export class UI {
  constructor() {
    this.hud = $('hud');
    this.action = $('action');
    this.actionIcon = $('actionIcon');
    this.actionLabel = $('actionLabel');
    this.toastEl = $('toast');
    this.objectiveEl = $('objective');
    this.palette = $('palette');
    this.sheet = $('sheet');
    this.scrim = $('sheetScrim');
    this.floaterRoot = $('floaters');
    this.floaters = [];
    this.v = new THREE.Vector3();
    this.lastAction = '';
    this.handlers = {};
    $('sheetClose').addEventListener('click', () => this.closeSheet());
    this.scrim.addEventListener('click', () => this.closeSheet());
    for (const id of ['invBtn', 'buildBtn', 'eatBtn', 'rotateBtn', 'removeBtn', 'upBtn', 'downBtn']) {
      $(id).addEventListener('click', (e) => { e.stopPropagation(); this.handlers[id]?.(); });
      $(id).addEventListener('pointerdown', (e) => e.stopPropagation());
    }
    // Action button: press + hold.
    this.actionHeld = false;
    this.actionPressed = false;
    this.action.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.action.setPointerCapture?.(e.pointerId);
      this.press();
    });
    const up = () => this.release();
    this.action.addEventListener('pointerup', up);
    this.action.addEventListener('pointercancel', up);
    this.action.addEventListener('lostpointercapture', up);
  }

  on(name, fn) { this.handlers[name] = fn; }

  show() { this.hud.hidden = false; }

  press() {
    if (this.action.disabled) return;
    this.actionHeld = true;
    this.actionPressed = true;
    this.action.classList.add('pressed');
  }
  release() {
    this.actionHeld = false;
    this.action.classList.remove('pressed');
  }
  consumePress() {
    const p = this.actionPressed;
    this.actionPressed = false;
    return p;
  }

  setMeters(health, hunger, hasFood) {
    $('hpFill').style.width = `${health}%`;
    $('foodFill').style.width = `${hunger}%`;
    $('hpFill').classList.toggle('low', health < 30);
    $('foodFill').classList.toggle('low', hunger < 20);
    $('eatBtn').hidden = !(hasFood && hunger < 75);
  }

  setClock(day, clock, night) {
    const t = `Dag ${day} · ${clock}${night ? ' · nat' : ''}`;
    if ($('clock').textContent !== t) $('clock').textContent = t;
  }

  // a = { label, icon, enabled, style: ''|'locked'|'build' }
  setAction(a) {
    const key = a ? `${a.label}|${a.icon}|${a.enabled}|${a.style}` : 'none';
    if (key === this.lastAction) return;
    this.lastAction = key;
    if (!a) {
      this.action.disabled = true;
      this.actionLabel.textContent = '—';
      this.actionIcon.style.visibility = 'hidden';
      this.action.className = 'action';
      return;
    }
    this.action.disabled = !a.enabled;
    this.actionLabel.textContent = a.label;
    this.actionIcon.src = a.icon;
    this.actionIcon.style.visibility = '';
    this.action.className = `action ${a.style ?? ''}`;
  }

  toast(text, ms = 2200) {
    this.toastEl.textContent = text;
    this.toastEl.classList.add('show');
    clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => this.toastEl.classList.remove('show'), ms);
  }

  objective(text) {
    if (this.objectiveEl.textContent !== text) this.objectiveEl.textContent = text;
  }

  setBuildMode(on) {
    this.hud.classList.toggle('building', on);
    $('buildBtn').classList.toggle('on', on);
    $('buildTools').hidden = !on;
    this.palette.hidden = !on;
  }

  setLevelLabel(text) {
    const el = $('levelLabel');
    if (el.textContent !== text) el.textContent = text;
  }

  setRemoveMode(on) {
    $('removeBtn').classList.toggle('on', on);
  }

  renderPalette(selected, inv) {
    this.palette.textContent = '';
    for (const p of PIECES) {
      const b = document.createElement('button');
      b.type = 'button';
      const afford = inv.canAfford(p.cost);
      b.className = `piece${p.id === selected ? ' sel' : ''}${afford ? '' : ' poor'}`;
      b.innerHTML = `<img src="${p.icon}" alt=""><span class="pn"></span><span class="pc"></span>`;
      b.querySelector('.pn').textContent = p.name;
      b.querySelector('.pc').textContent = Object.entries(p.cost).map(([id, n]) => `${n} ${itemName(id).toLowerCase()}`).join(' · ');
      b.addEventListener('pointerdown', (e) => e.stopPropagation());
      b.addEventListener('click', () => this.handlers.pickPiece?.(p.id));
      this.palette.appendChild(b);
    }
  }

  // --- Sheet --------------------------------------------------------------------
  get sheetOpen() { return !this.sheet.hidden; }

  openSheet(inv, chest = null) {
    this.chest = chest;
    this.inv = inv;
    $('sheetTitle').textContent = chest ? 'Kiste' : 'Rygsæk';
    $('craftCol').hidden = !!chest;
    $('chestCol').hidden = !chest;
    this.sheet.hidden = false;
    this.scrim.hidden = false;
    this.renderSheet();
  }

  closeSheet() {
    this.sheet.hidden = true;
    this.scrim.hidden = true;
    this.chest = null;
    this.handlers.sheetClosed?.();
  }

  renderSheet() {
    if (this.sheet.hidden) return;
    const inv = this.inv, chest = this.chest;
    const itemsEl = $('invItems');
    itemsEl.textContent = '';
    const list = inv.list();
    if (!list.length) itemsEl.innerHTML = '<p class="empty">Tom. Saml drivtømmer, sten og nælder ved stranden.</p>';
    for (const [id, n] of list) {
      const el = this.itemCard(id, n);
      if (chest) el.appendChild(this.btn('Læg i', () => { const k = inv.count(id); inv.remove(id, k); chest.add(id, k); this.renderSheet(); this.handlers.changed?.(); }));
      else if (ITEMS[id]?.food) el.appendChild(this.btn('Spis', () => this.handlers.eat?.()));
      itemsEl.appendChild(el);
    }
    if (chest) {
      const ce = $('chestItems');
      ce.textContent = '';
      const cl = chest.list();
      if (!cl.length) ce.innerHTML = '<p class="empty">Kisten er tom.</p>';
      for (const [id, n] of cl) {
        const el = this.itemCard(id, n);
        el.appendChild(this.btn('Tag', () => { const k = chest.count(id); chest.remove(id, k); inv.add(id, k); this.renderSheet(); this.handlers.changed?.(); }, true));
        ce.appendChild(el);
      }
      return;
    }
    const rEl = $('recipes');
    rEl.textContent = '';
    for (const r of RECIPES) {
      const outId = Object.keys(r.out)[0];
      const owned = ITEMS[outId]?.tags.includes('tool') && inv.has(outId);
      const locked = r.needs && !inv.has(r.needs);
      const row = document.createElement('div');
      row.className = `recipe${owned ? ' done' : ''}`;
      row.innerHTML = `<img src="${itemIcon(outId)}" alt=""><div><div class="rn"></div><div class="rt"></div><div class="cost"></div></div>`;
      row.querySelector('.rn').textContent = itemName(outId) + (owned ? ' ✓' : '');
      row.querySelector('.rt').textContent = locked ? `Kræver ${itemName(r.needs).toLowerCase()} først.` : r.text;
      const cost = row.querySelector('.cost');
      for (const [id, n] of Object.entries(r.cost)) {
        const s = document.createElement('span');
        if (inv.count(id) < n) s.className = 'short';
        s.innerHTML = `<img src="${itemIcon(id)}" alt="">${inv.count(id)}/${n}`;
        cost.appendChild(s);
      }
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = owned ? 'Har' : 'Lav';
      b.disabled = owned || locked || !inv.canAfford(r.cost);
      b.addEventListener('click', () => this.handlers.craft?.(r));
      row.appendChild(b);
      rEl.appendChild(row);
    }
  }

  itemCard(id, n) {
    const el = document.createElement('div');
    el.className = 'item';
    el.innerHTML = `<img src="${itemIcon(id)}" alt=""><span class="icount">${n}</span><span class="iname"></span>`;
    el.querySelector('.iname').textContent = itemName(id);
    return el;
  }

  btn(text, fn, alt = false) {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = text;
    if (alt) b.className = 'alt';
    b.addEventListener('click', fn);
    return b;
  }

  // --- Floating pickups --------------------------------------------------------------
  floater(pos, item, amount) {
    const el = document.createElement('div');
    el.className = 'floater';
    el.innerHTML = `<img src="${itemIcon(item)}" alt=""><span>+${amount} ${itemName(item)}</span>`;
    this.floaterRoot.appendChild(el);
    this.floaters.push({ el, pos: pos.clone(), t: 0, dur: 1.1, drift: (Math.random() - 0.5) * 30 });
  }

  update(dt, camera) {
    const w = window.innerWidth, h = window.innerHeight;
    for (let i = this.floaters.length - 1; i >= 0; i--) {
      const f = this.floaters[i];
      f.t += dt;
      const p = f.t / f.dur;
      if (p >= 1) { f.el.remove(); this.floaters.splice(i, 1); continue; }
      this.v.copy(f.pos).project(camera);
      const x = (this.v.x * 0.5 + 0.5) * w + f.drift * p;
      const y = (-this.v.y * 0.5 + 0.5) * h - 70 * p - 20;
      f.el.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
      f.el.style.opacity = p < 0.7 ? 1 : 1 - (p - 0.7) / 0.3;
    }
  }

  overlay(text, dark) {
    const o = $('overlay');
    o.hidden = !text && !dark;
    o.classList.toggle('dark', !!dark);
    $('overlayText').textContent = text ?? '';
  }
}
