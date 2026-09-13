# Design Brief — Working Title: *Tideborn* (locked working title)

**Status:** Locked plan → design brief v1.1 (2026-09-13) — followers dual-path + multi-clade fauna  
**Engine:** Unreal Engine 5 (Blueprints-first; C++ only where it earns keep)  
**Art DCC:** Blender → UE5 (see skill [Game Dev + 3D Assets](sand-workflow:game-dev-3d-assets))  
**Quality doctrine:** High-quality results over speed. No sloppy interim “just to show something.” Stage gates over vanity milestones.  
**IP rule:** Original IP. ARK-inspired *genre* fantasy only — no cloned creatures, names, UI, or distinctive copyrighted content.

---

## 1. Pitch

You wash up in a living wild that rewards **looking**, **claiming ground**, and **building a people** — animals *and* humanoids. The critical path is exploration and building a foothold with tamed creatures and/or recruited followers. Creature **breeding, mutations, and lineages** are a vast optional mastery layer. Humanoids use a dual **Followers** layer: force (capture/bind) *or* earn (rescue/recruit/hire). Neither breeding nor a specific follower path is required to advance; both should be deeply tempting.

One-sentence loop (critical path):  
**Explore a landmark → gather what you need → build/upgrade a camp → bring creatures and/or followers that help you push farther.**

One-sentence loops (optional mastery):  
**Creatures:** Pair tames → raise offspring → chase mutations and stronger lineages → open variants and long-term goals.  
**Followers:** Capture *or* earn people → assign roles → manage loyalty/risk → grow a capable camp.

---

## 2. Pillars (priority order for decisions)

| Priority | Pillar | Player fantasy | Design implication |
|----------|--------|----------------|--------------------|
| P0 | **Exploration** | “What’s over that ridge?” | Readable landmarks, traversal gates that are *interesting* not empty distance, discovery rewards |
| P0 | **Base building** | “This place is *mine*.” | Modular snap kit, solid placement feel, camp as emotional hub |
| P0 | **Creature mastery** | “My animals change how I play.” | Multi-clade roster (not dinosaur-only); taming on/near critical path; breeding as deep opt-in |
| P0 | **Follower mastery** | “I built a camp *with people*.” | Dual paths: force (capture/bind/enslave) vs earn (rescue/recruit/hire); shared roles; loyalty/risk differ by path |
| P1 | Crafting & light progression | “I earned better tools.” | Supports gather/build/tame — not a spreadsheet main course |
| P1 | Combat & hunting | “The wild can kill me.” | Threat shapes routes and camps; not a skill-shot action game |
| P2 | Hard survival meters | Pressure, not punishment | Light hunger/thirst/temperature — never the star |

**Hard constraint — breeding:**  
Breeding is an **extensive optional side-quest layer** that can open a whole mode of play (stronger creatures, new variants via mutations, lineage goals). It must **never be required** to advance the main exploration/building path. It must be so rewarding and fun that players *want* to sink time into it.

**Hard constraint — followers:**  
Force and earn paths are both real. Neither path is required to finish the critical path. Capture/bind has brittle loyalty and revolt/escape risk; earn paths have higher trust ceilings and better long-term specialists.

---

## 3. Vertical slice (what “done” means for v1 quality bar)

### 3.1 Experience goal
A stranger can play **~25–45 minutes**, understand the fantasy, finish a short critical-path arc, and *notice* that breeding exists as a juicy side door — without being forced through it.

### 3.2 Slice bounds (in)

