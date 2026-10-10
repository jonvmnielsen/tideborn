# Decisions

## D-001 — Browser/mobile version in three.js (2026-10-09)
Jon wants to build and test Tideborn on his phone and in the browser. The Unreal project needed his PC for every playtest, and the cove art pass stalled across ten iterations. A three.js version lives in `web/` and deploys to GitHub Pages on every push. The Unreal project stays in the repo untouched. The locked design docs in `Docs/` apply to the web version; only the engine changes.

## D-002 — Camera: third person, as the design says (revised 2026-10-09)
v0.1 used a fixed 3/4 top-down camera. Jon asked to follow the design, which locks third person. The camera now orbits behind the player: right thumb (or mouse drag) turns it, and it eases back behind the player while walking.

## D-003 — Art from the shared game-assets library (2026-10-09)
No code-built primitive props or characters. Models come from `jonvmnielsen/game-assets` (KayKit + Quaternius, CC0). The game copies only what it uses via `web/assets.json`. The earlier Burr-hound and Kelp-back blockouts are retired; new creatures will be made for the library.

## D-004 — Terrain is a generated heightfield, not hex tiles (2026-10-09)
Jon rejected the KayKit board-game hex tiles: too small, reads as a board game. The island is now a ~360 m low-poly heightfield with the three bands from ART_DIRECTION (shore with wreck in the south, forest belt in the middle, terraced ridge with the overlook tower in the north). Terrain is ground, not a prop, so generating it in code does not conflict with D-003. Colors follow the KayKit palette.

## D-005 — Every tree is a gatherable node (2026-10-09)
Forest clumps from the hex pack are gone. Forests are made of single trees, each one choppable, regrowing after a few minutes. Instanced per 64 m chunk so the view and shadow frustums can skip chunks.

## D-006 — Early progression: hands → stone axe → pick (2026-10-09)
Bare hands gather dead branches, loose stones, reeds and washed-up supply crates. A stone axe fells trees; a pick breaks boulders. This is the "basic tools → better gather" chain from DESIGN_BRIEF §3.2.

## D-007 — Interim building kit from KayKit Dungeon (2026-10-09)
ART_DIRECTION wants driftwood timber, lashed fiber and stone footings with pitched roofs. KayKit has no such kit. Until Quaternius building packs are in the library, the kit uses KayKit Dungeon stone-and-timber walls, wood floors on stone footings, and a pitched roof made of tilted plank floors. Same 4 m grid, so pieces can be swapped later without breaking saves.

## D-008 — Washed-up supplies as the food source (2026-10-09)
No animal or plant food models yet. Supply crates wash up on the beach and are refilled by the tide every morning (fits "Tideborn"). Hunting and cooking come with creatures.

## D-009 — Build mode moves a cursor, not the player (2026-10-10)
Jon found placing pieces by walking the character around too fiddly. In build mode the left stick (WASD) moves a cursor and the camera orbits it; the player stays put and only walks after the cursor if it gets more than 11 m away. Pieces snap to the nearest valid spot around the cursor and prefer what the camera faces: next to existing foundations the empty neighbour in the view direction wins, and at a corner the wall edge you look at face-on wins. ▲/▼ pick the floor level (for foundations: raise/lower in 0.5 m steps, footings stretch to the ground, up to 4.5 m). Walls can stack on walls; fences join end to end or at right angles.

## D-010 — Style B: scanned materials, generated trees (2026-10-10)
Jon wants adult games and found the KayKit/Quaternius look childish; he chose direction B (detailed real surfaces on simple shapes), free assets only. Recorded in ART_DIRECTION §13a and game-assets D-009. In the web version:
- **Ground**: smooth heightfield with a custom material (`world/ground.js`) blending four Poly Haven texture sets (sand, grass, forest floor, rock) by per-vertex weights from height, slope and biome; world-space projection, side projection on cliffs, height-based blend edges, two-scale sampling against tiling. Replaces the flat-shaded vertex colours of D-004.
- **Light**: Poly Haven sky HDRI as image-based light (`scene.environment`), scaled by the day/night cycle; lower exposure and a less saturated sea.
- **Trees** (ez-tree, generated) and **rocks** have two versions: full models for the nearest ones (≈45 m desktop / 30 m phone, capped) and cheap cards / simplified rocks beyond (`Scatter` LodSet). Stumps live in a pool that only draws shown stumps. Measured ~0.7 M triangles per frame on desktop and ~0.4 M on phone, shadows included.
- **Landmarks**: a Poly Haven ship hull heeled over on the beach (sails removed), the giant oak, a stone fort half sunk into the ridge as the overlook ruin, mossy boulder crags.
- **Gathering**: driftwood and dead trees for wood, nettles and ferns for fiber (replacing reeds), scanned stones, wooden crates for washed-up food. Campfire is a stone fire pit, chest a wooden chest.
- Saves keep buildings and inventory; felled-tree state is only restored on the same flora layout (`floraVersion`).
- Download is ~26 MB (was ~6 MB): 1024 px textures on big rocks and the ship, 256–512 px on small things.

