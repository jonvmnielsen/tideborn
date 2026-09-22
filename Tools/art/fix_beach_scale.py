# -*- coding: utf-8 -*-
"""Diagnose beach bounds; scale/place correctly; ensure continuous ground under cove."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_terrain_fix_result.txt"
MAT = "/Game/Tideborn/Art/Materials"
MESH = "/Game/Tideborn/Art/Meshes"
lines = []

def log(m):
    t = str(m); unreal.log("[TerrainFix] " + t); lines.append(t)

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
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break

def bounds_info(mesh):
    try:
        box = mesh.get_bounding_box()
        mn, mx = box.min, box.max
        return "min=(%.1f,%.1f,%.1f) max=(%.1f,%.1f,%.1f) size=(%.1f,%.1f,%.1f)" % (
            mn.x, mn.y, mn.z, mx.x, mx.y, mx.z, mx.x-mn.x, mx.y-mn.y, mx.z-mn.z)
    except Exception as e:
        return str(e)

try:
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e:
    log(str(e))

beach = load(MESH + "/SM_TidebornBeach")
water = load(MESH + "/SM_TidebornWater")
log("beach bounds " + bounds_info(beach) if beach else "no beach")
log("water bounds " + bounds_info(water) if water else "no water")

sand = load(MAT + "/M_Tideborn_Sand")
water_mat = load(MAT + "/M_Tideborn_WaterSimple")
ground = load(MAT + "/M_Tideborn_Ground")
ox, oy, oz = 1000.0, 1000.0, 100.0

# Remove current beach/water placements + leftover strips
for a in list(actors()):
    lab = label(a)
    if lab in ("TidebornEnv_Beach", "TidebornEnv_WaterMesh") or lab.startswith("TidebornEnv_Sand") or lab.startswith("TidebornEnv_Ground") or "Ocean" in lab or "Shallows" in lab:
        try:
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
            log("x " + lab)
        except Exception:
            pass

sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
plane = load("/Engine/BasicShapes/Plane")

# SAFETY: large sand plane always under feet so never void
def spawn_plane(loc, sx, sy, mat, lab):
    a = sub.spawn_actor_from_object(plane, loc, unreal.Rotator(0, 0, 0))
    if a:
        a.set_actor_scale3d(unreal.Vector(sx, sy, 1))
        a.set_actor_label(lab)
        apply(a, mat)
        log("plane " + lab)
    return a

spawn_plane(unreal.Vector(ox, oy, oz - 2), 120, 120, sand, "TidebornEnv_SandBase")
spawn_plane(unreal.Vector(ox, oy + 1400, oz - 3), 120, 100, ground, "TidebornEnv_Ground")
spawn_plane(unreal.Vector(ox, oy - 1100, oz - 20), 130, 70, water_mat, "TidebornEnv_Ocean")

# Place sculpted beach ON TOP of sand base, scaled to cover cove (~8000uu if mesh is ~1 unit, or match bounds)
if beach:
    # Target coverage ~9000 x 11000 uu
    try:
        box = beach.get_bounding_box()
        sx0 = max(abs(box.max.x - box.min.x), 1.0)
        sy0 = max(abs(box.max.y - box.min.y), 1.0)
        sz0 = max(abs(box.max.z - box.min.z), 1.0)
        scale_x = 9000.0 / sx0
        scale_y = 11000.0 / sy0
        scale_z = max(1.0, 350.0 / sz0)  # heighten relief
        sc = unreal.Vector(scale_x, scale_y, scale_z)
        log("beach scale %s from size %.1f %.1f %.1f" % (sc, sx0, sy0, sz0))
    except Exception as e:
        sc = unreal.Vector(1, 1, 1); log("scale fail " + str(e))
    # Bake mat
    try:
        s = unreal.StaticMaterial(); s.set_editor_property("material_interface", sand)
        beach.set_editor_property("static_materials", [s])
        unreal.EditorAssetLibrary.save_asset(MESH + "/SM_TidebornBeach")
    except Exception as e:
        log(str(e))
    b = sub.spawn_actor_from_object(beach, unreal.Vector(ox, oy - 100, oz - 5), unreal.Rotator(0, 0, 0))
    if b:
        b.set_actor_scale3d(sc)
        b.set_actor_label("TidebornEnv_Beach")
        apply(b, sand)
        log("beach placed")

if water:
    try:
        box = water.get_bounding_box()
        sx0 = max(abs(box.max.x - box.min.x), 1.0)
        sy0 = max(abs(box.max.y - box.min.y), 1.0)
        scw = unreal.Vector(12000.0 / sx0, 8000.0 / sy0, 1.0)
        log("water scale %s" % scw)
    except Exception:
        scw = unreal.Vector(1, 1, 1)
    try:
        s = unreal.StaticMaterial(); s.set_editor_property("material_interface", water_mat)
        water.set_editor_property("static_materials", [s])
        unreal.EditorAssetLibrary.save_asset(MESH + "/SM_TidebornWater")
    except Exception:
        pass
    w = sub.spawn_actor_from_object(water, unreal.Vector(ox, oy - 1200, oz - 35), unreal.Rotator(0, 0, 0))
    if w:
        w.set_actor_scale3d(scw)
        w.set_actor_label("TidebornEnv_WaterMesh")
        apply(w, water_mat)
        log("water placed")

# PlayerStart safe on sand
for a in actors():
    if "PlayerStart" in cname(a) or label(a) == "PlayerStart":
        a.set_actor_location(unreal.Vector(ox + 80, oy + 120, oz + 110), False, True)
        a.set_actor_rotation(unreal.Rotator(pitch=0, yaw=-90, roll=0), False)

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
