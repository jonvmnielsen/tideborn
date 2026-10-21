// Every land animal on the island, as data (Design Brief §4.1: species are data, not code).
// Adding a new animal = sync its model into public/cove (game-assets: assets.cove.json), then add
// an entry here and a line in SPAWNS. Nothing else changes. A species whose model isn't synced
// yet is skipped with a console note, so entries for animals on their way can sit here already.
//
// Body and size
//   model     asset key (public/cove/<model>.glb)
//   height    metres to the top of the body (the island makes things big: D-025)
//   length    for long, low animals (crocodiles, snakes): scale by length instead of height
//   radius    body radius for collisions and hits (default height × 0.32)
//   yaw       turn the model if it doesn't face +z (radians)
//   tint      RGB multiplier on its colours
//   clips     clip names to look for, per action, when the model's names are unusual:
//             { idle, walk, run, eat, attack, death, hit } → [names…] (case-insensitive, substring ok)
// Behaviour
//   kind      prey | territorial | hostile | hunter (see creatures.js)
//   active    'day' | 'night' | 'always' (default) — night animals come out at dusk, gone at dawn
//   hp, walk, run (m/s), scare (m it bolts at), charge (m a territorial one charges at),
//   sense (m a hostile one notices you at; ×1.6 at night), leash (m from home it will chase),
//   damage, bite (s between bites), fire (m it keeps from a burning fire or torch; hunters)
//   eyes      RGB of eyeshine — the glint of its eyes in the dark (night animals)
//   loot, xp, herd
//   tame      { food: [...], feeds, carry, use, ride } — can be tamed by feeding; ride = { eye, walk,
//             run, seat }: a grown tame one can be ridden (eye height, speeds, and how far its middle is
//             ahead of your eyes — metres, m/s)
//   family    breeding family (breeding.js); sex 'f' | 'm'

export const SPECIES = {
  doe: { name: 'Hind', family: 'deer', sex: 'f', model: 'animal/doe', height: 2.3, hp: 60, walk: 1.6, run: 9, xp: 20, kind: 'prey', scare: 13, loot: { meat: 5, hide: 3 }, herd: 4,
    tame: { food: ['banana', 'coconut'], feeds: 4, carry: 60, use: 'Pakdyr: bærer for dig og kan rides', ride: { eye: 2.5, walk: 3.4, run: 8.5, seat: 0.7 } } },
  stag: { name: 'Kæmpehjort', family: 'deer', sex: 'm', model: 'animal/stag', height: 3.4, hp: 140, walk: 1.6, run: 8.5, xp: 45, kind: 'territorial', scare: 11, charge: 8, damage: 20, loot: { meat: 9, hide: 5 },
    tame: { food: ['banana', 'coconut'], feeds: 7, carry: 140, use: 'Stærkt pakdyr: bærer meget for dig og kan rides', ride: { eye: 3.2, walk: 3.6, run: 9.5, seat: 1.0 } } },
  fox: { name: 'Ildræv', model: 'animal/fox', height: 0.7, hp: 25, walk: 1.6, run: 7, xp: 10, kind: 'prey', scare: 9, loot: { meat: 1, hide: 1 }, tint: [1.5, 0.75, 0.45] },
  // Night hunter (Design Brief §3.2 threat): packs come out of the jungle after dark, circle you
  // and dart in to bite; they won't come into the light of a fire or torch, and they slink off at
  // dawn. Model: Quaternius' velociraptor (CC0) until the Sketchfab one is in — only `model` (and
  // maybe `clips`) changes then.
  stalker: { name: 'Natraptor', model: 'animal/raptor', height: 1.7, length: 4.2, radius: 0.6, hp: 50, walk: 2.4, run: 11, xp: 30, kind: 'hunter', active: 'night', sense: 34, leash: 90, damage: 8, bite: 1.6, fire: 11, eyes: [0.95, 0.75, 0.3],
    loot: { meat: 4, hide: 2 } },
};

// Where they live. at: [x, metres back from the shore at that x] — the island's south coast runs
// along x; n animals share the home; a herd stays together.
export const SPAWNS = [
  { kind: 'doe', at: [-10, 31], n: 4 },
  { kind: 'stag', at: [-4, 33], n: 1 },
  { kind: 'doe', at: [70, 32], n: 3 },
  { kind: 'fox', at: [-85, 40], n: 1 },
  { kind: 'fox', at: [35, 38], n: 1 },
  // Night packs: dens at the jungle edge west and east of the beach camp.
  { kind: 'stalker', at: [-60, 62], n: 3 },
  { kind: 'stalker', at: [55, 66], n: 2 },
];
