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

## D-015 — First-person arms and gathering in the look test (2026-10-12)
Jon: a machete floating on its own doesn't work — a hand must hold it, with real animations later — and gathering should come in now.
- **Arms** (`cove/hands.js`): the player's own arms from Quaternius Modular Character Outfits (peasant sleeves; only the arms mesh is drawn; same 65-bone rig as the Universal Animation Library, so authored clips can replace the procedural poses later). Poses are keyframed in camera space as "where the machete is and which way blade and edge point"; the arms follow by two-bone IK, the right hand is turned so the knuckles run along the handle and the fingers close around it, the left hand hangs out of view or reaches. Animations: idle (breathing, walk sway), swing (wind-up, cut, recover — the hit lands mid-cut), pick-up (left hand reaches down and forward). On narrow screens the hands move toward the middle.
- **Gathering** (`cove/gather.js`): the nearest gatherable thing in front within reach (2–2.3 m) is the target; a ring crosshair, its name and a progress bar show what a click does. Palms (5 cuts), young palms, bamboo and tree ferns fall over away from you (palms drop coconuts); banana plants, bushes and big leaves are cut; ground cover (grass, ferns, bromeliads, flowers) is cut when you look down at it; stones, driftwood and coconuts are picked up; the camp's crates and barrels open once. Canopy trees are too big for the machete (needs an axe later). Items: wood, palm leaves, fibre, bamboo, stone, coconuts, bananas, rope — shown in an inventory strip with icons rendered from their models, plus "+2 Træ" toasts.
- Controls: desktop left click = cut / pick up, E = pick up; phone: one action button (Hug / Saml / Åbn).
- Sounds: Kenney (CC0) cut, slice, swish, wood impacts, pick-up, crate and grass footsteps; Sonniss tree fall.
- Not saved yet; nothing regrows yet.

## D-016 — Carrying, bags, crafting, sweeping cuts, saving; castaways with faces (2026-10-12)
Jon: the machete must be held upright in front; finds belong in a backpack, not on screen; carrying needs a natural limit, and bags of different kinds should be made and found; a swing should cut everything in a radius and angle, not one aimed thing; the sky haze blurred the horizon.
- **Machete upright** in front (edge forward), the hand fully in view; on narrow screens the hands sit nearer the middle.
- **Sweeping cuts** (`gather.js`): a swing hits everything within 2.6 m and ±70° in front — a swathe of grass, several bushes, the palm beside you. Things you pick up (stones, driftwood, coconuts, piles, crates) still need you to look at them.
- **Carrying** (`inventory.js`): every item has a weight; without a bag you carry 8 kg. Palm-leaf pouch (+6 kg) and bamboo basket (+14 kg) are made; a canvas backpack (+24 kg) is found in one of the washed-up crates. What doesn't fit is left in a pile on the ground to come back for.
- **Bag panel** (Tab / I, or the bag button with the load, top right): contents with icons, drop, hold a tool, and recipes — rope (fibre), stone axe (stone, wood, rope), the two bags, a lean-to kit. Nothing is shown on screen otherwise except short "+2 Træ" notes.
- **Stone axe**: fells the rainforest trees (8 cuts, giants 14) and cuts palms faster; Q (or the tool button) switches tool.
- **Lean-to**: made from bamboo, palm leaves and rope, then placed in front of you.
- **Regrowth and saving**: cut plants come back (grass after ~2½ min, palms ~15 min); inventory, what's cut, piles, opened crates and built shelters are saved in the browser (`localStorage`), "Start forfra" in the bag panel clears it.
- **Clearer air**: bloom only on really bright things (lava, glints), lighter fog, a cleaner blue horizon.
- **Castaways** (`npc.js`): two fellow survivors at the camp, assembled from Quaternius parts on one rig — outfit (peasant / ranger), the head of the Universal Base Characters body (only head and neck triangles kept, the outfit covers the rest), beard, hair, eyebrows (grey in the free pack, tinted here) — animated with Universal Animation Library clips: one walks the beach and talks, one kneels by the boat.

