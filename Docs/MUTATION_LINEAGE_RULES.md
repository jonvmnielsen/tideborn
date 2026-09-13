# Mutation & Lineage Rules — Island Ecology Addendum

**Status:** LOCKED v2 (2026-09-13)  
**Parent:** `DESIGN_BRIEF.md`  
**Applies to:** Creatures only (not humanoid Followers)  
**Hard constraints:**  
- Breeding is a deep **optional** mastery track (side-quest scale).  
- **Never required** to advance exploration / building / critical-path landmarks.  
- Must be rewarding enough that players *want* to engage.  
- World logic: **Island Ecology** (speculative evolution).

---

## 0. Design thesis (v2)

**Primary strength path = lineage breeding.**  
You make stronger and stronger *normal* creatures by choosing parents with better stats, generation after generation. Wild tames are a starting point; a dedicated breeding project can produce adults that clearly outclass random wild spawns — without any mutation.

**Mutations = additional layer on top of that.**  
They are not the only way to get strong. They add:
- potential for **even higher** power (stat spikes / soft-cap breaks),
- **new skills** (ability-lite),
- **new looks** and named **variants**,
- long-term collection / prestige goals.

**No pity system.** Dry streaks happen. Mutation remains a real prize, not a guaranteed drip.

---

## 1. Design goals

| Goal | Meaning |
|------|---------|
| Breeding skill expression | Pair choice and selection matter more than lucky mutation RNG |
| Strength without mutations | A clean high-stat lineage is already a huge reward |
| Mutations as spice + ceiling | Extra power, skills, looks, variants — not the sole progression rail |
| Readable | Player can explain inheritance and any mutation in plain language |
| Ecology-true | Traits feel like island niche adaptations |
| Bounded chaos | Mutations don’t make every baby a firework; stats stay the spine |
| Non-gating | Nothing on the critical path requires bred or mutated creatures |

---

## 2. Creature identity model

Every creature instance stores:

```
SpeciesId
Sex (or species-specific reproductive rules — explicit in data)
Generation (0 = wild-caught / world-spawned)
Parents[0..1] (null for wild)
StatBlock (§3)
MutationSlots[] (§4)   // may be empty on a god-tier stat beast
Colors / CosmeticGenes
LineageId
TameState / Bond
```

- **Wild:** Generation 0, natural variance inside species ranges.  
- **Bred:** Generation = max(parent gens) + 1; stats inherit (§3); mutations may or may not appear (§4).

---

## 3. Stats — the main power ladder

### 3.1 Core stats (all species)

Keep the list tight and survival-meaningful:

| Stat | Role |
|------|------|
| **Vitality** | HP / toughness |
| **Power** | Melee / work burst |
| **Speed** | Move / chase / flee |
| **Stamina** | Sprint, glide time, work shifts |
| **Carry** | Haul weight |
| **Wits** | Tame resistance, train speed, light AI hooks |

Species define:
- `WildMin` / `WildMax` per stat (what you find in the wild)
- `BreedCap` per stat (how high pure breeding can push — **above** typical wild max)
- Optional `MutationSoftCap` (mutations may push a bit past BreedCap — see §4)

### 3.2 Wild rolls

Wild spawns roll each stat in `[WildMin, WildMax]` with a mid-biased curve (great wilds exist, gods are rare).

### 3.3 Inheritance (the skill of breeding)

For each core stat on birth:

1. **Parent blend:** `base = lerp(statA, statB, Focus)`  
   - Default Focus = 0.5  
   - If UI offers **sire/dam focus**, allow 0.35 / 0.65 so players express intent
2. **Breeding variance:** ± `BreedNoise` (default ~4–7% of that stat’s wild range)
3. **Selection pressure (generational climb):**  
   `base` is then pulled slightly toward the **better parent** for that stat (small bias, e.g. 10–15% of the gap).  
   This is what lets lineages get **stronger and stronger** over generations without mutations.
4. **Clamp** to `[speciesFloor, BreedCap]` for non-mutated influence  
5. If a mutation grants a stat effect, apply after clamp, then clamp to `MutationSoftCap` if defined

