# CLAUDE.md — Tideborn

Island survival game by Jon (non-technical director; talk to him in Danish). Two versions live here:

- `web/` — **active**: three.js browser/mobile game, deployed to https://jonvmnielsen.github.io/tideborn/ by `.github/workflows/pages.yml` on every push to `main` touching `web/`.
- Unreal project (`Source/`, `Content/`, `Config/`, `Tideborn.uproject`) — paused, see DECISIONS.md D-001. Don't modify it unless Jon asks.

## Rules
- `Docs/` are locked design docs. Follow them; amend deliberately with Jon, never silently.
- Art comes from the `jonvmnielsen/game-assets` repo only. Add models to `web/assets.json`, run `npm run sync-assets` (needs game-assets cloned next to tideborn), commit `web/public/assets/`. Never build characters or props from code primitives.
- Record engine/architecture choices in `DECISIONS.md`.
- Test before pushing: `npm run build`, then load `web/dist` in headless Chromium (swiftshader) and check console errors and a screenshot at phone (390×844) and desktop size. Swiftshader runs at very low fps, so wait on game state (`window.__tideborn`) instead of wall-clock time.

## web/ architecture
See `web/README.md` for the file map and `STATUS.md` for progress against the slice. Key facts:
- Island = generated heightfield (`world/terrain.js`), 520 m square, 2.5 m grid, sea level 0. South = +z (shore, spawn, wreck), north = −z (ridge, tower).
- Every tree/rock/reed is a node in `world.nodes`, drawn through chunked instancing (`world/scatter.js`); hiding = shrinking the instance in place.
- Collision: circles and oriented boxes in a spatial grid (`world/collide.js`); boxes can have `top` (steppable) and `bottom` (walk under). Walkable raised surfaces (floors, stairs) live in `Surfaces`.
- Building grid is 4 m, world-aligned; foundations at level 0, lofts/roofs at levels of 4 m. Edges keyed `x:i,j,k` / `z:i,j,k`.
- Data-driven: `src/data/items.js`, `recipes.js`, `build.js`, `harvest.js`.
- `window.__tideborn` exposes everything for tests (world, player, gather, building, inv, dayNight, ui...).
