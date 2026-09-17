# Tideborn free art pipeline

## Sources and licensing

The shore art pass uses **CC0** assets from [Poly Haven](https://polyhaven.com/) and [ambientCG](https://ambientcg.com/): PBR shore sand/rock/bark/wood/ground sets, a Poly Haven beach HDRI, and coastal rock/tree-prop source meshes. The detailed source list and URLs are in `RawArt/CC0/manifest/FREE_ASSETS.md`.

## Project paths

- Source packages: `RawArt/CC0/`
- Unreal textures: `Content/Tideborn/Art/Textures/`
- Unreal materials: `Content/Tideborn/Art/Materials/`
- Unreal meshes: `Content/Tideborn/Art/Meshes/`
- Unreal HDRI: `Content/Tideborn/Art/HDRI/`
- Import script: `Tools/art/import_cc0_to_ue.py`
- Import report on Jon's PC: `Tools/art/import_cc0_result.txt`

The importer creates these material assets when run successfully: `M_Tideborn_RockShore`, `M_Tideborn_RockBoulder`, `M_Tideborn_Sand`, `M_Tideborn_Bark`, `M_Tideborn_Wood`, `M_Tideborn_Ground`, `M_Tideborn_WoodACG`, `M_Tideborn_BarkACG`, and `M_Tideborn_RockACG`. It imports the coastal FBX source meshes (`coast_land_rocks_02_1k` and `coast_land_rocks_03_1k`), imports the selected HDRI, places a small readability sample near PlayerStart, and attempts the existing-level lighting pass (directional light, skylight, and height fog). The script is intentionally repeatable and uses replace-existing imports.

## Verification status

The CC0 source package is present locally. This checkout did not contain `import_cc0_result.txt`, a running `UnrealEditor-Cmd`, or generated `Content/Tideborn/Art` assets, so the final UE material/mesh counts and whether lighting tweaks actually ran must be confirmed from the report on Jon's PC rather than claimed here.

The script's intended lighting log is `lighting tweaked (directional/skylight/fog)`. If the report shows a missing source or import failure, rerun the script once from Unreal Editor-Cmd after confirming the raw package is available.

## Fab / Megascans status

Fab browser checking was inconclusive. The local Epic vault is empty, and no claimed Megascans assets were found locally. This pass therefore relies on the CC0 Poly Haven and ambientCG sources above; no Fab/Megascans dependency is asserted.

## PIE playtest note

Open `Content/ThirdPerson/Maps/ThirdPersonMap` and press **Play In Editor**. Start at the existing PlayerStart and look toward the shore/building area for the imported sample props, updated shore materials, HDRI/skylight, and fog. If `Content/Tideborn/Art` is still empty, run `Tools/art/import_cc0_to_ue.py` once in Unreal Editor-Cmd first, then reopen the map and PIE.

## Import status (2026-09-17)

Imported on Jons-PC into `Content/Tideborn/Art`:
- Materials: `M_Tideborn_RockShore`, `RockBoulder`, `Sand`, `Bark`, `Wood`, `Ground`, ACG variants
- Meshes: `boulder_01_1k`, `coast_land_rocks_02_1k`, `coast_land_rocks_03_1k`, `dead_tree_trunk_1k`
- HDRI: `PH_industrial_sunset_puresky`

Fab/Megascans: skipped for now (Epic sign-in declined). CC0-only path.

Playtest: open ThirdPersonMap, PIE near spawn — look for TidebornShore_* rocks/trunk and warmer directional light.
