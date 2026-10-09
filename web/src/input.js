// Touch: left thumb = floating joystick, right thumb = drag to turn the camera,
// buttons for actions. Desktop: WASD/arrows, mouse drag to turn, wheel to zoom, keys.

const STICK_R = 56;

export class Input {
  constructor({ moveZone, lookZone, stick, knob }) {
    this.stick = stick;
    this.knob = knob;
    this.move = { x: 0, y: 0, mag: 0 }; // stick space: x right, y down
    this.look = { dx: 0, dy: 0 };
    this.zoomDelta = 0;
    this.keys = new Set();
    this.moveTouch = null;
    this.lookTouch = null;
    this.mouseLook = null;
    this.handlers = {}; // key → fn
    this.touchUsed = matchMedia('(pointer: coarse)').matches;
    this.enabled = true;

    moveZone.addEventListener('pointerdown', (e) => this.startMove(e));
    lookZone.addEventListener('pointerdown', (e) => this.startLook(e));
    window.addEventListener('pointermove', (e) => this.onMove(e));
    window.addEventListener('pointerup', (e) => this.onUp(e));
    window.addEventListener('pointercancel', (e) => this.onUp(e));
    window.addEventListener('wheel', (e) => { this.zoomDelta += Math.sign(e.deltaY); }, { passive: true });

    window.addEventListener('keydown', (e) => {
      if (e.target instanceof HTMLInputElement) return;
      const k = e.key.toLowerCase();
      if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright', 'shift'].includes(k)) {
        this.keys.add(k);
        e.preventDefault();
      }
      if (!e.repeat && this.handlers[k]) {
        this.handlers[k](true);
        e.preventDefault();
      }
    });
    window.addEventListener('keyup', (e) => {
      const k = e.key.toLowerCase();
      this.keys.delete(k);
      this.handlers[`${k}:up`]?.();
    });
    window.addEventListener('blur', () => {
      this.keys.clear();
      this.endMove();
      this.lookTouch = null;
      this.mouseLook = null;
      this.handlers.blur?.();
    });
    window.addEventListener('contextmenu', (e) => e.preventDefault());
  }

  on(key, fn) {
    this.handlers[key] = fn;
  }

  startMove(e) {
    if (this.moveTouch || !this.enabled) return;
    e.preventDefault();
    if (e.pointerType === 'mouse') { this.startLook(e); return; }
    this.moveTouch = { id: e.pointerId, ox: e.clientX, oy: e.clientY, dx: 0, dy: 0 };
    this.stick.style.left = `${e.clientX}px`;
    this.stick.style.top = `${e.clientY}px`;
    this.knob.style.transform = 'translate(0px, 0px)';
    this.stick.hidden = false;
  }

  startLook(e) {
    if (!this.enabled) return;
    e.preventDefault();
    if (e.pointerType === 'mouse') {
      this.mouseLook = { x: e.clientX, y: e.clientY };
      return;
    }
    if (this.lookTouch) return;
    this.lookTouch = { id: e.pointerId, x: e.clientX, y: e.clientY };
  }

  onMove(e) {
    const t = this.moveTouch;
    if (t && e.pointerId === t.id) {
      let dx = e.clientX - t.ox, dy = e.clientY - t.oy;
      const len = Math.hypot(dx, dy);
      if (len > STICK_R) {
        const over = len - STICK_R;
        t.ox += (dx / len) * over;
        t.oy += (dy / len) * over;
        this.stick.style.left = `${t.ox}px`;
        this.stick.style.top = `${t.oy}px`;
        dx = e.clientX - t.ox;
        dy = e.clientY - t.oy;
      }
      t.dx = dx;
      t.dy = dy;
      this.knob.style.transform = `translate(${dx}px, ${dy}px)`;
      return;
    }
    const l = this.lookTouch;
    if (l && e.pointerId === l.id) {
      this.look.dx += e.clientX - l.x;
      this.look.dy += e.clientY - l.y;
      l.x = e.clientX;
      l.y = e.clientY;
      return;
    }
    if (this.mouseLook && e.pointerType === 'mouse') {
      this.look.dx += e.clientX - this.mouseLook.x;
      this.look.dy += e.clientY - this.mouseLook.y;
      this.mouseLook.x = e.clientX;
      this.mouseLook.y = e.clientY;
    }
  }

  onUp(e) {
    if (this.moveTouch && e.pointerId === this.moveTouch.id) this.endMove();
    if (this.lookTouch && e.pointerId === this.lookTouch.id) this.lookTouch = null;
    if (e.pointerType === 'mouse') this.mouseLook = null;
  }

  endMove() {
    this.moveTouch = null;
    this.stick.hidden = true;
  }

  update() {
    let x = 0, y = 0;
    const k = this.keys;
    if (k.has('a') || k.has('arrowleft')) x -= 1;
    if (k.has('d') || k.has('arrowright')) x += 1;
    if (k.has('w') || k.has('arrowup')) y -= 1;
    if (k.has('s') || k.has('arrowdown')) y += 1;
    let mag = Math.hypot(x, y);
    if (mag > 0) {
      const walk = k.has('shift') ? 0.5 : 1;
      x = (x / mag) * walk; y = (y / mag) * walk; mag = walk;
    } else if (this.moveTouch) {
      const l = Math.hypot(this.moveTouch.dx, this.moveTouch.dy);
      if (l > 6) {
        mag = Math.min(1, (l - 6) / (STICK_R - 6));
        x = (this.moveTouch.dx / l) * mag;
        y = (this.moveTouch.dy / l) * mag;
      }
    }
    if (!this.enabled) { x = 0; y = 0; mag = 0; }
    this.move.x = x;
    this.move.y = y;
    this.move.mag = mag;
  }

  takeLook() {
    const d = { dx: this.look.dx, dy: this.look.dy };
    this.look.dx = 0;
    this.look.dy = 0;
    return d;
  }

  takeZoom() {
    const z = this.zoomDelta;
    this.zoomDelta = 0;
    return z;
  }
}
