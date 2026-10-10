# Status

_Last updated: 2026-10-10_ · Play: https://jonvmnielsen.github.io/tideborn/

Measured against the vertical slice in `Docs/DESIGN_BRIEF.md` §3.

## Phase 1 — Camp (web v0.2) ✅ playable
- [x] One island biome with three bands and three landmarks: shipwreck on the shore, giant oak on the forest rise, sunken fort ruin on the ridge
- [x] Style B (D-010): textured ground, scanned rocks/driftwood/plants, generated trees with far versions, sky light
- [x] Third-person camera, touch joystick + camera drag, keyboard/mouse
- [x] Gather wood / stone / fiber; every tree choppable; regrowth
- [x] Crafting: stone axe, pick (tool gates gathering)
- [x] Modular building on a 4 m grid: foundation, wall, doorway, window, loft (2nd floor), roof, stairs, fence, campfire, torch, chest, bed; ghost with green/red and reason; remove with 50% refund
- [x] Stand on floors, walk through doorways, walls block
- [x] Day/night (12 min), fires and torches light the camp at night
- [x] Light hunger, health, faint and respawn at your bed
- [x] Save/load of inventory, buildings, chest contents, felled trees, time, home

### Known gaps
- Player character and building kit are still the KayKit look (D-007) — they clash with style B until replacements exist
- Gable ends of roofs are open
- No sound yet
- Real-phone frame rate not measured yet (headless: ~0.4 M triangles/frame on phone settings); download ~26 MB

## Phase 2 — Wild ⏳ blocked on art
Burr-hound (night threat), Kelp-back (haul tame), Cliff-glider (opens the overlook). Needs animal models: Quaternius animal pack requested from Jon.

## Phase 3 — Bloodline ⏳
Breeding per `Docs/MUTATION_LINEAGE_RULES.md`. Data model can be built before art.

## Phase 4 — Followers ⏳
Bound / Ally / Hire per `Docs/FOLLOWERS_RULES.md`. KayKit Adventurers can stand in for the two island cultures.
