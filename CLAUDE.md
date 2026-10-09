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
See `web/README.md` for the file map. Key facts:
- World scale `WS = 4` (KayKit hex pack is board-game scale). Hex tile ≈ 8 m flat-to-flat.
- Coast pieces are matched automatically: `World.measureTiles` raycasts each coast model at all 6 rotations to learn which edges are water, and `fitTile` picks the piece whose water edges match the neighbors.
- Walking uses baked per-tile height grids (`TileHeights`), not physics. Colliders are circles.
- Ocean color and foam come from a distance-to-land field baked at load.
- `window.__tideborn` exposes world/player/nodes/inventory for tests.
