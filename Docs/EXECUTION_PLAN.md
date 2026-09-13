# Execution Plan & Bot Org

**Status:** LOCKED v1 (2026-09-13)  
**Parent docs:** `DESIGN_BRIEF.md` · `MUTATION_LINEAGE_RULES.md` (LOCKED v2) · `FOLLOWERS_RULES.md` (LOCKED v2) · `ART_DIRECTION.md` (LOCKED v1)  
**Quality doctrine:** High-quality over speed. No vanity milestones. Stage gates from the design brief and [Game Dev + 3D Assets](sand-workflow:game-dev-3d-assets).

---

## 0. How we work

| Rule | Meaning |
|------|---------|
| Plan → then execute | No UE project until Jon greenlights Phase 0 |
| One engine truth | Unreal Engine 5, Blueprints-first, third-person |
| Design is law | Locked docs beat improvisation; amend docs when we change intent |
| Spin bots lazily | Create a specialist **when their phase starts**, not a full studio on day one |
| Parent owns architecture | This lead agent (chat) keeps pillars, refuses scope creep, merges decisions |
| Playtest before widen | Slice exit criteria before bosses / huge map / multiplayer |

---

## 1. Prerequisites before any bot codes

Jon + lead confirm:

1. ~~Working title~~ → **Tideborn** locked as working title  
2. Epic / UE5 version pinned  
3. Repo home (Cursor Origin / GitHub / local-only)  
4. Machine that can run UE5 editor (Jon’s PC vs cloud limits — UE editor is heavy; expect Jon’s machine or a capable workstation for editor work; bots assist design, docs, Blender assets, Blueprint plans, reviews)  
5. Greenlight: “Start Phase 0”

**Honest constraint:** Full UE editor play isn’t something every agent desktop can replace. Execution mix = **design/docs/automation here** + **UE work on a machine with the editor** + **cloud coding agents for repo** when connected.

---

## 2. Phase roadmap (execute in order)

### Phase 0 — Foundations (lead + optional Repo bot)
**Exit:** Runnable empty third-person character, Enhanced Input, interact trace stub, folder hygiene, README pinning UE version + links to design docs.

- Create UE5 project (third-person template or blank + character)  
- Map design docs into `/Docs` in repo  
- Input + camera baseline per lock  
- Logging / debug draws for interact  

**Bots:** Lead only (or **Harbor** repo steward if repo is live).

### Phase 1 — Camp loop
**Exit:** Gather → craft minimal → modular snap build (kit greybox OK if art gate dated) → save/load inventory + builds.

**Bots:** **Keel** (UE systems), **Spline** (modular kit / Blender blockout).

### Phase 2 — Wild
**Exit:** Burr-hound threat + one useful tame (Kelp-back or Cliff-glider) with utility gate to a landmark.

**Bots:** **Keel**, **Marrow** (creature AI/taming), **Spline** (creature blockout).

### Phase 3 — Bloodline + Followers (can overlap carefully)
**Exit:**  
- Breeding thin path per mutation rules v2 (purebred strength climb + optional mutation)  
- Followers v2: one Bound + one Ally proven; Hire optional  

**Bots:** **Keel**, **Marrow**, **Oath** (Followers dual-path), playtest **Rove**.

### Phase 4 — Slice lock (art + feel)
**Exit:** Art direction v1 bar inside slice; audio feedback; perf pass; bug list; all slice acceptance tests green.

**Bots:** **Spline**, **Marrow**, **Rove**, **Bar-Island** (quality gate — name distinct from Snow Melt Bar).

### Phase 5+ — Widen / Horizon
More species, building tiers, biome 2, bosses, huge map, multiplayer eval — **separate addenda**, new bot loadout then.

---

## 3. Bot org (proposed specialists)

Create only when needed. Names are working titles — rename freely.

| Bot | Lane | When to spin up | May code? |
|-----|------|-----------------|-----------|
| **Lead (this chat)** | Pillars, priorities, doc locks, integration calls | Already | Yes (orchestration, docs, reviews) |
| **Harbor** | Repo hygiene, PR small docs, version pins | Phase 0 if repo exists | Docs / repo only |
| **Keel** | UE systems: inventory, craft, build, save, data assets | Phase 1 | Yes — Blueprints/systems |
| **Spline** | Blender→UE modular kit + landmark blockouts; texel/pivot discipline | Phase 1 | Art pipeline; no random scope |
| **Marrow** | Creatures: AI, tame, breed/mutation data per locked rules | Phase 2–3 | Yes — creature systems |
| **Oath** | Followers Bound/Ally/Hire per locked v2 | Phase 3 | Yes — NPC/follower systems |
| **Rove** | Playtest: exploration feel, softlocks, “is breeding tempting?”, Force vs Earn spice | Phase 2+ | No production features; reports only |
| **Bar-Island** | Quality gate vs design + art exit criteria | Phase 4 | Fail/pass only; may request fixes |

**Do not** reuse Snow Melt playtest bots for this IP — different project, different bar.

### Collaboration rules
- Lead assigns **one vertical** at a time per bot (no “build the whole game”).  
- Bots read locked docs before proposing changes.  
- Rule changes go through Jon + Lead → doc amend → then code.  
- Rove/Bar-Island never “just ship” around a failed gate.

---

## 4. First 10 execution tickets (after greenlight)

1. Pin UE version + create project + third-person pawn  
2. `/Docs` copy of locked design set  
3. Enhanced Input move/look/interact  
4. Item data asset + inventory component  
5. Gather node → add to inventory  
6. Snap build ghost (foundation/wall) greybox  
7. Save/load inventory + placed pieces  
8. One landmark blockout + path from shore  
9. One tameable + one threat stub  
10. Playtest note template for Rove  

Tickets 8–10 start Phase 2; don’t skip 1–7.

---

## 5. Risk register

| Risk | Mitigation |
|------|------------|
| UE editor access bottleneck | Phase 0 on Jon’s UE machine; bots prep Blueprints specs + Blender assets offline |
| Scope love (bosses/map early) | Horizon backlog only; Lead veto |
| Art forever greybox | Dated art gate in Phase 1; Phase 4 fails without near-final slice art |
| Breeding/Followers spaghetti | Locked rules docs; data-first; thin path before encyclopedia |
| Too many bots at once | Lazy spawn; max ~2–3 active builders + 1 playtester |

---

## 6. Success definition for “execution started”

Not “lots of bots exist.”  
**Success:** Phase 0 exit met on a real UE5 project tied to these docs, with Jon able to move a third-person pawn and interact with a stub.

---

## 7. Open before Phase 0

1. ~~Working title~~ → **Tideborn**  
2. Repo / Epic account readiness  
3. Explicit greenlight to execute  

---

*Execution plan v1 — quality gates, lazy bot spawn, UE5 third-person slice first.*
