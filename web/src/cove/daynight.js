// The island's day (Design Brief §3.2: day/night as readability + light pressure). One day is
// 20 minutes: the sun is up from about 06:00 to 18:30, then it is night until dawn. Nights are
// dark but readable under the moon; fires, torches and the volcano are the bright things, and the
// wild gets more dangerous (night hunters come out, hostile animals see farther).
// The sky light is rebuilt only when the sun has moved a little (it costs a few ms).
export const DAY_SECONDS = 1200;
const RISE = 6.0, SET = 18.5;

export class DayNight {
  constructor(sky, { hour = 8.5 } = {}) {
    this.sky = sky;
    this.hour = hour;
    this.speed = 1; // tests and sleeping speed it up
    this.listeners = [];
    this.lastElev = null;
    this.since = 0;
    this.apply(true);
  }

  // Sun elevation (degrees) and azimuth (east → west over the day).
  sun(h = this.hour) {
    const dayLen = SET - RISE;
    if (h >= RISE && h <= SET) return [70 * Math.sin(Math.PI * (h - RISE) / dayLen), 85 + 185 * (h - RISE) / dayLen];
    // Under the horizon it keeps going round, from the west at sunset to the east at dawn.
    const k = ((h - SET + 24) % 24) / (24 - dayLen); // 0 at sunset → 1 at sunrise
    return [-40 * Math.sin(Math.PI * k), 270 + 175 * k];
  }

  get night() { return this.hour < RISE - 0.25 || this.hour > SET + 0.5; }
  get dark() { return this.sky.night; } // 0..1 how dark it is right now
  get clock() { const h = Math.floor(this.hour), m = Math.floor((this.hour - h) * 60); return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`; }

  set(hour) { this.hour = ((hour % 24) + 24) % 24; this.apply(true); }

  update(dt) {
    const was = this.night;
    this.hour = (this.hour + (dt * this.speed * 24) / DAY_SECONDS) % 24;
    this.since += dt;
    this.apply(false);
    if (was !== this.night) for (const f of this.listeners) f(this.night);
  }

  apply(force) {
    const [elev, az] = this.sun();
    if (!force && this.lastElev !== null && Math.abs(elev - this.lastElev) < 0.6 && this.since < 6) return;
    this.lastElev = elev;
    this.since = 0;
    this.sky.setSun(elev, az);
  }

  toJSON() { return +this.hour.toFixed(3); }
  load_(h) { if (typeof h === 'number') this.set(h); }
}
