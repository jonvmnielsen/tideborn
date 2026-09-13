# Followers Dual-Path Rules Addendum

**Status:** LOCKED v2 (2026-09-13)  
**Parent:** `DESIGN_BRIEF.md`  
**Applies to:** Humans / humanoids only (not creature taming/breeding)  
**Hard constraints:**  
- Dual paths are both **first-class**: **Force** (capture / bind / enslave) and **Earn** (rescue / recruit; hire is contractual).  
- **Path locks on acquisition** — once Bound or once Ally (rescued/recruited), they **stay that way** for that character. No Force↔Earn conversion.  
- **Hire** is the flexible contract path: requires **upkeep/wages**; can leave if unpaid.  
- Neither path is required for the critical path.  
- Conan Exiles is a reference for capture *depth*, not a clone.  
- Distinct from creature breeding/mutations.

---

## 0. Design thesis (v2)

Followers are a **lasting moral-strategic choice**, not a temporary label.

- **Force** and **Earn (Ally)** are permanent identities for that person once acquired.  
- Each direction has **asymmetric benefits** — neither is strictly “correct”; both are spicy.  
- **Hire** spices the middle: paid help without binding someone’s fate forever.  
- The intrigue: *Do I take them, earn them, or rent help?* — and live with the mechanical profile that choice creates.

---

## 1. Acquisition outcomes (locked identity)

| Outcome | How you get it | Permanence | Upkeep |
|---------|----------------|------------|--------|
| **Bound** (Force) | Defeat → capture → bind | **Permanent** Bound identity | Food + binding maintenance |
| **Ally** (Earn) | Rescue or recruit | **Permanent** Ally identity | Food + fair treatment (morale) |
| **Hire** | Pay to contract | Until contract ends / they leave | Food + **wages** on schedule |

**No path conversion.** A Bound follower does not become an Ally through kindness grinding. An Ally does not become Bound through a dark decree. (New people can still be acquired the other way — the *character’s* path is locked.)

Faction reputation may **unlock** Ally recruits or mark camps as capturable; it does not rewrite an existing Follower’s identity.

---

## 2. Asymmetric benefits (the spice)

Both directions must feel powerful in different ways. Tune numbers in playtests; keep the *shape*.

### 2.1 Bound (Force) — benefits

| Benefit | Fantasy | Mechanical sketch |
|---------|---------|-------------------|
| **Fast labor** | Taken now, working now | Shorter break-in; earlier role access for Gatherer/Builder/Guard |
| **Cheap upkeep** | No wages | Food + restraints only — strong economy for large camps |
| **Fear presence** | Camp feels dangerous | Small passive: wild scavengers / weak hostiles less likely to idle near Bound guards |
| **Hard jobs** | They don’t get a say | Can be assigned high-risk tasks Allies may refuse (night bait, suicide holds, toxic gather) |
| **Intimidation on expeditions** | Force as a tool | Combat openers / NPC surrender chance slightly up when Bound fighters are present |
| **Numbers game** | Empire of bodies | Easier to mass low/mid labor than Ally pipeline |

**Costs that keep it spicy (not free power):** escape risk, revolt risk at low Loyalty, lower TrustCeiling, worse crafting/beast-care quality, Ally/faction reputation hits if witnessed, no access to top trust roles.

### 2.2 Ally (Earn — Rescue/Recruit) — benefits

| Benefit | Fantasy | Mechanical sketch |
|---------|---------|-------------------|
| **Higher ceiling** | Real loyalty | Higher TrustCeiling; better long-term skills |
| **Quality work** | They care | Crafting / building quality bonuses; fewer failures |
| **Beast-handler synergy** | Trust with animals | Best nursery / tame-care bonuses — ties into creature mastery side-quest |
| **Scout & knowledge** | Willing eyes | Better map pings, landmark hints, ambush warnings |
| **Social proof** | People join people | Nearby recruit chances / better hire rates when Allies are visible and happy |
| **Stable expeditions** | Won’t bolt mid-trip | No escape checks; reliable companions for exploration pillar |
| **Unique hooks** | Stories | Ally-only dialogue, side tips, optional camp events |

**Costs:** slower/rarer acquisition, food + fairness demands, no “hard job” overrides, weaker mass-labor economy than Bound spam.

### 2.3 Hire — benefits & limits

| Benefit | Limit |
|---------|--------|
| Temporary specialists without permanent moral lock | **Wages** required on schedule |
| Can fill gaps (guard while you explore) | Unpaid → Loyalty drop → **leave** (not revolt) |
| Neutral-ish reputation | Lower ceiling than Ally; no Bound fear presence |

Hire is the spice valve: power without forever.

---

## 3. Loyalty, morale, risk (by identity)

### 3.1 Shared meters

- **Loyalty** 0–100 (long-term)  
- **Morale** −20…+20 (short-term)  
- **TrustCeiling** caps Loyalty by identity  