- **One biome**, visually distinct, with **2–3 landmarks** (e.g. wreck/shore → forest rise → stone overlook or cave mouth). Landmarks must be memorable from game camera, not only from a skybox screenshot.
- **Modular building kit:** foundation, wall, doorway, roof/slope, campfire, storage — snap preview, valid/invalid placement, enough to feel like a *home*.
- **Gather + craft (support):** wood / stone / fiber (or biome equivalents) → basic tools → better gather → camp pieces.
- **Taming (critical-path friendly):** at least **one** clearly useful tame (haul and/or traversal and/or guard). Tame loop readable: find → prepare → secure → bond → utility unlock.
- **Threat:** at least **one** hostile archetype that makes camps, routes, and tames matter.
- **Followers (opt-in, dual path):** prove force *and/or* earn acquisition with one useful camp role; critical path completable solo.
- **Breeding (opt-in, thin but real):** pair two tames → gestation/raise → offspring with **visible** mutation or clear stat/trait win → player understands the mastery hook. Critical path remains completable with wild tames only.
- **Die / respawn**, **save / load** of durable state (inventory, built pieces, tames, breeding progress, followers).
- **Day/night** as readability + light pressure (not full hardcore sim).

### 3.3 Slice bounds (out of *slice*, still on roadmap)

Kept in the **idea / later vision** area — not deleted:

- Bosses / pinnacle encounters  
- Huge map / multi-biome world  
- Multiplayer  
- Deep combat skill trees  
- Full breeding encyclopedia (many species, mutation categories, lineage meta)  
- Advanced building tiers, plumbing, automation, etc.

### 3.4 Slice exit criteria (quality gates)

- [ ] Critical-path loop completable without breeding and without cheats  
- [ ] Landmarks readable and desirable; exploration feels authored  
- [ ] Building placement feels trustworthy (snap, feedback, no jank as “content”)  
- [ ] Tame utility is obvious in the body (you *use* the creature to push farther)  
- [ ] Breeding opt-in produces at least one “I want to do that again” moment  
- [ ] Follower opt-in shows a real force-vs-earn tradeoff (loyalty/risk), not a cosmetic label  
- [ ] Art inside the slice meets the project’s target bar (not greybox-as-final)  
- [ ] Frame budget acceptable at slice density on target hardware  
- [ ] Known bugs listed; no infinite polish trap  

---

## 4. Systems architecture

### 4.1 Principles

- **Data over hardcoding:** items, recipes, build pieces, species, traits, mutations as data assets.  
- **Components over god-objects:** Inventory, Interactor, Health, Tameable, Breedable, Follower (loyalty/path), Builder.  
- **Simulation ≠ UI:** widgets observe; they don’t own item truth.  
- **Prefabs/Actors** for anything placed more than once.  
- **Blueprints-first** for systems spikes; extract C++ when profiling or shared core demands it.

### 4.2 Suggested build order (dependency)

1. Locomotion + camera + interact trace  
2. Item definitions + inventory + pickup/drop/stack  
3. Gathering nodes  
4. Crafting (minimal tree)  
5. Modular building (ghost, snap, commit, cost)  
6. Save/load graph for world + inventory + builds  
7. One creature: AI senses + combat/threat  
8. Taming pipeline + creature utility  
9. Breeding data model + one pair path + mutation roll + offspring  
10. Landmark traversal hook that uses tame utility (not breed-gated)  
11. Polish: audio/feedback/day-night readability  
12. *Later:* world size, bosses, more species, multiplayer  

### 4.3 Inventory / crafting / building

- Items = IDs + stack rules + icons + meshes + tags.  
- Recipes reference item IDs only.  
- Building pieces share a **grid / snap / pivot** contract with the modular art kit (same truth in Blender and UE).  
- Storage containers reuse inventory backend.

### 4.4 Taming

- Wild creature states: wild → calming/secure → tamed → (optional) following / parked / mounted / working.  
- Prefer **readable** taming (player understands why it worked) over opaque timers alone.  
- Utility examples for slice: carry weight, climb/jump assist, lamp/scare, resource gather assist — pick **one primary** utility and do it well.

### 4.5 Followers (humanoids) — dual path

**Not creatures-only.** Humans/humanoids are first-class systems citizens.

**Dual acquisition (both first-class):**
- **Force:** defeat → capture → bind/enslave → work/combat. Brittle loyalty; escape/revolt risk; faster labor, lower trust ceiling.
- **Earn:** rescue / recruit / hire / faction reputation → willing bond. Higher loyalty ceiling; better specialists; upkeep/reputation costs.

