# -*- coding: utf-8 -*-
"""v6 dump: TidebornEnv/WLB/WetSand/ShoreEdge + water/sand Y coverage + corridor blockers."""
from __future__ import annotations
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
OUT = ROOT / "Tools" / "art" / "cove_dump_v6.txt"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines = []
def log(m):
    t = str(m); unreal.log("[DumpV6] " + t); lines.append(t)
def label(a):
    try: return a.get_actor_label() or ""
    except Exception: return ""
try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load " + str(e))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = list(eas.get_all_level_actors())
log("=== TidebornEnv / WLB / WetSand / ShoreEdge ===")
water_y = []; sand_y = []; blockers = []
for a in actors:
    lab = label(a)
    keep = (lab.startswith("TidebornEnv_") or lab.startswith("TidebornEnv_WLB_")
            or lab.startswith("TidebornEnv_WetSand_") or "ShoreEdge" in lab
            or lab.startswith("TidebornEnv_WLB") or "WLB_" in lab)
    if not keep and not any(k in lab for k in ("SandBase","Ocean","Shallows","WetSand","ShoreEdge","WLB_","Boulder","SandRamp")):
        continue
    if not (lab.startswith("Tideborn") or "ShoreEdge" in lab):
        continue
    loc = a.get_actor_location(); sc = a.get_actor_scale3d()
    mats = []
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        try:
            mesh = comp.get_editor_property("static_mesh")
            mn = mesh.get_name() if mesh else "?"
        except Exception:
            mn = "?"
        for i in range(4):
            try:
                m = comp.get_material(i)
                if m: mats.append("%s[%d]=%s" % (mn, i, m.get_name()))
            except Exception:
                break
        break
    hy = 50.0 * sc.y; hx = 50.0 * sc.x
    y0, y1 = loc.y - hy, loc.y + hy
    x0, x1 = loc.x - hx, loc.x + hx
    line = "%s | loc=(%.0f,%.0f,%.1f) sc=(%.2f,%.2f,%.2f) | Y[%.0f..%.0f] X[%.0f..%.0f] | %s" % (
        lab, loc.x, loc.y, loc.z, sc.x, sc.y, sc.z, y0, y1, x0, x1, ";".join(mats) or "-")
    log(line)
    if "Ocean" in lab or "Shallows" in lab:
        water_y.append((lab, y0, y1, loc.z, sc.y))
    if lab == "TidebornEnv_SandBase":
        sand_y.append((lab, y0, y1, loc.z, sc.y))
    # Corridor blockers X in [850,1150] Y in [400,900]
    if 850 <= loc.x <= 1150 and 400 <= loc.y <= 900:
        if any(k in lab for k in ("WLB_", "Boulder", "ShoreEdge", "WetSand", "SandRamp", "Trunk")):
            blockers.append(line)
log("")
log("=== Water Y coverage ===")
for lab, y0, y1, z, sy in water_y:
    log("%s Z=%.1f scY=%.2f Y[%.0f..%.0f]" % (lab, z, sy, y0, y1))
log("=== SandBase Y coverage ===")
for lab, y0, y1, z, sy in sand_y:
    log("%s Z=%.1f scY=%.2f Y[%.0f..%.0f]" % (lab, z, sy, y0, y1))
log("=== Corridor blockers X[850,1150] Y[400,900] ===")
for b in blockers:
    log("BLOCK " + b)
log("blocker_count=%d" % len(blockers))
OUT.write_text("\n".join(lines) + "\nDONE\n", encoding="utf-8")
log("wrote %s (%d lines)" % (OUT, len(lines)))
