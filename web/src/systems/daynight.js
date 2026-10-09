// Day/night cycle. One full day = DAY_LENGTH seconds. phase 0 = midnight, 0.25 = 06:00.
import * as THREE from 'three';
import { smoothstep } from '../noise.js';

export const DAY_LENGTH = 720; // 12 minutes per day

const K = (c) => new THREE.Color(c);
const SKY = {
  day:   { top: K('#5fb2ea'), hor: K('#e9f2ee'), sun: K('#fff1dc'), hemiSky: K('#dff1ff'), hemiGround: K('#7c8f5a') },
  dusk:  { top: K('#4a6fa8'), hor: K('#f2b37a'), sun: K('#ffb070'), hemiSky: K('#f0c8a8'), hemiGround: K('#6d5f4a') },
  night: { top: K('#0d1830'), hor: K('#2a3b5c'), sun: K('#8fa8d8'), hemiSky: K('#5d74a8'), hemiGround: K('#2b3326') },
};

export class DayNight {
  constructor({ scene, sun, hemi, sky, world }) {
    this.scene = scene;
    this.sun = sun;
    this.hemi = hemi;
    this.sky = sky;
    this.world = world;
    this.phase = 0.3; // start a little after sunrise
    this.day = 1;
    this.sunDir = new THREE.Vector3();
    this.light = 1;
    this.listeners = { dawn: [], dusk: [] };
    this.c = { top: new THREE.Color(), hor: new THREE.Color(), sun: new THREE.Color(), hs: new THREE.Color(), hg: new THREE.Color() };
  }

  on(evt, fn) { this.listeners[evt].push(fn); }

  get hours() { return (this.phase * 24) % 24; }
  get isNight() { return this.phase < 0.23 || this.phase > 0.8; }
  get clock() {
    const h = Math.floor(this.hours), m = Math.floor((this.hours - h) * 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
  }

  // Jump to the next morning (sleeping).
  skipToMorning() {
    if (this.phase > 0.25) this.day++;
    this.phase = 0.26;
    for (const f of this.listeners.dawn) f();
  }

  update(dt) {
    const before = this.phase;
    this.phase += dt / DAY_LENGTH;
    if (this.phase >= 1) { this.phase -= 1; this.day++; }
    if (before < 0.25 && this.phase >= 0.25) for (const f of this.listeners.dawn) f();
    if (before < 0.78 && this.phase >= 0.78) for (const f of this.listeners.dusk) f();

    const ang = (this.phase - 0.25) * Math.PI * 2; // 0 at sunrise, π/2 at noon
    const elev = Math.sin(ang);
    const dayT = smoothstep(-0.12, 0.25, elev);
    const duskT = (1 - smoothstep(0.05, 0.4, Math.abs(elev))) * smoothstep(-0.25, 0.0, elev);

    // Sun from the east in the morning to the west at dusk; moon opposite at night.
    if (elev > -0.05) this.sunDir.set(-Math.cos(ang), Math.max(0.12, elev), 0.35).normalize();
    else this.sunDir.set(Math.cos(ang), Math.max(0.35, -elev), -0.3).normalize();

    const { top, hor, sun, hs, hg } = this.c;
    const lerp3 = (out, key) => out.copy(SKY.night[key]).lerp(SKY.day[key], dayT).lerp(SKY.dusk[key], duskT * 0.85);
    lerp3(top, 'top');
    lerp3(hor, 'hor');
    lerp3(sun, 'sun');
    lerp3(hs, 'hemiSky');
    lerp3(hg, 'hemiGround');

    this.sun.color.copy(sun);
    this.sun.intensity = 0.45 + 2.3 * dayT;
    this.hemi.color.copy(hs);
    this.hemi.groundColor.copy(hg);
    this.hemi.intensity = 0.55 + 0.85 * dayT;
    this.sky.material.uniforms.uTop.value.copy(top);
    this.sky.material.uniforms.uHorizon.value.copy(hor);
    this.scene.fog.color.copy(hor);
    this.light = 0.32 + 0.68 * dayT;
    this.nightness = 1 - dayT;
  }
}