## D-017 — First-person arms from the forge instead of a character's arms (2026-10-12)
Jon: the hand still looked strange. The borrowed third-person arm (D-015) deformed at the wrist when posed by IK, its fingers never really closed (the animation library's hands are open in every clip), and its smooth textured look clashed with the faceted island. Now the arms are our own rigid faceted pieces (game-assets `forge-lowpoly`: `fp_fist`, `fp_hand`, `fp_forearm`, `fp_upperarm`): a fist modelled closed around a handle (it rides on the tool, so it grips the machete and the axe the same way), an open hand for reaching, forearms with rolled linen sleeves and a leather wrist band, upper arms in the sleeve. The same camera-space keyframes and two-bone IK place them; nothing bends, so nothing can look rubbery. The Quaternius rig stays for the castaways.

## D-018 — First-person arms: PSX First Person Arms (drillimpact, CC0) (2026-10-12)
Jon: the forge arms (D-017) weren't good either — get assets. He downloaded the two free CC0 viewmodel packs found: PSX First Person Arms (drillimpact; 18 clips by its author) and WRAD ARMS (wriks; rig only). Tideborn uses the PSX arms because they come animated:
- The rig is authored in glTF space looking along +z with its "camera" bone at the eye; every frame it's turned to face our camera and the eye bone is put on the camera (`hands.js` `fit`). It's lifted (see amendment) so the hand and tool sit in our narrower view, and moved toward the middle on portrait screens.
- The machete (or stone axe) sits in the right hand bone, handle in the fist. Clips: `knife_draw` when a tool comes out, `knife_idle` while holding, `knife_hit_01` / `knife_hit_02` alternating on each cut (the sweep lands about a third in), `grab.L` for picking up with the left hand while the right keeps the tool. Walk sway on top.
- The pixel-art texture keeps nearest-neighbour filtering. The forge arm pieces stay in the library but are no longer used. WRAD ARMS is in the library as an alternative.
- Amended 2026-10-12 (Jon: "the hand must hold the machete, not have it go into the hand"): the tool mount sits in the hole of the closed fist (hand-bone space (−0.012, 0.085, 0), measured from the finger joints) and the handle runs across the fist along the knuckle line, blade out above thumb and index. The knife clips hold a short knife flat across the body, so after each animation frame the forearm is rolled 0.9 rad about its own axis and the wrist bent −0.4 rad (`hands.js` `twist`) — the machete then stands upright in front of you, leaning slightly forward. The tool is turned about its round handle so the edge faces forward and a little of the flat shows. Arms lifted 17 cm and moved 8 cm forward so the fist is in view at idle.

## D-019 — First-person arms drawn as a viewmodel, small in the lower right (2026-10-14)
Jon: the weapon and hands were far too big — ideally only in the lower-right quarter of the screen; look at what other games do. Most first-person games draw the arms and weapon as a separate "viewmodel": their own camera and field of view, drawn after the world with the depth cleared, so the world's FOV can change without changing the gun, and the gun never cuts into walls (CS2 `viewmodel_fov` 54–68, where a higher value "pushes the gun smaller and further into the corner"; the Bevy and Unity viewmodel examples render the arms on their own layer with a fixed FOV). Tideborn does the same:
- The arms and tool are on layer 1 and drawn by `ViewmodelPass` (after the world, before bloom) through `hands.view`, a camera on the eye with its own lens: `VIEW.fov` = 110° across the screen's shorter side, plus a lens shift `VIEW.shift` = (0.25, −0.3) screen halves (right/down; x scaled by the aspect on portrait). At rest the hand and the whole machete sit in the lower-right quarter on desktop and phone; a cut sweeps out of it and back.
- The sun and sky light also light layer 1, so the arms are lit like the world. They cast no shadows.
- The knife clips hold the left arm out in front as a guard. It is folded away (upper-arm bone scaled to nothing, so it vanishes into the shoulder behind the eye) and only comes out to pick things up (`grab.L`).
- The holder lift from D-018's amendment is back to 7.5 cm; framing is now the viewmodel camera's job.

## D-020 — Cut from the right, ARK-style carrying, base building (2026-10-14)
Jon: the weapon faced the wrong way and cut the wrong way (it must come from the right toward the middle); arms and weapon 10 % bigger and entering lower; the weight limit felt annoying (how does ARK do it?); "you must be able to build a whole base". He also asked that low poly gets a high budget so it doesn't look cheap.
- **The cut** is our own motion on top of `knife_idle` (the PSX knife clips cut from upper left to lower right): the arm draws back to the right, sweeps in toward the middle and down, and returns (`hands.js` `CUT`, hit at 0.25 s). The tool is turned so the edge faces the middle and leads. Viewmodel lens `VIEW.fov` 105°, shift (0.25, −0.38).
- **Carrying, after ARK** (ark.wiki.gg/wiki/Weight: you start around 100, wood weighs 0.5 and fibre 0.01; above ~50 % you slow, at ~85 % you're encumbered, at 100 % you can't move): you carry 100 kg, bags add 30 / 75 / 150, resources weigh 0.01–0.5 kg. Picking up is never refused; above 60 % you walk slower, above 100 % you trudge at 35 % and can't run.
- **Base building** (`src/cove/build.js`): a world-aligned 3 m grid with 3 m storeys. Foundations on stilts (the stilts reach the ground, so slopes work), walls / doorways / windows / railings on foundation and floor edges at any storey, doors and gates that hang in their frames and swing away from you, floors (loft = next storey), thatch roofs with automatic gables, stairs, pillars, palisades that join end to end, gate frames, campfire and torches (two pooled fire lights), bed (where you wake) and chest (storage). Aim with the crosshair; green/red ghost with a reason; R turns, right click / Esc / ✕ stops; tear-down gives everything back. You climb decks up to 1.05 m (no jump), walk on floors and stairs; walls, closed doors and fences stop you. Saved with the rest. The kit is ours (game-assets forge-lowpoly `b_*`, ~1–5k triangles a piece).

## D-021 — Health, hunting and the first threat with known animals (2026-10-14)
Step 2 of the plan Jon approved ("run all five steps, one at a time, test before the next; known animals, not invented species"). The design brief's invented roster (Kelp-back, Burr-hound…) is set aside for now.
- **Animals** (`src/cove/creatures.js`) are data: model, height, health, walk/run speed, behaviour (`prey` bolts when you come close or hit it and the herd bolts with it; `territorial` charges if you come too close, bites, turns away; `hostile` hunts you within its range, wider at night, until you leave its home or it is badly hurt) and loot. Skinned Quaternius animals (CC0) with their own clips; the death fall is procedural (the clips have none). Now on the island: two herds of hinds, a red stag that guards the first herd, two foxes. Dead animals come back after 10 minutes.
- **Combat**: a swing that catches an animal in its arc hurts it (machete 18, stone axe 26) — it flinches and bleeds chips. A felled animal is butchered with E / a tap for meat and hide.
- **Health** (`vitals.js`): 100, bar top left, red edge flash on a bite, slow regeneration after 8 s unhurt, eating heals (banana 8, coconut 12, raw meat 6, cooked meat 30). At 0 you black out: everything but tools and bags stays in a pile where you fell, and you wake in your bed (or on the beach) with 60.
- **Food and gear**: cooked meat is made by a campfire (recipes can need a station), a hide backpack (+110 kg) from four hides.
- Waiting on Jon's Quaternius animal packs for the real night threat (feral dogs / wolves) and wild boar.

## D-022 — Taming: earn its trust with food; the first tame is a pack animal (2026-10-14)
Step 3. Readable taming as the brief asks (find → prepare → secure → bond → utility), without opaque timers:
- **Find and prepare**: each tameable species likes certain food (hind and stag: bananas or coconuts). Looking at one tells you what it eats.
- **Approach**: with that food in your bag and walking (not running) a wild animal lets you come close instead of bolting — the stag doesn't charge. Running, or hitting it, breaks the trust.
- **Bond**: feed it from your hand (E / tap; hind 4 times, stag 7). The last feeding makes it yours and it gets a name.
- **Utility — haul**: a tame animal carries for you in its saddlebags (hind 60 kg, stag 140 kg; E / tap opens them like a chest). It follows a few metres behind (runs to catch up, comes to you if you get far away) or stays where you tell it. Tame animals can't be hurt by your swings, and are saved with their name, mode and load.
- When Jon's Quaternius packs arrive the same system takes the horse / donkey (haul and later riding) and the dog (guard).

## D-023 — Followers: Ally by earning, Bound by force (2026-10-14)
Step 4, after `Docs/FOLLOWERS_RULES.md` (slice scope: one Ally and one Bound end-to-end with a readable benefit each; identities never convert; the critical path needs no followers). Hire is left for later. People are Quaternius outfits + base heads with the Universal Animation Library (both CC0); more clips loaded (jog, punches, hits, death, getting up, chopping, carrying, folded arms, sitting).
- **Earn → Ally**: Ida lies hurt on the east beach — give her three meals and she gets up and joins. Mads mends his boat by the camp — bring 2 rope and 6 wood. Allies start at loyalty 60, ceiling 95; only allies can follow you ("Følg"), and they fight animals and raiders that go for you.
- **Force → Bound**: two raiders (Rask, Vibe) camp on the west headland and attack anyone who comes close. Beat one down (non-lethal) and bind them with a rope within 45 s, or they get up. Bound start at 25, ceiling 65, gather 50 % more for food alone, and as guards keep charging animals away from their post — but they never follow you, and a bound one whose loyalty falls below 15 from hunger runs back to the raiders.
- **Roles**: Følg (allies), Saml (walk to something growing near their post, chop, carry it back into the nearest chest), Vagt (stand at the post and fight what comes near), Hvil. E / tap on a follower opens their orders: identity badge, loyalty against its ceiling, role, "give food now".
- **Upkeep**: every 5 minutes each follower eats — from a chest near their post, or your bag when they walk with you; fed +6 loyalty, unfed −12.
- Jens still walks the beach (no path yet). The old fixed castaways are replaced by this.

