# -*- coding: utf-8 -*-
"""Diagnose + bake mats onto ALL Tideborn meshes; clear checkerboard; reposition gameplay off sightline."""
from __future__ import annotations
import pathlib, time, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_clean_result.txt"
SHOT = ROOT / "Saved" / "Screenshots" / "WindowsEditor"
MAT = "/Game/Tideborn/Art/Materials"
lines = []

def log(m):
    t = str(m); unreal.log("[CoveClean] " + t); lines.append(t)

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

def mesh_info(a):
    info = []
    for cls in (unreal.StaticMeshComponent,):
        try:
            for comp in a.get_components_by_class(cls):
                sm = comp.get_editor_property("static_mesh")
                mats = []
                for i in range(4):
                    try:
                        m = comp.get_material(i)
                        mats.append(m.get_name() if m else "None")
                    except Exception:
                        break
                info.append("%s mats=%s" % (sm.get_name() if sm else "?", mats))
        except Exception:
            pass
    return info

def bake(path, mat):
    mesh = load(path)
    if not mesh or not mat: return False
    try:
        existing = []
        try: existing = list(mesh.get_editor_property("static_materials") or [])
        except Exception: pass
        n = max(1, len(existing))
        slots = []
        for i in range(n):
            s = unreal.StaticMaterial()
            s.set_editor_property("material_interface", mat)
            slots.append(s)
        mesh.set_editor_property("static_materials", slots)
        # Disable nanite if it blocks mat preview? keep nanite
        unreal.EditorAssetLibrary.save_asset(path)
        log("baked %s x%d" % (path, n))
        return True
    except Exception as e:
        log("bake fail %s %s" % (path, e)); return False

def apply(a, mat):
    if not mat: return 0
    n = 0
    for cls in (unreal.StaticMeshComponent,):
        try:
            for comp in a.get_components_by_class(cls):
                # force override materials array
                try:
                    overrides = []
                    for i in range(8):
                        overrides.append(mat)
                    comp.set_editor_property("override_materials", overrides)
                except Exception:
                    pass
                for i in range(8):
                    try:
                        comp.set_material(i, mat); n += 1
                    except Exception:
                        break
        except Exception:
            pass
    return n

def destroy(a, why):
    try:
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
        log("destroy %s (%s)" % (label(a), why))
    except Exception as e:
        log("destroy fail " + str(e))

def shot(name, loc, rot):
    SHOT.mkdir(parents=True, exist_ok=True)
    target = SHOT / (name + ".png")
    if target.exists():
        try: target.unlink()
        except Exception: pass
    for cmd in ("ShowFlag.ModeWidgets 0","ShowFlag.Selection 0","ShowFlag.SelectionOutline 0","ShowFlag.Bounds 0","ShowFlag.Collision 0","ShowFlag.LightRadius 0"):
        try: unreal.SystemLibrary.execute_console_command(None, cmd)
        except Exception: pass
    try:
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
    except Exception: pass
    try:
        unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, name)
    except Exception as e:
        log("shot err " + str(e))
    for _ in range(45):
        time.sleep(0.4)
        if target.exists() and target.stat().st_size > 150000:
            log("shot ok %s %d" % (name, target.stat().st_size)); return True
    log("shot miss " + name); return False

