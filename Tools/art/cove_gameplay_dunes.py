# -*- coding: utf-8 -*-
"""Move gameplay off rock arms; try create simple Landscape for beach."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_landscape_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
lines = []

def log(m):
    t = str(m); unreal.log("[Land] " + t); lines.append(t)

def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())

def label(a):
    try: return a.get_actor_label() or ""
    except: return ""

def cname(a):
    try: return a.get_class().get_name() or ""
    except: return ""

def load(p):
    return unreal.EditorAssetLibrary.load_asset(p) if p and unreal.EditorAssetLibrary.does_asset_exist(p) else None

def apply(a, mat):
    if not mat: return
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        try: comp.set_editor_property("override_materials", [mat]*8)
        except Exception: pass
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break

try:
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e:
    log("load " + str(e))

ox, oy, oz = 1000.0, 1000.0, 100.0
rock = load(MAT + "/M_Tideborn_RockShore") or load(MAT + "/M_Tideborn_RockBoulder")
bark = load(MAT + "/M_Tideborn_Bark")
creature = load(MAT + "/M_Tideborn_CreatureSolid")
gate = load(MAT + "/M_Tideborn_GateSolid")

# Pull gameplay clearly outside rock corridors
for a in actors():
    lab = label(a); cn = cname(a)
    if "Kelp" in lab:
        a.set_actor_location(unreal.Vector(ox - 750, oy + 200, oz + 40), False, True)
        apply(a, creature); log("kelp out")
    if "Burr" in lab or "Hound" in lab:
        a.set_actor_location(unreal.Vector(ox + 900, oy + 250, oz + 50), False, True)
        apply(a, creature); log("hound out")
    if "ShoreGate" in lab or ("Gate" in lab and "Tideborn" in lab):
        a.set_actor_location(unreal.Vector(ox + 100, oy + 1600, oz + 90), False, True)
        apply(a, gate); log("gate out")
    if "Gather" in lab and "Stone" in lab:
        a.set_actor_location(unreal.Vector(ox + 280, oy + 200, oz + 30), False, True)
        apply(a, rock)
    if "Gather" in lab and "Wood" in lab:
        apply(a, bark)

woods = [a for a in actors() if "Gather" in label(a) and "Wood" in label(a)]
for i, a in enumerate(woods):
    a.set_actor_location(unreal.Vector(ox + 200 + i * 140, oy + 180, oz + 30), False, True)

# Try Landscape — several APIs across UE versions
land_ok = False
try:
    # Hide flat sand/ground planes under landscape later; first spawn landscape
    # UE5.4: EditorLevelLibrary.spawn_actor_from_class(Landscape)
    land_cls = unreal.Landscape
    # New landscape via LandscapeEditorObject is editor-mode only.
    # Fallback: use LandscapeProxy if available
    log("Landscape class=%s" % land_cls)
except Exception as e:
    log("Landscape cls " + str(e))

# Attempt import-style create through unreal.LandscapeImportHelper if present
try:
    helper = unreal.LandscapeImportHelper
    log("has LandscapeImportHelper")
except Exception:
    log("no LandscapeImportHelper")

# Create heightmap-like undulation using scaled rock "dune" proxies? Skip — instead
# raise sand plane edges by adding slightly tilted duplicate sand strips as fake dunes.
sand = load(MAT + "/M_Tideborn_Sand")
plane_mesh = load("/Engine/BasicShapes/Plane")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
# Fake dune berms along rock lines (slightly raised sand shelves)
for i, (x, y, yaw, sx, sy) in enumerate((
    (ox - 350, oy - 100, 8.0, 25, 55),
    (ox + 450, oy - 100, -8.0, 25, 55),
    (ox + 100, oy - 600, 0.0, 70, 20),
)):
    a = sub.spawn_actor_from_object(plane_mesh, unreal.Vector(x, y, oz + 8), unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
    if a:
        a.set_actor_scale3d(unreal.Vector(sx, sy, 1.0))
        a.set_actor_label("TidebornEnv_Dune_%d" % i)
        # slight pitch via rotator - pitch tilts plane
        a.set_actor_rotation(unreal.Rotator(pitch=3.0 if i < 2 else 2.0, yaw=yaw, roll=0.0), False)
        apply(a, sand)
        log("dune %d" % i)

try:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception:
    pass

RESULT.write_text("\n".join(lines) + "\nDONE\n", encoding="utf-8")
log("DONE")
