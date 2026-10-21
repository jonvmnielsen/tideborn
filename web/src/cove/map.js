// The island map (Design Brief §2, P0 exploration: "what's over that ridge?"). M — or the map
// button on phones — opens it. It starts covered: the ground you have seen fills in as you
// move (farther from high ground), so the map is a record of where you have been and what is
// still unknown. It shows you (an arrow), your bed, fires, tame animals, allies and trælle, and
// the places you have found. The explored area is saved.
import { SIZE, VOLCANO } from './island.js';

const RES = 256;   // map pixels across the whole square
const FOG = 190;   // fog cells across (4 m each)
const CELL = SIZE / FOG;

export class IslandMap {
  constructor({ island, mobile }) {
    this.island = island;
    this.mobile = mobile;
    this.seen = new Uint8Array(FOG * FOG);
    this.t = 0;
    this.places = []; // { name, x, z, r } — named on the map once you have been within r metres
    this.el = document.createElement('div');
    this.el.className = 'mapview';
    this.el.hidden = true;
    this.el.innerHTML = '<div class="map-in"><canvas></canvas><div class="map-head"><b>Øen</b><span></span><button type="button">Luk</button></div></div>';
    document.body.appendChild(this.el);
    this.canvas = this.el.querySelector('canvas');
    this.info = this.el.querySelector('.map-head span');
    const close = (e) => { e.stopPropagation(); e.preventDefault(); this.toggle(false); };
    this.el.querySelector('button').addEventListener('click', close);
    this.el.addEventListener('click', close);
    this.el.addEventListener('touchstart', close, { passive: false });
  }

  get open() { return !this.el.hidden; }

  toggle(on = !this.open) {
    this.el.hidden = !on;
    if (on) { this.paintBase(); this.draw(); }
    this.onToggle?.(on);
  }

  // Reveal what you can see from where you stand.
  update(dt, p) {
    this.t += dt;
    if (this.t < 0.4) { if (this.open && (this.drawT = (this.drawT ?? 0) + dt) > 0.25) { this.drawT = 0; this.draw(); } return; }
    this.t = 0;
    const h = Math.max(0, this.island.heightAt(p.x, p.z));
    const r = Math.min(140, 42 + h * 0.9);
    const cx = (p.x + SIZE / 2) / CELL, cz = (p.z + SIZE / 2) / CELL, rc = r / CELL;
    let fresh = 0;
    for (let j = Math.max(0, Math.floor(cz - rc)); j <= Math.min(FOG - 1, Math.ceil(cz + rc)); j++) {
      for (let i = Math.max(0, Math.floor(cx - rc)); i <= Math.min(FOG - 1, Math.ceil(cx + rc)); i++) {
        if ((i - cx) ** 2 + (j - cz) ** 2 > rc * rc || this.seen[j * FOG + i]) continue;
        this.seen[j * FOG + i] = 1;
        fresh++;
      }
    }
    if (fresh) { this.dirty = true; this.changed = true; }
    for (const pl of this.places) if (!pl.found && Math.hypot(p.x - pl.x, p.z - pl.z) < (pl.r ?? 40)) { pl.found = true; this.changed = true; this.dirty = true; this.onFound?.(pl); }
    if (this.open) this.draw();
  }

  seenAt(x, z) {
    const i = Math.floor((x + SIZE / 2) / CELL), j = Math.floor((z + SIZE / 2) / CELL);
    return i >= 0 && j >= 0 && i < FOG && j < FOG && this.seen[j * FOG + i] === 1;
  }

  // The land, painted once: the island's own ground colours, shaded by slope like a relief map.
  paintBase() {
    if (this.base) return;
    const I = this.island, c = document.createElement('canvas');
    c.width = c.height = RES;
    const g = c.getContext('2d'), img = g.createImageData(RES, RES), d = img.data;
    const m = SIZE / RES;
    for (let j = 0; j < RES; j++) for (let i = 0; i < RES; i++) {
      const x = -SIZE / 2 + (i + 0.5) * m, z = -SIZE / 2 + (j + 0.5) * m;
      const h = I.heightAt(x, z);
      let r, gg, b;
      if (h < -0.3) {
        const k = Math.min(1, -h / 14);
        r = 0.36 - 0.24 * k; gg = 0.72 - 0.38 * k; b = 0.78 - 0.2 * k;
      } else {
        const col = I.colourAt(x, z, h, I.slopeAt(x, z), 0, 0).c;
        // Light from the north-west.
        const sh = (I.heightAt(x - 2, z - 2) - I.heightAt(x + 2, z + 2)) * 0.06;
        const k = 1 + Math.max(-0.35, Math.min(0.35, sh));
        r = col.r * k; gg = col.g * k; b = col.b * k;
      }
      const o = (j * RES + i) * 4;
      d[o] = Math.min(255, Math.pow(r, 1 / 2.2) * 255); d[o + 1] = Math.min(255, Math.pow(gg, 1 / 2.2) * 255); d[o + 2] = Math.min(255, Math.pow(b, 1 / 2.2) * 255); d[o + 3] = 255;
    }
    g.putImageData(img, 0, 0);
    this.base = c;
    this.fog = document.createElement('canvas');
    this.fog.width = this.fog.height = FOG;
    this.dirty = true;
  }

