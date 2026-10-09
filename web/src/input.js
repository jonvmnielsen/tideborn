// Touch joystick (appears under the left thumb), action button, and keyboard.
// Produces a camera-relative move vector: x = east, z = south (screen down).

const STICK_R = 56; // px of knob travel

export class Input {
  constructor({ zone, stick, knob, action }) {
    this.zone = zone;
    this.stick = stick;
    this.knob = knob;
    this.actionEl = action;
    this.move = { x: 0, z: 0, mag: 0 };
    this.keys = new Set();
    this.touch = null; // { id, ox, oy, dx, dy }
    this.actionHeld = false;
    this.actionPressed = false; // edge: true for one frame after press
    this.usedTouch = false;
    this.usedKeyboard = false;

    zone.addEventListener('pointerdown', (e) => this.onDown(e));
    window.addEventListener('pointermove', (e) => this.onMove(e));
    window.addEventListener('pointerup', (e) => this.onUp(e));
    window.addEventListener('pointercancel', (e) => this.onUp(e));

    action.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      action.setPointerCapture?.(e.pointerId);
      this.pressAction();
    });
    const release = () => this.releaseAction();
    action.addEventListener('pointerup', release);
    action.addEventListener('pointercancel', release);
    action.addEventListener('lostpointercapture', release);
    action.addEventListener('keydown', (e) => { if (e.key === 'Enter') this.pressAction(); });
    action.addEventListener('keyup', (e) => { if (e.key === 'Enter') this.releaseAction(); });

    window.addEventListener('keydown', (e) => {
      const k = e.key.toLowerCase();
      if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(k)) {
        this.keys.add(k);
        this.usedKeyboard = true;
        e.preventDefault();
      }
      if ((k === 'e' || k === ' ') && !e.repeat) {
        this.pressAction();
        this.usedKeyboard = true;
        e.preventDefault();
      }
    });
    window.addEventListener('keyup', (e) => {
      const k = e.key.toLowerCase();
      this.keys.delete(k);
      if (k === 'e' || k === ' ') this.releaseAction();
    });
    window.addEventListener('blur', () => {
      this.keys.clear();
      this.releaseAction();
      this.endTouch();
    });
    window.addEventListener('contextmenu', (e) => e.preventDefault());
  }

  pressAction() {
    if (this.actionEl.disabled) return;
    this.actionHeld = true;
    this.actionPressed = true;
    this.actionEl.classList.add('pressed');
  }

  releaseAction() {
    this.actionHeld = false;
    this.actionEl.classList.remove('pressed');
  }

  onDown(e) {
    if (this.touch) return;
    e.preventDefault();
    this.usedTouch = e.pointerType !== 'mouse' || this.usedTouch;
    this.touch = { id: e.pointerId, ox: e.clientX, oy: e.clientY, dx: 0, dy: 0 };
    this.stick.style.left = `${e.clientX}px`;
    this.stick.style.top = `${e.clientY}px`;
    this.knob.style.transform = 'translate(0px, 0px)';
    this.stick.hidden = false;
  }

  onMove(e) {
    const t = this.touch;
    if (!t || e.pointerId !== t.id) return;
    let dx = e.clientX - t.ox, dy = e.clientY - t.oy;
    const len = Math.hypot(dx, dy);
    if (len > STICK_R) {
      // Let the base trail the thumb so the stick never "runs out".
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
  }

  onUp(e) {
    if (this.touch && e.pointerId === this.touch.id) this.endTouch();
  }

  endTouch() {
    this.touch = null;
    this.stick.hidden = true;
  }

  update() {
    let x = 0, z = 0;
    const k = this.keys;
    if (k.has('a') || k.has('arrowleft')) x -= 1;
    if (k.has('d') || k.has('arrowright')) x += 1;
    if (k.has('w') || k.has('arrowup')) z -= 1;
    if (k.has('s') || k.has('arrowdown')) z += 1;
    let mag = Math.hypot(x, z);
    if (mag > 0) {
      x /= mag; z /= mag; mag = 1;
    } else if (this.touch) {
      const l = Math.hypot(this.touch.dx, this.touch.dy);
      const dead = 6;
      if (l > dead) {
        mag = Math.min(1, (l - dead) / (STICK_R - dead));
        x = (this.touch.dx / l) * mag;
        z = (this.touch.dy / l) * mag;
      }
    }
    this.move.x = x;
    this.move.z = z;
    this.move.mag = mag;
  }

  consumePress() {
    const p = this.actionPressed;
    this.actionPressed = false;
    return p;
  }
}
