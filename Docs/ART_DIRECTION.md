# Art Direction — Island World One-Pager

**Status:** LOCKED v1 (2026-09-13)  
**Parent:** `DESIGN_BRIEF.md`  
**World logic:** Island Ecology (speculative evolution)  
**Engine / DCC:** Unreal Engine 5 · Blender (game-ready pipeline)  
**Working title:** *Tideborn* (locked)

---

## 1. North star

**Readable wild that feels *evolved here*.**  
Not a dinosaur theme park. Not generic tropical postcard. An island with hard niches — spray, ridge wind, dense interior — where creatures and cultures look like they belong to those pressures.

**Player fantasy in one glance:** “I want to cross that ridge, claim that cove, and bring something living home.”

**Quality doctrine:** Slice art aims at **near-final** for what’s in the slice. Greybox is a phase with an exit — not the delivery.

---

## 2. Tone & references (direction, not clones)

| Lean into | Avoid |
|-----------|--------|
| Speculative naturalism (plausible weird) | Cartoon mascot proportions |
| Weathered materials, salt, moss, wear | Pristine plastic AAA sheen everywhere |
| Silhouette-first creatures | Noise detail that dies at game camera |
| Camp as warm human pocket in a cold wild | Horror-only gloom with no exploration joy |
| Grounded mythic *hint* (glow bar mutations, etc.) | Full high-fantasy particle carnival |

**Mood anchors (verbal):** coastal shipwreck mornings · ridge wind · green-dark understory · firelight on modular timber · night eyes in the brush.

*(When collecting image refs later: real islands, speculative evolution art, grounded survival games’ *readability* — never paste protected IP sheets as “our look.”)*

---

## 3. Pillars → visual priorities

| Pillar | Art must sell |
|--------|----------------|
| **Exploration** | 2–3 landmarks readable from approach distance; unique skyline hooks |
| **Base building** | Modular kit snaps clean; “home” reads warm vs wild |
| **Creature mastery** | Species silhouettes distinct at a glance; mutation tells obvious |
| **Follower mastery** | Bound vs Ally readable in pose/gear/UI color — not only a tooltip |

---

## 4. World palette & lighting

### 4.1 Biome bands (slice)

| Band | Palette | Light |
|------|---------|-------|
| **Shore / wreck** | Wet stone, bleached wood, kelp greens, rust-iron | Hard horizon light, reflections, spray |
| **Gather belt / forest** | Deep canopy green, bark browns, filtered god-rays | Soft shafts; readable path contrast |
| **Ridge / overlook** | Wind-scrub, pale rock, thin grass | Big sky, colder grade, long shadows |

### 4.2 Camp accent

Warm fire orange / ember as the emotional “safe” key against cool wild grades. Building wood stays natural with slight warm bias indoors.

### 4.3 Color management

PBR-correct: albedo without baked lighting; night uses lighting + emissive tells (mutation glow, campfire), not crushed underexposure that hides gameplay.

---

## 5. Landmarks (slice must-haves)

Each landmark needs a **one-second silhouette** from the previous band.

1. **Wreck / shore** — broken hull or ribbed timber spine; spawn narrative; tutorial gather.  
2. **Forest rise** — a single enormous niche tree / stone root arch / bone-coral growth (original) as mid-island hook.  
3. **Overlook or cave mouth** — traversal payoff for Cliff-glider utility; wide read of the island.

Landmarks are authored set pieces + modular dress — not pure procedural noise.

---

## 6. Modular building kit (visual rules)

Aligned with game-dev skill + brief:

- **Grid:** lock meters (recommend **2 m** foundation module; document in kit README).  
- **Material family:** driftwood timber + lashed fiber + rough stone footings (shore culture tech).  
- **Wear:** salt bleach on seaward faces; moss on forest pieces — same meshes, material variants.  
- **Snap readability:** ghost valid = calm cool; invalid = clear warm warning (UI + mesh tint).  
- **Silhouette of home:** pitched roof + fire glow should read at dusk from 50–80 m.

Pieces in slice: foundation, wall, doorway, roof/slope, campfire, storage — plus binding post for Bound Followers (distinct, not “friendly bed”).

---

## 7. Creatures (Island Ecology silhouettes)

Original designs — **niche body plans**, readable jobs.