**Resulting fantasy:**  
A patient breeder with no mutations should still produce a Kelp-back that hauls like a truck compared to a beach wild. Mutations are how you break into *special* territory — not how you unlock “real” strength.

### 3.4 Diminishing climb (anti-infinite)

As a stat approaches `BreedCap`, inheritance bias and noise shrink (asymptotic).  
You can keep polishing a lineage forever for tiny gains; big jumps happen early–mid project.  
Mutations are the clean way to punch *near or through* soft ceilings.

---

## 4. Mutations — extra layer

### 4.1 Role in the fantasy

| Without mutations | With mutations |
|-------------------|----------------|
| Very strong, optimized normal adults | Strong *plus* skills / looks / variants |
| Prestige of a clean bloodline | Prestige of rare morphs and named variants |
| Best tools for most jobs | Situational gods + collection goals |

Mutations may:
- add **flat or % stat bonuses** (extra strength layer),
- grant **skills** (ability-lite tags),
- change **appearance**,
- contribute toward **variant** identity (multi-mutation or specific combo — mostly roadmap).

### 4.2 Slot families (Island Ecology)

| Family | Fantasy | Examples |
|--------|---------|----------|
| **Hide** | Surface adaptation | Moss camo, salt seal, load callus |
| **Limb** | Movement / grip | Grip pads, spring haunch, web digit |
| **Sense** | Perception | Night-eye, scent mark |
| **Frame** | Body plan | Broad haul, compact build |
| **Display** | Look / prestige | Crest, glow bar, pigment break |
| **Breath** | Endurance niche | Later species (dive / ridge air) |

**Slice-active:** Hide, Limb, Sense, Frame, Display.

### 4.3 Caps

| Rule | Default |
|------|---------|
| Max gameplay mutations per creature | **3** |
| Display (cosmetic-only) | May occupy a **4th** slot if it has no combat/work effect |
| Max per family | **1** (Display: up to 2 if both cosmetic-only) |
| Max **new** mutations gained on a single birth | **1** |
| Tier II / III | Roadmap (lineage prerequisites) |

Empty mutation list on a near-BreedCap animal is **valid and desirable**.

### 4.4 Birth mutation roll — **no pity**

On birth:

1. Roll `MutationChance` (default **12%** base for Generation ≥ 1).  
2. **No pity, no stacking consolation, no guaranteed drip after dry streaks.**  
3. On failure: child is still potentially a huge win via **stats alone**.  
4. On success: choose family weighted by species niche tags → pick mutation → apply **visible tell** + effects.

Optional (not pity): species or care environment applies a **small fixed bias** to family weights (shore camp → Hide slightly more likely *when* a mutation hits). Biases never raise the chance to near-certainty and do not accumulate after failures.

### 4.5 Starter catalog (slice)

#### Hide
| Id | Tier | Layer | Effect | Tell |
|----|------|-------|--------|------|
| `hide_camo_moss` | I | Skill + look | Harder to detect in foliage | Mottled break-up |
| `hide_salt_seal` | I | Skill | Less stamina drain in spray/shore | Gloss dark hide |
| `hide_load_callus` | I | Power | +Carry | Shoulder callus |

#### Limb
| Id | Tier | Layer | Effect | Tell |
|----|------|-------|--------|------|
| `limb_grip_pads` | I | Skill | Better rock grip / climb assist | Toe pads |
| `limb_spring_haunch` | I | Power | Burst Speed / jump assist | Heavy haunch |
| `limb_web_digit` | I | Skill | Minor swim stamina | Light webbing |

#### Sense
| Id | Tier | Layer | Effect | Tell |
|----|------|-------|--------|------|
| `sense_night_eye` | I | Skill | Better night detection | Eye sheen |
| `sense_scent_mark` | I | Skill | Pulse-reveal nearby nodes/corpses | Facial marking |

#### Frame
| Id | Tier | Layer | Effect | Tell |
|----|------|-------|--------|------|
| `frame_broad_haul` | I | Power | +Carry, slight −Speed | Wide torso |
| `frame_compact` | I | Skill/QoL | Tighter spaces; slightly faster growth | Short silhouette |

