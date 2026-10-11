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

## D-011 — Player: Quaternius Modular Men "adventurer" (2026-10-10)
The big-headed KayKit barbarian clashed with style B. Interim player until a style-B character exists: the adventurer from Quaternius Ultimate Modular Men (CC0, realistic proportions, beard and work clothes, ~8k triangles). Its clips are mapped by role in `player.js` (walk → Walk, chop → Sword_Slash, sleep → Death held at the end…), so another model can be dropped in. The stone axe is the Zombie Apocalypse Kit axe, placed in the right hand from the finger bones. The camera sits closer (8 m desktop, 9 m phone) for the smaller figure.

## D-012 — Tropical start, first person, Stranded Deep as the target (2026-10-11)
Jon found the style-B island still not good enough and named Stranded Deep as the look he wants. Decisions: the start area becomes a tropical, lush island (other biomes later), and the game goes **first person** (DESIGN_BRIEF and ART_DIRECTION amended, §13b). Before rebuilding the game, a separate look test proves the target in the browser: `web/cove.html` (`src/cove/`), with its own asset list `assets.cove.json` synced to `public/cove/` so the game's download is unchanged.
- Sea (`cove/ocean.js`): MeshStandardMaterial + Gerstner waves; depth from the island heightfield (signed, so the swash and foam follow the real waterline); turquoise→blue by depth, transparency in the shallows, lacy shore and crest foam, toned-down sky reflection in the shallows, caustics on the sand below.
- Sky (`cove/sky.js`): three's physical sky graded toward a clear tropical blue, drifting cloud layer, sun + image-based light from the same sky; four times of day.
- Island (`cove/island.js`): a real island in deep water — crescent beach, lagoon, jungle hill, rocky headlands.
- Flora (`cove/flora.js`): generated palms (our generator), ez-tree broadleaf trees tinted tropical, Poly Haven Smuggler's Cove rocks/cliff/plants, Dutch ship wreck, cannon, chest, crates, shells; wind sway on all plants; small plants are drawn only near the player; far tree cards matte (Lambert).
- First person (`cove/fps.js`): mouse look with pointer lock / two-thumb touch, wading slows you, machete in hand.
- Measured (headless): ~1–1.4 M triangles desktop on the beach (2 M deep in the jungle), ~0.3–0.5 M on phone settings. Download ~17 MB.

## D-013 — Stylized faceted low poly, volcano island (2026-10-11)
Jon wants to move away from realism: stylized is fine as long as it is made for adults (ART_DIRECTION §13c), with the low-poly tropical volcano island image as the target. The cove look test is rebuilt in that style; first person and the tropical start (D-012) stay.
- **Models**: our own faceted generator in game-assets (`forge-lowpoly`, its D-012): palms, rainforest canopy trees, banana, elephant ear, monstera, fern, heliconia, grass, bushes with hibiscus, rocks, cliffs, basalt, barrel, crate, rowboat, machete, driftwood. 150–1400 triangles each, vertex colours, no textures; palms and canopy trees have far versions. The cove's models went from ~15 MB to 0.7 MB.
- **Island** (`cove/island.js`): a volcano (150 m, crater with a lava lake, gullied flanks, six lava runs) behind the jungle. The ground is one mesh of hard facets with one colour per triangle (sand, grass, jungle, olive rock with moss, ash, basalt, lava); triangles under deep water are skipped. Lava glows through an emissive vertex attribute (`cove/facets.js`).
- **Sea**: same Gerstner sea with stylized colours, flat per-triangle normals near the camera (smooth far away) and crisper, graphic foam; ~3 m facets.
- **Light**: neutral tone mapping (ACES greyed the colours out), a warm sand-coloured hemisphere bounce, exposure that opens up at dawn and dusk, bloom (threshold above the lit scene, so mainly lava and sun glints).
- **Smoke**: an instanced column of faceted puffs rising from the crater and drifting downwind.
- Measured (headless): ~1.0–1.15 M triangles on the beach at desktop settings (~1.6 M deep in the jungle), ~0.35 M on phone. Far trees don't render into the shadow map (`farShadow: false`; they are outside the shadow box anyway).

## D-014 — A living jungle: layered planting, ground cover, animals, sharper picture (2026-10-11)
Jon: the island felt empty — it must be an exotic, lush, living jungle island — and the picture was too low-resolution.
- **Sharper**: the bloom chain renders into a multisampled target (4× desktop, 2× phone) instead of a non-antialiased one; pixel ratio up to 2 on all devices; shadow maps 4096 desktop / 2048 phone.
- **Layered jungle** (`cove/flora.js`): emergent giant trees and canopy trees with hanging lianas, palms, bamboo groves (noise patches), tree ferns, young palms, a dense understory (banana, elephant ear, monstera, heliconia, hibiscus), mossy fallen logs. Collision circles live in a 4 m grid (placement went from linear scans to constant time).
- **Ground cover** (`cove/cover.js`): grass, ferns, bromeliads, small elephant ears and three kinds of flowers generated cell by cell from a seeded hash around the player (38 m desktop, 24 m phone), shrinking toward the edge; rebuilt when the player crosses an 8 m cell. The jungle floor gets leaf-litter and moss patches.
- **Animals** (`cove/fauna.js`): macaw and blue-parrot flocks looping over the canopy, gulls circling the lagoon (with glides), butterflies around the player, crabs dashing sideways at the waterline, three kinds of reef fish schooling in the shallows. Wings flap and tails beat in the vertex shader; all instanced.
- **Sound**: synthesized tropical bird calls (whistles, trills, squawks, gull cries, hoots) on top of surf and forest loops.
- Only trees cast shadows now (the understory sits in their shade); the sea mesh uses ~3.5 m facets.
- Measured (headless): desktop ~1.0 M triangles on the beach, ~1.6–1.7 M deep in the jungle; phone ~0.45 M beach, ~0.7 M jungle. Cove models 1.1 MB.

