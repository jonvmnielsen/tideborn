# Decisions

## D-001 — Browser/mobile version in three.js (2026-10-09)
Jon wants to build and test Tideborn on his phone and in the browser. The Unreal project needed his PC for every playtest, and the cove art pass stalled across ten iterations. A three.js version lives in `web/` and deploys to GitHub Pages on every push. The Unreal project stays in the repo untouched. The locked design docs in `Docs/` still apply; only the engine and camera change.

## D-002 — Camera: 3/4 top-down instead of third person (2026-10-09)
Thumb controls make a free third-person camera hard to use. A fixed 3/4 camera that follows the player suits gathering, building and creature work on a phone.

## D-003 — Art from the shared game-assets library (2026-10-09)
No code-built primitive art. Models come from `jonvmnielsen/game-assets` (KayKit + Quaternius, CC0). The game copies only what it uses via `web/assets.json` and the library's sync script. The earlier Burr-hound and Kelp-back blockouts are retired; new creatures will be made for the library.