| Working name | Silhouette brief | Material notes | Mutation tells |
|--------------|------------------|----------------|----------------|
| **Kelp-back** | Low heavy grazer; broad back plane for haul | Wet hide, kelp-like fringe | Callus plates, moss camo break-up, salt gloss |
| **Cliff-glider** | Long-limbed; membrane planes between limbs | Matte membrane + keratin ridges | Grip pads, haunch bulk, eye sheen |
| **Burr-hound** | Low night hunter; bristled outline; pack readable | Dark matte, burr/seed hooks | (Threat first; breed later) |

**Rules:**  
- Identify species at 30–40 m without UI.  
- Mutation changes **shape or pattern**, not only a shader slider.  
- No protected dinosaur “mascot” default — if a dino-line niche appears later, it must earn ecology.

---

## 8. Humanoids (cultures in the same ecology)

Two slice cultures, same island, different read:

| Culture | Look | Gameplay hook |
|---------|------|----------------|
| **Coastal scavengers** | Salvage cloth, shell/bone fasteners, wreck palette | Force targets + Hire; Bound gear aesthetic |
| **Grove people** | Fiber/leaf weave, sap dyes, quieter greens | Ally rescue/recruit; beast-care affinity |

**Identity readability:**  
- **Bound:** restraints/post language, stripped personal kit, posture closed  
- **Ally:** kept personal kit, open posture, culture-colored accents  
- **Hire:** neutral trade sash / token — contractual, not enslaved, not kin yet  

Avoid clone Conan barbarian kits; keep island-evolved clothing logic (salt, thorns, climb).

---

## 9. Character (player)

- Readable survivor: practical layered kit that can **upgrade visually** with craft tiers (stitch, plate, fiber).  
- Camera: **third-person locked** for building + creature/Follower read.  
- Hands/tools readable in first meters of craft loop.

---

## 10. VFX / audio art direction (light touch)

| Moment | Art note |
|--------|----------|
| Build snap | Soft confirm tick + dust, not fireworks |
| Tame bond | Quiet biological tell (breath, eye, posture) |
| Mutation birth | One clear morph beat — readable, not slot-machine celebration spam |
| Night threat | Sound first; eyes second; chase last |
| Bound vs Ally UI | Color + icon language consistent across panels |

---

## 11. Pipeline gates (non-negotiable)

From [Game Dev + 3D Assets](sand-workflow:game-dev-3d-assets):

1. Blockout at player scale **in UE** before detail  
2. High → low → UV (texel density standard) → bake → PBR  
3. Export validate: scale, normals, collision, Nanite vs LOD decision  
4. Mutation morphs planned in topology early (don’t bolt on later)  
5. Kit naming + pivots from piece one  

**Texel density:** pick a project px/m and enforce across architecture kit; creatures may use higher on faces.

---

## 12. Slice art exit criteria

- [ ] Three bands grade differently without loading-screen vibes  
- [ ] Landmarks identifiable from approach  
- [ ] Camp reads as *home* at dusk  
- [ ] Three creature silhouettes unconfused  
- [ ] Bound / Ally / Hire readable in world + UI  
- [ ] Modular kit wears salt vs moss variants  
- [ ] No greybox left as “final” inside slice bounds  

---

## 13. Open art locks

1. ~~Working title~~ → **Tideborn** locked (final marketing name later)  
2. ~~Camera~~ → **third-person locked**  
3. How mythic mutation glow is allowed to get  
4. Binding post visual severity (gritty vs ritualized)  

---

## 13a. Amendment 2026-10-10 — web look (Jon)

Jon found the KayKit/Quaternius look too childish and chose **direction "B"** for the web version: simple game-weight shapes with **real, detailed surfaces** — photo-scanned stone, bark, soil, sand and weathered wood (Poly Haven, CC0), image-based sky light, and trees generated by our own pipeline. Free assets only. This sharpens §2 (no cartoon proportions, weathered materials) rather than changing the direction.

- In: textured ground blended by band, scanned rocks and driftwood, generated trees with far LODs, a real shipwreck hull, a sunken fort ruin as the overlook.
- Still interim: the player character and the modular building kit (KayKit) until style-B replacements exist.
- Blood and gore are allowed in Jon's games by default; how far Tideborn goes is still open (ties to §13.4).

---

## 14. Out of scope for this one-pager

Full concept-art pack, final meshes, animation bible — those follow once this direction is locked.

---

*Art direction v1 — Island Ecology, readable wild, warm camp, permanent Bound/Ally visual language.*