#### Display
| Id | Tier | Layer | Effect | Tell |
|----|------|-------|--------|------|
| `display_crest_tide` | I | Look | Prestige / tiny Wits flavor optional | Crest |
| `display_glow_bar` | I | Look (+tiny QoL) | Player night readability | Biolum strip |
| `display_pigment_break` | I | Look | None | High-contrast paint |

**Species weights:** Kelp-back → Hide/Frame/Display; Cliff-glider → Limb/Sense/Display.

---

## 5. Variants (mutations → “new creatures” fantasy)

**Variant** = a recognized morph when rules match (name + unique icon).

**Slice:** soft only — UI can label e.g. “Moss-backed Kelp-back” when `hide_camo_moss` present.  
**Roadmap:** formal variants from mutation combos or Tier II sets that feel like *new* island forms — still optional content, never gates.

Variants are how mutations deliver “new ones” without replacing the stat-breeding fantasy.

---

## 6. Lineage & care

- Pair compatible adults (same species in slice; hybrids later).  
- Gestation/egg/care per species data; nursery needs food/safety.  
- **Lineage screen:** parents, generation, stats vs BreedCap, mutations, variant tags.  
- **Pin goals:** pin a target *stat profile* and/or a target mutation — coaching, not cheats.  
- Maturity: Newborn → Juvenile → Adult; full job utility at Adult. Mutation tells visible at birth.  
- Inbreeding: soft penalties (frailty / slightly lower mutation chance) — not a hard block.

---

## 7. Power budget vs wild

| Population | Intent |
|------------|--------|
| Average wild | Baseline tools |
| Lucky wild | Occasional strong finds — still below dedicated BreedCap projects |
| Bred, no mutations, high gens | **Clearly stronger** work animals — main side-quest reward |
| Bred + mutations | Stronger *and* specialized / spectacular |

**Balance rule:** a top purebred should beat a top wild at that species’ job.  
A mutated purebred should feel special, not make purebreds feel worthless.

---

## 8. Non-gating (unchanged)

Allowed: better haul, safer nights, prestige morphs, QoL skills, optional dens later.  
Forbidden: required mutant/bred key for critical landmarks, bosses, or build tiers.

---

## 9. Economy / time (extensive side quest)

Care, pair cooldowns, multi-generation stat climbs, mutation hunting as *extra*, nursery risk from threats (Burr-hounds punish careless camps).  
Long projects = many generations of **stat work**, with mutations as intermittent jackpots — **without pity**.

---

## 10. Starting numbers (tune in playtests)

| Parameter | v2 start |
|-----------|----------|
| Base mutation chance | **12%** (no pity) |
| Pity | **None** |
| Max gameplay mutations | 3 (+ optional cosmetic Display) |
| New mutations per birth | 0 or 1 |
| Stat noise | ~4–7% of wild range |
| Better-parent bias | ~10–15% of parent gap |
| Inbreeding mutation penalty | small, optional |

Debug-log every birth (parents, stats, mutation yes/no).

---

## 11. Slice acceptance tests

- [ ] Multi-generation breed produces an adult **clearly stronger** than average wild **with zero mutations**  
- [ ] Mutation can appear and shows a visible tell + skill or power layer  
- [ ] Dry mutation streaks do **not** trigger consolations  
- [ ] Critical path completable with no breeding  
- [ ] Lineage UI shows gen, stats vs cap, mutations  

---

## 12. Roadmap

Tier II/III, hybrids, formal variant encyclopedia, optional mutation dens/events, environment family-weight biases expanded.

---

## 13. Changelog

**v2:** Removed pity entirely. Elevated purebred generational stat climbing as the primary strength path (`BreedCap`, better-parent bias, diminishing approach to cap). Reframed mutations as an additive layer for extra power, skills, looks, and variants — not the sole path to strong creatures. Mutation base chance set to 12%.

---

*Addendum v2 — stats first, mutations on top, no pity, never gate the main path.*