**Shared role board** (assignable, swappable): builder, gatherer, guard, scout, beast-handler, crafter, expedition lead — path changes *risk and ceiling*, not whether roles exist.

**Design notes:** Conan Exiles thralls are a reference for *capture depth*, not a clone target. More diverse entry points and relationship modes. Distinct from creature breeding/mutations.

**Slice:** at least one earn-path follower *or* one force-path captive proven end-to-end with one useful role; critical path completable solo.

### 4.6 Breeding & mutations (full model early; slice proves a thin path)


**Design stance:** side-quest depth, main-path optional, prestige + power + novelty rewards.

**Data to design before content sprawl:**

| Concept | Notes |
|---------|--------|
| Species | Stats baselines, breed rules, gestation, baby growth, diet |
| Individual | Guaranteed + random stat rolls; parents; generation index |
| Sex / pair rules | Explicit; no accidental softlocks |
| Mutation | Typed slots (e.g. stat, cosmetic, ability-lite); rarity weights; caps per generation to avoid explode-to-god |
| Lineage | Traceable parents; UI that makes “project breeding” satisfying |
| Variants | Mutation combinations may unlock named variants later — roadmap, not slice-critical |
| Non-gate rule | No required landmark, build tier, or story beat requires a bred/mutated creature |

**Slice proof:** one species breedable end-to-end; at least one mutation category visible (stat *or* cosmetic *or* minor ability); offspring usable in the same systems as wild tames.

**Anti-goals:** forcing breeding for map progress; invisible RNG with no player skill/selection; infinite stacking with no diminishing structure.

---

## 5. World & content (slice)

**Working biome direction (placeholder — art lock later):** coastal wild meeting dense interior — shore wreck as spawn narrative, forest as gather/build belt, elevated or cave landmark as “farther” unlocked with tame utility.

**Creatures (slice minimum):**

| Role | Count | Notes |
|------|------:|-------|
| Useful tame | 1 | Traversal/haul/guard — critical-path helper |
| Threat | 1 | Shapes night/routes/camp |
| Breedable | 1 | May be the same as the useful tame |

**Roster doctrine:** not dinosaur-only. Dinosaurs may appear as *one clade* among mammals, birds, arthropods, marine life, speculative island fauna, etc. **Locked:** Island Ecology (speculative evolution). Niche-adapted original fauna; dinosaurs are not the brand (optional minority only if they earn a niche).

**Humanoids (slice minimum):** prove dual-path Followers with ≥1 useful role (earn and/or force). Original cultures/looks — not Conan clones.

Original designs only — silhouette, behavior, and naming distinct from existing commercial IPs.

---

## 5.1 Slice roster sketch (Island Ecology — draft ideas, not final art)

Original speculative species — placeholders for design, rename freely:

| Working name | Niche | Slice role |
|--------------|-------|------------|
| **Kelp-back** | Shore grazer with buoyant hide | Early haul tame; calm temperament |
| **Cliff-glider** | Membrane-glide between ridges | Traversal tame (opens overlook landmark) |
| **Burr-hound** | Night pack hunter, low profile | Threat archetype |
| **Root-tapper** | Digs tubers / soft stone | Optional gather assist (later than slice-critical) |

**Humanoid presence (same island):** coastal scavenger band + inland grove people — supports both *earn* (rescue castaway / hire guide) and *force* (raid camp captive) without needing a continent of factions yet.

**Mutation flavor (ecology-true):** camouflage morphs, grip/climb pads, salt-tolerant hide, night-eye, load-bearing frame — prefer traits that scream “this island shaped them.”

---

## 6. Art & audio direction (process)

### 6.1 Pipeline (mandatory)

Follow the game-ready pipeline from the research skill:

Blockout (player-scale in UE) → high → low → UV (texel density standard) → bake → PBR → export (FBX/USD as chosen) → import validate (scale, normals, collision, LODs/Nanite decision) → dress in-engine.

### 6.2 Modular kit rules