def main():
    try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
    except Exception as e: log("load "+str(e))

    # Inventory
    log("=== ACTOR DUMP ===")
    for a in actors():
        lab = label(a)
        if not lab and "Light" in cname(a): continue
        if any(k in cname(a) for k in ("SkyAtmosphere","SkyLight","Directional","Exponential","Volumetric","PlayerCamera","WorldSettings","AbstractNav","DefaultPhysics", "GameplayDebugger")):
            continue
        mi = mesh_info(a)
        if mi or lab.startswith("Tideborn") or "Gather" in lab or "Player" in cname(a) or "BP_" in lab:
            log("%s | %s | %s" % (lab, cname(a), mi))

    rock = load(MAT+"/M_Tideborn_RockBoulder")
    bark = load(MAT+"/M_Tideborn_Bark")
    sand = load(MAT+"/M_Tideborn_Sand")
    ground = load(MAT+"/M_Tideborn_Ground")
    water = load(MAT+"/M_Tideborn_WaterSimple")
    creature = load(MAT+"/M_Tideborn_CreatureSolid")
    gate = load(MAT+"/M_Tideborn_GateSolid")
    wood = load(MAT+"/M_Tideborn_Wood")

    # Bake every Tideborn mesh we have
    bake_map = [
        ("/Game/Tideborn/Art/Meshes/boulder_01_1k", rock),
        ("/Game/Tideborn/Art/Meshes/dead_tree_trunk_1k", bark),
        ("/Game/Tideborn/Meshes/SM_WoodStump", bark),
        ("/Game/Tideborn/Meshes/SM_StoneCluster", rock),
        ("/Game/Tideborn/Meshes/SM_BurrHound", creature),
        ("/Game/Tideborn/Meshes/SM_KelpBack", creature),
        ("/Game/Tideborn/Meshes/SM_ShoreGate", gate),
        ("/Game/Tideborn/Meshes/SM_Foundation", wood),
        ("/Game/Tideborn/Meshes/SM_PathPost", wood),
    ]
    for path, mat in bake_map:
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            bake(path, mat)

    ox, oy, oz = 1000.0, 1000.0, 100.0

    # Destroy any remaining engine primitive actors / checkerboard shapes that aren't TidebornEnv sand/ground/water
    for a in actors():
        lab = label(a); cn = cname(a)
        for comp in []:
            pass
        try:
            for comp in a.get_components_by_class(unreal.StaticMeshComponent):
                sm = comp.get_editor_property("static_mesh")
                if not sm: continue
                mn = sm.get_name().lower()
                # Engine basic shapes used as junk
                if mn in ("sphere", "cylinder", "cube", "cone", "1m_cube") and not lab.startswith("TidebornEnv_Sand") and not lab.startswith("TidebornEnv_Ground") and "Ocean" not in lab and "Shallows" not in lab:
                    if not lab.startswith("Tideborn"):
                        destroy(a, "engine primitive "+mn)
                        break
        except Exception:
            pass

    # Reposition: open sightline from spawn to ocean (-Y). Put creatures/gate OFF center.
    for a in actors():
        lab = label(a); cn = cname(a)
        if "PlayerStart" in cn or lab == "PlayerStart":
            a.set_actor_location(unreal.Vector(ox+100, oy+20, oz+95), False, True)
            a.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=-90.0, roll=0.0), False)
        if "Kelp" in lab:
            # left side of beach, not center
            a.set_actor_location(unreal.Vector(ox-520, oy-280, oz+40), False, True)
            apply(a, creature)
        if "Burr" in lab or "Hound" in lab:
            a.set_actor_location(unreal.Vector(ox+780, oy+200, oz+50), False, True)
            apply(a, creature)
        if "ShoreGate" in lab or ("Gate" in lab and "Tideborn" in lab):
            a.set_actor_location(unreal.Vector(ox+100, oy+1250, oz+90), False, True)
            apply(a, gate)
        if "Gather" in lab and "Stone" in lab:
            a.set_actor_location(unreal.Vector(ox+480, oy+160, oz+30), False, True)
            apply(a, rock)
        if "Gather" in lab and "Wood" in lab:
            apply(a, bark)
        if lab.startswith("TidebornEnv_Sand"): apply(a, sand)
        elif lab.startswith("TidebornEnv_Ground"): apply(a, ground)
        elif "Ocean" in lab or "Shallows" in lab: apply(a, water)
        elif "Trunk" in lab or "Boulder" in lab:
            apply(a, bark if "Trunk" in lab else rock)

    woods = [a for a in actors() if "Gather" in label(a) and "Wood" in label(a)]
    for i,a in enumerate(woods):
        a.set_actor_location(unreal.Vector(ox+420+i*130, oy+120, oz+30), False, True)
        apply(a, bark)

    # Soft light again
    for a in actors():
        if "DirectionalLight" in cname(a):
            try:
                a.set_editor_property("intensity", 4.0)
                a.set_actor_rotation(unreal.Rotator(pitch=-38.0, yaw=35.0, roll=0.0), False)
            except Exception: pass

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    except Exception:
        try: unreal.EditorLevelLibrary.save_current_level()
        except Exception: pass
    try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception: pass

    # Beauty shot: spawn looking to ocean — open sand, rocks on sides, water ahead
    shot("TidebornCoveVerify", unreal.Vector(ox+100, oy+50, oz+150), unreal.Rotator(pitch=-4.0, yaw=-90.0, roll=0.0))
    shot("TidebornCoveOverview", unreal.Vector(ox+100, oy+2200, oz+1000), unreal.Rotator(pitch=-38.0, yaw=-90.0, roll=0.0))

    RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
    log("DONE")

if __name__ == "__main__":
    main()
