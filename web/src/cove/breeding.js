// Breeding and lineage (D-024, Docs/MUTATION_LINEAGE_RULES.md v2). Stats are the spine: every
// animal has six (vitality, power, speed, stamina, carry, wits); wild ones roll inside the wild
// range (mid-biased), bred ones blend their parents, wobble a little, and lean a bit toward the
// better parent — so a patient breeder gets clearly stronger animals than any wild one, without
// mutations. Mutations are the rare extra layer: 12 % per birth (generation ≥ 1), never more than
// one new per birth, at most three that do something (+ a look-only one), one per family, and no
// pity — a dry streak is just a dry streak. Each mutation shows on the animal.
// Pairing: two tame adults of one species, a female and a male, close together. She carries for a
// few minutes, then a fawn is born tame beside her; it grows to an adult over ten minutes.

// Wild range and breeding cap per stat, per family. Carry is in units (males carry half again).
export const FAMILY = {
  deer: {
    name: 'Krondyr',
    stats: {
      vitality: { label: 'Vitalitet', min: 40, max: 60, cap: 90 },
      power: { label: 'Kraft', min: 20, max: 40, cap: 65 },
      speed: { label: 'Fart', min: 6.0, max: 8.0, cap: 9.8, dec: 1 },
      stamina: { label: 'Udholdenhed', min: 40, max: 60, cap: 90 },
      carry: { label: 'Bæreevne', min: 70, max: 120, cap: 220, unit: 'units' },
      wits: { label: 'Kløgt', min: 20, max: 45, cap: 80 },
    },
    gestation: 180, cooldown: { f: 300, m: 120 }, grow: 600,
    // Family weights when a mutation hits (deer: hide, frame, display; some limb).
    weights: { hide: 3, frame: 3, display: 3, limb: 2 },
  },
};

export const MUTATIONS = {
  hide_load_callus: { family: 'hide', name: 'Bærehud', note: '+15 % bæreevne', tell: 'mørke skuldre', carry: 1.15, tint: [0.78, 0.72, 0.7] },
  hide_camo_moss: { family: 'hide', name: 'Mosplettet', note: 'Svær at få øje på i krattet', tell: 'grønlig, plettet pels', tint: [0.8, 0.95, 0.72] },
  limb_spring_haunch: { family: 'limb', name: 'Springlår', note: '+10 % fart', tell: 'kraftige baglår', speed: 1.1, scale: [1, 1, 1.06] },
  frame_broad_haul: { family: 'frame', name: 'Bred ryg', note: '+20 % bæreevne, lidt langsommere', tell: 'bredere krop', carry: 1.2, speed: 0.95, scale: [1.14, 1, 1] },
  frame_compact: { family: 'frame', name: 'Kompakt', note: 'Vokser hurtigere op', tell: 'kortere og lavere', grow: 0.75, scale: [1, 0.92, 0.92] },
  display_pigment_break: { family: 'display', name: 'Broget', note: 'Kun udseende', tell: 'lyse pletter', cosmetic: true, tint: [1.35, 1.3, 1.25] },
  display_dark: { family: 'display', name: 'Sort', note: 'Kun udseende', tell: 'næsten sort pels', cosmetic: true, tint: [0.42, 0.4, 0.42] },
};

const MUTATION_CHANCE = 0.12;
const NOISE = 0.07;    // of the breeding range (cap − wild min); tuned so ten generations clearly beat the best wild
const BIAS = 0.15;     // pull toward the better parent, of the gap

// Mid-biased roll inside the wild range: great wilds exist, gods are rare.
export function rollWild(fam, rand = Math.random) {
  const out = {};
  for (const [k, s] of Object.entries(FAMILY[fam].stats)) out[k] = s.min + ((rand() + rand()) / 2) * (s.max - s.min);
  return out;
}

export function inherit(fam, a, b, rand = Math.random) {
  const out = {};
  for (const [k, s] of Object.entries(FAMILY[fam].stats)) {
    const range = s.cap - s.min;
    let base = (a[k] + b[k]) / 2;
    const better = Math.max(a[k], b[k]);
    // Closer to the cap, the climb slows (bias and noise shrink).
    const near = Math.max(0, Math.min(1, (base - s.max) / (s.cap - s.max)));
    base += (better - base) * BIAS * (1 - near * 0.7);
    base += (rand() * 2 - 1) * NOISE * range * (1 - near * 0.6);
    out[k] = Math.max(s.min * 0.85, Math.min(s.cap, base));
  }
  return out;
}

// A child's mutations: parents' mutations pass down (each with an even chance from one parent),
// plus at most one new one at 12 % (generation ≥ 1). Caps per the rules.
export function mutate(fam, a, b, gen, rand = Math.random) {
  const pool = [...new Set([...(a ?? []), ...(b ?? [])])];
  const kept = pool.filter((id) => ((a ?? []).includes(id) && (b ?? []).includes(id)) || rand() < 0.5);
  const out = [];
  for (const id of kept) if (canAdd(out, id)) out.push(id);
  let fresh = null;
  if (gen >= 1 && rand() < MUTATION_CHANCE) {
    const w = FAMILY[fam].weights;
    const fams = Object.entries(w).flatMap(([f, n]) => Array(n).fill(f));
    const f = fams[Math.floor(rand() * fams.length)];
    const opts = Object.keys(MUTATIONS).filter((id) => MUTATIONS[id].family === f && canAdd(out, id));
    if (opts.length) { fresh = opts[Math.floor(rand() * opts.length)]; out.push(fresh); }
  }
  return { list: out, fresh };
}

function canAdd(list, id) {
  const m = MUTATIONS[id];
  if (list.includes(id)) return false;
  const same = list.filter((x) => MUTATIONS[x].family === m.family);
  if (m.family === 'display') { if (same.length >= 2 || !m.cosmetic) return false; }
  else if (same.length >= 1) return false;
  const gameplay = list.filter((x) => !MUTATIONS[x].cosmetic).length;
  if (!m.cosmetic && gameplay >= 3) return false;
  return list.length < 4;
}

// What the stats and mutations mean for the animal's jobs.
export function effective(c) {
  const st = c.stats, muts = c.mutations ?? [];
  const mul = (key) => muts.reduce((a, id) => a * (MUTATIONS[id][key] ?? 1), 1);
  const grown = Math.min(1, c.maturity ?? 1);
  return {
    carry: st.carry * (c.sex === 'm' ? 1.5 : 1) * mul('carry') * (grown < 1 ? grown * 0.5 : 1),
    run: st.speed * mul('speed'),
    hp: st.vitality,
    growMul: mul('grow'),
  };
}
