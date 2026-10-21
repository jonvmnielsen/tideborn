# Status

_Last updated: 2026-10-21_ · Play: https://jonvmnielsen.github.io/tideborn/

**Now (D-025):** new direction — a giant, mysterious island (bigger animals, no farm animals or dogs). Capture with a club → bind → wake → lead → captive post → træl; trælle never leave or eat but do less than allies (who follow, fight and have skills). Carrying in units; levels with six stats and stamina. Before that (D-020–D-024): base building, hunting and health, taming, followers, breeding. Almost everything can be attacked: crabs, reef fish and butterflies die to a swing (crab and fish give a little meat and XP, and come back later); strangers (Jens, Mads, Ida) get a warning blow first, then fight back and become fair game. **D-027:** tame hinds and giant stags can be ridden ("Rid" in their panel; twice your sprint, no stamina). **D-026:** the day goes round (20 min; dark nights with stars and moonlight; sleep in a bed to skip the night), packs of night raptors (Quaternius velociraptor for now) that circle and dart in one at a time but stay out of firelight, animals as data (`species.js`), credits for CC BY models, and a phone budget (~30 % fewer triangles). Next: giant creatures from Sketchfab (CC BY, curated list sent to Jon — waiting for the zips) and the story concept (on hold, Jon's call).

**Look test** for the new direction (tropical volcano island, stylized adult low poly, first person, living jungle with animals, arms holding the machete, gathering with carrying limits, bags, crafting and saving, and two castaways — D-012–D-016): https://jonvmnielsen.github.io/tideborn/cove.html — the game below is the previous direction until it is rebuilt.

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
- Player is the Quaternius Modular Men adventurer (D-011): realistic proportions but low-poly flat colours; no sit/lie/jump clips (falls back to idle/death pose). Building kit is still KayKit (D-007)
- Gable ends of roofs are open
- No sound yet
- Real-phone frame rate not measured yet (headless: ~0.4 M triangles/frame on phone settings); download ~26 MB

## Phase 2 — Wild ⏳ blocked on art
Burr-hound (night threat), Kelp-back (haul tame), Cliff-glider (opens the overlook). Needs animal models: Quaternius animal pack requested from Jon.

## Phase 3 — Bloodline ⏳
Breeding per `Docs/MUTATION_LINEAGE_RULES.md`. Data model can be built before art.

## Phase 4 — Followers ⏳
Bound / Ally / Hire per `Docs/FOLLOWERS_RULES.md`. KayKit Adventurers can stand in for the two island cultures.
