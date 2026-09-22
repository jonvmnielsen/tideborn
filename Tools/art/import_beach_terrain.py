# -*- coding: utf-8 -*-
"""Import sculpted beach/water FBX, replace flat planes, keep rock dress, verify shot."""
from __future__ import annotations
import pathlib, time, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_terrain_result.txt"
SHOT = ROOT / "Saved" / "Screenshots" / "WindowsEditor"
MAT = "/Game/Tideborn/Art/Materials"
MESH_DST = "/Game/Tideborn/Art/Meshes"
lines = []

def log(m):
    t = str(m); unreal.log("[Terrain] " + t); lines.append(t)

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
        try: comp.set_editor_property("override_materials", [mat] * 8)
        except Exception: pass
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break

def import_fbx(path, dest):
    task = unreal.AssetImportTask()
    task.filename = str(path)
    task.destination_path = dest
    task.automated = True
    task.save = True
    task.replace_existing = True
    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = False
    options.import_materials = False
    options.import_textures = False
    options.static_mesh_import_data.combine_meshes = True
    options.static_mesh_import_data.auto_generate_collision = True
    options.static_mesh_import_data.import_uniform_scale = 1.0
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.imported_object_paths) if task.imported_object_paths else []
    log("import %s -> %s" % (path, paths))
    return paths

try:
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e:
    log("load " + str(e))

# Import meshes
beach_paths = import_fbx(ROOT / "RawArt" / "CC0" / "Models" / "SM_TidebornBeach.fbx", MESH_DST)
water_paths = import_fbx(ROOT / "RawArt" / "CC0" / "Models" / "SM_TidebornWater.fbx", MESH_DST)

beach_mesh = None
water_mesh = None
for p in beach_paths:
    a = load(p)
    if isinstance(a, unreal.StaticMesh):
        beach_mesh = a; break
if not beach_mesh:
    beach_mesh = load(MESH_DST + "/SM_TidebornBeach")
for p in water_paths:
    a = load(p)
    if isinstance(a, unreal.StaticMesh):
        water_mesh = a; break
if not water_mesh:
    water_mesh = load(MESH_DST + "/SM_TidebornWater")

sand = load(MAT + "/M_Tideborn_Sand")
ground = load(MAT + "/M_Tideborn_Ground")
water_mat = load(MAT + "/M_Tideborn_WaterSimple")
rock = load(MAT + "/M_Tideborn_RockShore") or load(MAT + "/M_Tideborn_RockBoulder")
bark = load(MAT + "/M_Tideborn_Bark")
log("beach=%s water=%s sand=%s" % (bool(beach_mesh), bool(water_mesh), bool(sand)))

# Remove flat env planes (keep rocks/trunks)
for a in list(actors()):
    lab = label(a)
    if any(k in lab for k in ("TidebornEnv_Sand", "TidebornEnv_Ground", "TidebornEnv_Ocean", "TidebornEnv_Shallows", "TidebornEnv_Dune", "TidebornEnv_Beach", "TidebornEnv_WaterMesh")):
        try:
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
            log("x " + lab)
        except Exception:
            pass

ox, oy, oz = 1000.0, 1000.0, 100.0
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Place beach centered on cove origin; Blender mesh Y- toward ocean matches our -Y ocean
if beach_mesh:
    # Bake sand onto mesh asset
    try:
        existing = list(beach_mesh.get_editor_property("static_materials") or [])
        n = max(1, len(existing))
        slots = []
        for _ in range(n):
            s = unreal.StaticMaterial(); s.set_editor_property("material_interface", sand); slots.append(s)
        beach_mesh.set_editor_property("static_materials", slots)
        unreal.EditorAssetLibrary.save_asset(MESH_DST + "/SM_TidebornBeach")
    except Exception as e:
        log("bake beach " + str(e))
    b = sub.spawn_actor_from_object(beach_mesh, unreal.Vector(ox, oy - 200, oz - 40), unreal.Rotator(pitch=0, yaw=0, roll=0))
    if b:
        b.set_actor_label("TidebornEnv_Beach")
        apply(b, sand)
        log("placed beach")

if water_mesh:
    try:
        slots = [unreal.StaticMaterial()]
        slots[0].set_editor_property("material_interface", water_mat)
        water_mesh.set_editor_property("static_materials", slots)
        unreal.EditorAssetLibrary.save_asset(MESH_DST + "/SM_TidebornWater")
    except Exception as e:
        log("bake water " + str(e))
    w = sub.spawn_actor_from_object(water_mesh, unreal.Vector(ox, oy - 900, oz - 55), unreal.Rotator(pitch=0, yaw=0, roll=0))
    if w:
        w.set_actor_label("TidebornEnv_WaterMesh")
        apply(w, water_mat)
        log("placed water mesh")

# Re-seat PlayerStart on beach
for a in actors():
    lab = label(a); cn = cname(a)
    if "PlayerStart" in cn or lab == "PlayerStart":
        a.set_actor_location(unreal.Vector(ox + 80, oy + 80, oz + 120), False, True)
        a.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=-90.0, roll=0.0), False)
        log("playerstart")
    if "Boulder" in lab:
        apply(a, rock)
    if "Trunk" in lab:
        apply(a, bark)

for a in actors():
    if "DirectionalLight" in cname(a):
        try:
            a.set_editor_property("intensity", 3.4)
            a.set_actor_rotation(unreal.Rotator(pitch=-40.0, yaw=30.0, roll=0.0), False)
        except Exception:
            pass
    if "ExponentialHeightFog" in cname(a):
        try:
            a.set_editor_property("fog_density", 0.028)
        except Exception:
            pass

try:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception:
    try: unreal.EditorLevelLibrary.save_current_level()
    except Exception: pass
try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception:
    pass

# Screenshot
SHOT.mkdir(parents=True, exist_ok=True)
target = SHOT / "TidebornCoveVerify.png"
if target.exists():
    try: target.unlink()
    except Exception: pass
for cmd in ("ShowFlag.ModeWidgets 0", "ShowFlag.Selection 0", "ShowFlag.SelectionOutline 0", "ShowFlag.Bounds 0", "ShowFlag.Collision 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(ox + 80, oy + 100, oz + 180),
        unreal.Rotator(pitch=-6.0, yaw=-90.0, roll=0.0),
    )
except Exception:
    pass
try:
    unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, "TidebornCoveVerify")
except Exception as e:
    log("shot " + str(e))
for _ in range(40):
    time.sleep(0.4)
    if target.exists() and target.stat().st_size > 100000:
        log("shot ok %d" % target.stat().st_size); break

RESULT.write_text("\n".join(lines) + "\nDONE\n", encoding="utf-8")
log("DONE")
