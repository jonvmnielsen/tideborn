# Tideborn

Working title for an island survival game.

**▶ Spil i browseren / på telefonen:** https://jonvmnielsen.github.io/tideborn/

Island Ecology (speculative evolution) · base building · exploration · creature mastery (taming + breeding/mutations) · humanoid Followers (Bound / Ally / Hire).

## Status

**Browser/mobil v0.2 — Phase 1 Camp spilbar** (`web/`, three.js): stor ø med kyst, skov og højderyg, alle træer kan fældes, crafting, modulært byggeri, dag/nat, sult, gemning. Se [`STATUS.md`](STATUS.md) og [`web/README.md`](web/README.md).

Unreal-versionen er sat på pause (Phase 2 Wild, greybox). Se [`DECISIONS.md`](DECISIONS.md).
Design docs in [`Docs/`](Docs/) are locked planning artifacts and apply to both versions. Quality over speed.

## Pillars

- Exploration
- Base building
- Creature mastery (selective breeding primary strength ladder; mutations extra layer; never gates critical path)
- Follower mastery (Bound vs Ally permanent identities; Hire with wages)

## Docs

| Doc | Status |
|-----|--------|
| [DESIGN_BRIEF.md](Docs/DESIGN_BRIEF.md) | Plan locked |
| [MUTATION_LINEAGE_RULES.md](Docs/MUTATION_LINEAGE_RULES.md) | LOCKED v2 |
| [FOLLOWERS_RULES.md](Docs/FOLLOWERS_RULES.md) | LOCKED v2 |
| [ART_DIRECTION.md](Docs/ART_DIRECTION.md) | LOCKED v1 |
| [EXECUTION_PLAN.md](Docs/EXECUTION_PLAN.md) | LOCKED v1 |

## Engine

**Aktiv:** three.js i `web/`, deployet til GitHub Pages ved hvert push. Grafik fra [game-assets](https://github.com/jonvmnielsen/game-assets).

**På pause:**
- Unreal Engine **5.4.4** (Third Person Blueprint template + Tideborn C++ module)
- Blueprints-first systems; small C++ for input/interact foundation
- Third-person camera

## Phase 0

- [x] UE project in repo
- [x] `IA_Interact` mapped to **E**
- [x] World stub `Tideborn_InteractStub` (TriggerBox)
- [x] `UTidebornInteractComponent` on `BP_ThirdPersonCharacter` (line trace + on-screen message)

**Verify:** open `Tideborn.uproject`, Play, walk toward the stub near spawn, press **E** — cyan/yellow debug text + trace line.

## License / IP

Original IP. Genre-inspired only — do not clone protected content from other games.