  draw() {
    if (!this.base) return;
    const s = this.size ?? 0;
    const want = Math.floor(Math.min(innerWidth * 0.94, innerHeight * 0.84));
    const dpr = Math.min(2, devicePixelRatio || 1);
    if (want !== s) { this.size = want; this.canvas.width = this.canvas.height = want * dpr; this.canvas.style.width = this.canvas.style.height = `${want}px`; }
    const W = this.canvas.width, g = this.canvas.getContext('2d');
    if (this.dirty) {
      // Unknown ground: a dark, papery cover with soft edges.
      const f = this.fog.getContext('2d'), img = f.createImageData(FOG, FOG);
      for (let k = 0; k < FOG * FOG; k++) { const o = k * 4; img.data[o] = 28; img.data[o + 1] = 32; img.data[o + 2] = 30; img.data[o + 3] = this.seen[k] ? 0 : 255; }
      f.putImageData(img, 0, 0);
      this.dirty = false;
    }
    g.imageSmoothingEnabled = true;
    g.save();
    g.filter = `blur(${W / 700}px)`; // soften the ground's speckle into map-like patches
    g.drawImage(this.base, 0, 0, W, W);
    g.restore();
    g.save();
    g.filter = `blur(${W / 140}px)`;
    g.drawImage(this.fog, 0, 0, W, W);
    g.restore();
    const at = (x, z) => [((x + SIZE / 2) / SIZE) * W, ((z + SIZE / 2) / SIZE) * W];
    const u = W / 512;
    g.font = `${Math.round(13 * u)}px system-ui, sans-serif`;
    g.textAlign = 'center';
    const label = (text, x, y, col = '#f3ead2') => {
      g.lineWidth = 3 * u; g.strokeStyle = 'rgba(0,0,0,0.65)'; g.strokeText(text, x, y); g.fillStyle = col; g.fillText(text, x, y);
    };
    const dot = (x, z, col, r = 4, name = null) => {
      const [px, py] = at(x, z);
      g.beginPath(); g.arc(px, py, r * u, 0, Math.PI * 2); g.fillStyle = col; g.fill();
      g.lineWidth = 1.5 * u; g.strokeStyle = 'rgba(0,0,0,0.6)'; g.stroke();
      if (name) label(name, px, py - (r + 5) * u);
    };
    for (const pl of this.places) if (pl.found) { const [px, py] = at(pl.x, pl.z); label(pl.name, px, py, '#f7d99a'); }
    const M = this.markers?.() ?? {};
    for (const f of M.fires ?? []) dot(f.x, f.z, '#ffb24a', 3);
    if (M.home) dot(M.home.x, M.home.z, '#e9d9b0', 5, 'Hjem');
    for (const a of M.animals ?? []) dot(a.x, a.z, '#c9a36a', 4, a.name);
    for (const q of M.people ?? []) dot(q.x, q.z, q.ally ? '#8ad0a0' : '#a0a0a0', 4, q.name);
    // You: an arrow pointing the way you look.
    if (M.you) {
      const [px, py] = at(M.you.x, M.you.z), a = M.you.yaw;
      g.save(); g.translate(px, py); g.rotate(-a);
      g.beginPath(); g.moveTo(0, -9 * u); g.lineTo(6 * u, 7 * u); g.lineTo(0, 3 * u); g.lineTo(-6 * u, 7 * u); g.closePath();
      g.fillStyle = '#ff5a3a'; g.fill(); g.lineWidth = 1.5 * u; g.strokeStyle = '#fff'; g.stroke();
      g.restore();
    }
    let n = 0; for (let k = 0; k < this.seen.length; k++) n += this.seen[k];
    this.info.textContent = `${Math.round((n / this.landCells()) * 100)} % udforsket`;
  }

  // Fog cells that are land (for the explored share).
  landCells() {
    if (this._land) return this._land;
    let n = 0;
    for (let j = 0; j < FOG; j++) for (let i = 0; i < FOG; i++) if (this.island.heightAt(-SIZE / 2 + (i + 0.5) * CELL, -SIZE / 2 + (j + 0.5) * CELL) > -0.3) n++;
    this._land = Math.max(1, n);
    return this._land;
  }

  toJSON() {
    // Bits → base64.
    const bytes = new Uint8Array(Math.ceil(this.seen.length / 8));
    for (let k = 0; k < this.seen.length; k++) if (this.seen[k]) bytes[k >> 3] |= 1 << (k & 7);
    let s = '';
    for (const b of bytes) s += String.fromCharCode(b);
    return { fog: btoa(s), found: this.places.filter((p) => p.found).map((p) => p.name) };
  }

  load_(d) {
    if (!d?.fog) return;
    try {
      const s = atob(d.fog);
      for (let k = 0; k < this.seen.length; k++) this.seen[k] = (s.charCodeAt(k >> 3) >> (k & 7)) & 1;
      for (const p of this.places) if (d.found?.includes(p.name)) p.found = true;
      this.dirty = true;
    } catch { /* an old or broken save: start unexplored */ }
  }
}

export { VOLCANO };
