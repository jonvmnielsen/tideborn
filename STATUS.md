# Status

_Last updated: 2026-10-09_ · Play: https://jonvmnielsen.github.io/tideborn/

Measured against the vertical slice in `Docs/DESIGN_BRIEF.md` §3.

## Phase 1 — Camp (web v0.2) ✅ playable
- [x] One island biome with three bands and three landmarks: wreck on the shore, giant tree on the forest rise, ruined watchtower on the ridge
- [x] Third-person camera, touch joystick + camera drag, keyboard/mouse
- [x] Gather wood / stone / fiber; every tree choppable; regrowth
- [x] Crafting: stone axe, pick (tool gates gathering)
- [x] Modular building on a 4 m grid: foundation, wall, doorway, window, loft (2nd floor), roof, stairs, fence, campfire, torch, chest, bed; ghost with green/red and reason; remove with 50% refund
- [x] Stand on floors, walk through doorways, walls block
- [x] Day/night (12 min), fires and torches light the camp at night
- [x] Light hunger, health, faint and respawn at your bed
- [x] Save/load of inventory, buildings, chest contents, felled trees, time, home

### Known gaps
- Building kit is the interim KayKit Dungeon look (D-007); gable ends of roofs are open
- No sound yet
- Wreck is kitbashed debris, not a real hull (waiting for a ship model)
- Real-phone frame rate not measured yet

## Phase 2 — Wild ⏳ blocked on art
Burr-hound (night threat), Kelp-back (haul tame), Cliff-glider (opens the overlook). Needs animal models: Quaternius animal pack requested from Jon.

## Phase 3 — Bloodline ⏳
Breeding per `Docs/MUTATION_LINEAGE_RULES.md`. Data model can be built before art.

## Phase 4 — Followers ⏳
Bound / Ally / Hire per `Docs/FOLLOWERS_RULES.md`. KayKit Adventurers can stand in for the two island cultures.