- Grid increments locked (document meters).  
- Pivots at snap points.  
- Naming convention from piece one.  
- Trim sheets / atlases preferred for architecture; unique UVs for hero props/creatures.  
- Nanite for eligible statics; author LODs where Nanite isn’t the plan (foliage, skinned, etc.).

### 6.3 Target bar

Slice art is **near-final for the slice**, not prototype leftovers. Greybox is a phase with an exit date — not a delivery.

### 6.4 Audio

Footsteps, craft success, build place/snap, tame feedback, creature VO, night ambience — feedback before soundtrack maximalism.

---

## 7. Technical targets

| Topic | v1 intent |
|-------|-----------|
| Platform | PC first |
| Perspective | **Third-person locked** |
| Input | UE Enhanced Input |
| Networking | None in slice; keep code assumptions documented for *possible* later multiplayer (no heroic abstraction tax) |
| Performance | Budget for slice density; profile before expanding world |
| Versions | Pin UE5.x version in project README when repo exists |

---

## 8. Roadmap (sequenced, not deleted)

| Phase | Focus | Exit |
|-------|--------|------|
| **0 — Foundations** | Project hygiene, input, character, interact, inventory | Runnable empty level + items |
| **1 — Camp** | Gather, craft, modular build, save | Home you care about |
| **2 — Wild** | Threat + tame + utility gate to landmark | Critical path loop true |
| **3 — Bloodline** | Breeding thin path + mutation visibility | Opt-in mastery hook proven |
| **4 — Slice lock** | Art/audio pass to target bar, bug list, perf | Vertical slice exit criteria met |
| **5 — Widen** | More species, building tiers, biome 2 | Content without new unproven pillars |
| **6 — Horizon** | Bosses, large map, deeper mutations, multiplayer eval | Separate design addenda |

---

## 9. Team / bot org (when we execute)

Suggested specialist lanes (spin up only when executing that lane):

- **Design lead** — brief, balance tables, mutation rules  
- **UE systems** — inventory, build, tame, breed, save  
- **UE gameplay / AI** — creatures, threat, utility  
- **Blender kit** — modular camp + landmarks blockout→final  
- **Creature art** — original species  
- **Playtest** — feel, softlock hunt, “is breeding tempting?”  
- **Quality gate** — slice exit criteria enforcement  

Parent (this assistant) keeps architecture consistency and refuses scope that breaks pillars or quality doctrine.

---

## 10. Open decisions (not blockers for this brief)

1. ~~Working title~~ → **Tideborn** (locked; final marketing name later).  
2. **Art tone** (grounded prehistoric, stylized, dark mythic, etc.).  
3. ~~Camera~~ → **Third-person locked**.  
4. Exact **mutation taxonomy** (stat vs cosmetic vs ability weights).
4b. ~~Creature-world direction~~ → **Island Ecology (locked)**.
4c. Follower tone details (escape/revolt rules, hire upkeep, faction list).  
5. Epic account / UE version / repo hosting when execution starts.

---

## 11. Non-negotiables

1. Quality over speed; stage gates honored.  
2. Original IP only.  
3. Breeding never gates critical progress.
3b. Follower force *or* earn paths are both real; neither specific path is required to finish the critical path.  
4. Vertical slice before huge map / bosses / multiplayer.  
5. Data-driven items/species/mutations.  
6. Game-ready art pipeline — not film Blender habits.  

---

## 12. Next planning artifacts

0. Followers dual-path rules → see `FOLLOWERS_RULES.md` (**LOCKED v2**)

1. ~~Mutation & lineage rules addendum~~ → see `MUTATION_LINEAGE_RULES.md` (**LOCKED v2**)  
2. Art direction one-pager → see `ART_DIRECTION.md` (**LOCKED v1**)  
3. **Working title lock**  
4. Execution plan / bot org → see `EXECUTION_PLAN.md` (**LOCKED v1**)
5. Then — and only then — UE5 project scaffold + repo  

---

*Brief v1 locked to agreed plan. Amend deliberately; don’t silently erode pillars.*