| Identity | Default TrustCeiling | Escape | Revolt | Leave |
|----------|----------------------|--------|--------|-------|
| Bound | 55–70 | Yes | Yes (camp-scale if many Bound & miserable) | No (they flee via escape) |
| Ally | 85–100 | No | No | Rare (only if severely betrayed — design as last resort; prefer morale collapse / work refusal) |
| Hire | 70–85 | No | No | **Yes** if unpaid / contract broken |

### 3.2 Bound risk (keeps Force honest)

Escape pulses when unsupervised, at night, or during raids — modified by Loyalty, Morale, restraint quality, guards.  
Revolt if enough Bound are starving/abused — fight or mass flee.

### 3.3 Ally “betrayal” (rare)

Allies don’t convert to Bound. If systems need a break: they refuse work, demand redress, or walk away as **free NPCs** — still not enslavable *as that same locked Ally record* without treating them as a **new** capture target in the world (optional harsh rule; slice can omit re-capture of ex-Allies).

**Slice default:** ex-Ally who leaves is gone from Follower list; re-capture not required for slice proof.

---

## 4. Shared role board

Same jobs; **requirements and output** differ by identity.

| Role | Bound | Ally | Hire |
|------|-------|------|------|
| Gatherer | Strong early | Steady | Fine |
| Builder | Fast labor, slight quality− | Quality+ | Fine |
| Guard | Good; revolt risk if low Loyalty | Reliable | Fine while paid |
| Scout | Weak / locked until mid Loyalty | **Best** | OK |
| Crafter | Penalized quality | **Best** | Good if skilled hire |
| Beast-handler | Locked or heavily penalized | **Best** (synergy) | Mid |
| Quartermaster | Locked | High Loyalty Ally | Rare |
| Expedition lead | Mid combat only | **Best** for explore | Temporary |

Hard-job flag: certain assignments **Bound-only** (or Bound-preferred). Trust roles: **Ally-preferred / Ally-only**.

---

## 5. Acquisition pipelines

### 5.1 Force → Bound (permanent)

Down → escort to camp → bind structure/cost → break-in → Bound Follower.  
Identity badge: **Bound**. Stays Bound forever.

### 5.2 Earn → Ally (permanent)

Rescue or Recruit dialogue/quest → Ally Follower.  
Identity badge: **Ally**. Stays Ally forever.

### 5.3 Hire (contract)

Offer wages → Hire Follower until leave/fire.  
Can rehire later as a new contract (same person optional).

---

## 6. Slice scope

Prove:
1. One **Bound** end-to-end with a Force benefit readable (cheap labor or fear presence or hard job).  
2. One **Ally** end-to-end with an Earn benefit readable (quality, scout, or beast-care).  
3. **Hire** optional but recommended: pay → work → miss pay → leave.  
4. No path conversion UI exists.  
5. Zero Followers still clears critical path.  
6. Save/load persists identity, Loyalty, role, wage debt.

---

## 7. UI

- Big identity badge: **Bound** / **Ally** / **Hire** (never ambiguous)  
- Loyalty vs ceiling  
- Benefit tooltips per identity (“Fear presence”, “Beast-care bonus”, etc.)  
- Wage timer for Hire  
- Risk tells for Bound (morale color, murmur idles)

---

## 8. Anti-goals

- Soft converting Bound → Ally through friendship grinding  
- Force strictly better at everything  
- Earn strictly cosmetic “nice mode”  
- Followers required for landmarks  
- Humanoid breeding in v1  

---

## 9. Build order

1. Identities + badges (Bound/Ally/Hire)  
2. Force capture → bind  
3. Ally rescue or recruit  
4. Loyalty/Morale/ceilings  
5. Asymmetric passive benefits  
6. Roles (Gatherer, Builder, Guard + one Ally-favored)  
7. Bound escape; Hire leave  
8. Save/load + UI  

---

## 10. Starting numbers

| Parameter | Start |
|-----------|-------|
| Bound TrustCeiling | 65 |
| Ally TrustCeiling | 95 |
| Hire TrustCeiling | 80 |
| Hire pay period | per in-game day |
| Bound escape | event + rare pulse |
| Revolt | ≥3 Bound and avg Loyalty < 30 (slice may use 2) |

---

## 11. Acceptance tests

- [ ] Bound stays Bound after high Loyalty — no convert button  
- [ ] Ally stays Ally — no enslave-this-Ally flow in v2  
- [ ] Hire leaves when unpaid  
- [ ] At least one Bound-only (or Bound-best) benefit fires  
- [ ] At least one Ally-only (or Ally-best) benefit fires  
- [ ] Solo critical path without Followers  

---

## 12. Changelog

**v2:** Removed Force↔Earn conversion. Acquisition locks identity (Bound or Ally permanent). Hire remains upkeep-based and can leave. Added explicit **asymmetric benefits** for Bound and Ally so both moral directions are mechanically spicy. Clarified role output differences and anti-goals.

---

*Addendum v2 — locked identities, Hire with wages, benefits both ways, never gate the main path.*
