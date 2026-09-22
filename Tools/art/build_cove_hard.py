# -*- coding: utf-8 -*-
"""Hard cove pass: bake mats onto mesh assets, sparse horseshoe layout, strip grey props."""
from __future__ import annotations
import math, pathlib, random, time, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_hard_result.txt"
SHOT = ROOT / "Saved" / "Screenshots" / "WindowsEditor"
MAT = "/Game/Tideborn/Art/Materials"
MESH = "/Game/Tideborn/Art/Meshes"
OLD = "/Game/Tideborn/Meshes"
lines = []
C = {"destroyed": 0, "planes": 0, "props": 0, "moved": 0, "baked": 0}

def log(m):
    t = str(m); unreal.log("[CoveHard] " + t); lines.append(t)

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

def destroy(a, why):
    try:
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
        C["destroyed"] += 1
        log("x %s (%s)" % (label(a), why))
    except Exception as e:
        log("xfail " + str(e))

def clear():
    for a in actors():
        lab = label(a); cn = cname(a); low = lab.lower()
        if lab.startswith("TidebornEnv_") or lab.startswith("TidebornShore_"):
            destroy(a, "env"); continue
        if lab.startswith("SM_") or "Floor" in lab:
            destroy(a, "grey"); continue
        if "TextRender" in cn:
            destroy(a, "text"); continue
        # Strip path posts / beacons from cove — they read as grey pillars
        if any(k in lab for k in ("PathPost", "Beacon", "Landmark", "Tideborn_Beacon")):
            destroy(a, "grey pillar"); continue
        if cn == "StaticMeshActor" and not lab.startswith("Tideborn"):
            mesh_name = ""
            try:
                for comp in a.get_components_by_class(unreal.StaticMeshComponent):
                    sm = comp.get_editor_property("static_mesh")
                    if sm: mesh_name = sm.get_name(); break
            except Exception: pass
            mn = (mesh_name or "").lower()
            if any(x in mn for x in ("cube","cylinder","ramp","plane","floor","shape","1m","sphere","cone")):
                destroy(a, "tpl")

def bake_mesh_mat(mesh_path, mat):
    mesh = load(mesh_path)
    if not mesh or not mat: return False
    try:
        slot = unreal.StaticMaterial()
        slot.set_editor_property("material_interface", mat)
        try:
            slot.set_editor_property("material_slot_name", "Default")
        except Exception: pass
        try:
            slot.set_editor_property("imported_material_slot_name", "Default")
        except Exception: pass
        # Preserve slot count
        try:
            existing = mesh.get_editor_property("static_materials") or []
            n = max(1, len(existing))
        except Exception:
            n = 1
        slots = []
        for i in range(n):
            s = unreal.StaticMaterial()
            s.set_editor_property("material_interface", mat)
            slots.append(s)
        mesh.set_editor_property("static_materials", slots)
        unreal.EditorAssetLibrary.save_asset(mesh_path)
        C["baked"] += 1
        log("baked %s slots=%d" % (mesh_path, n))
        return True
    except Exception as e:
        log("bake fail %s: %s" % (mesh_path, e))
        return False

def apply_actor(a, mat):
    n = 0
    if not mat: return 0
    for cls_name in ("StaticMeshComponent", "SkeletalMeshComponent", "MeshComponent"):
        try:
            cls = getattr(unreal, cls_name)
        except Exception:
            continue
        try:
            for comp in a.get_components_by_class(cls):
                for i in range(12):
                    try:
                        comp.set_material(i, mat); n += 1
                    except Exception:
                        break
                try:
                    comp.set_editor_property("overlay_material", None)
                except Exception: pass
        except Exception:
            pass
    return n

def find_mesh(keys):
    for d in (MESH, OLD):
        if not unreal.EditorAssetLibrary.does_directory_exist(d): continue
        for ap in unreal.EditorAssetLibrary.list_assets(d, recursive=True):
            low = ap.lower()
            if "coast_land" in low or "stonecluster" in low: continue
            if any(k.lower() in low for k in keys):
                asset = load(ap)
                if isinstance(asset, unreal.StaticMesh):
                    return asset, ap.split(".")[0] if "." in ap else ap
    return None, None

def bounds_r(mesh):
    try:
        box = mesh.get_bounding_box(); e = box.max - box.min
        return max(abs(e.x), abs(e.y), abs(e.z))
    except Exception:
        return 100.0

def spawn(mesh, loc, yaw, scale, lab, mat):
    a = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_object(
        mesh, loc, unreal.Rotator(pitch=0.0, yaw=float(yaw), roll=0.0)
    )
    if not a: return None
    a.set_actor_scale3d(scale); a.set_actor_label(lab)
    apply_actor(a, mat)
    return a

def plane(loc, sx, sy, mat, lab):
    p = load("/Engine/BasicShapes/Plane")
    return spawn(p, loc, 0.0, unreal.Vector(sx, sy, 1.0), lab, mat)

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
    except Exception as e:
        log("cam " + str(e))
    try:
        unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, name)
    except Exception as e:
        log("shotapi " + str(e))
    for _ in range(40):
        time.sleep(0.4)
        if target.exists() and target.stat().st_size > 100000:
            log("shot ok %s %d" % (name, target.stat().st_size)); return True
        try: unreal.SystemLibrary.execute_console_command(None, "r.ScreenPercentage 100")
        except Exception: pass
    log("shot MISS %s" % name); return False

def main():
    try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
    except Exception as e: log("load "+str(e))

    ox, oy, oz = 1000.0, 1000.0, 100.0
    clear()

    sand = load(MAT + "/M_Tideborn_Sand")
    ground = load(MAT + "/M_Tideborn_Ground")
    rock = load(MAT + "/M_Tideborn_RockBoulder")
    bark = load(MAT + "/M_Tideborn_Bark")
    water = load(MAT + "/M_Tideborn_WaterSimple")
    creature = load(MAT + "/M_Tideborn_CreatureSolid")
    gate = load(MAT + "/M_Tideborn_GateSolid")
    log("mats sand=%s rock=%s bark=%s water=%s" % (bool(sand), bool(rock), bool(bark), bool(water)))

    boulder, bp = find_mesh(["boulder_01"])
    stump, sp = find_mesh(["dead_tree_trunk"])
    log("boulder=%s stump=%s" % (bp, sp))
    if bp and rock: bake_mesh_mat(bp, rock)
    if sp and bark: bake_mesh_mat(sp, bark)
    # reload after bake
    boulder = load(bp) if bp else None
    stump = load(sp) if sp else None

    # Soft light — stop blowing rocks white
    for a in actors():
        if "DirectionalLight" in cname(a):
            try:
                a.set_editor_property("intensity", 4.5)
                a.set_editor_property("light_color", unreal.LinearColor(1.0, 0.88, 0.7, 1.0))
                a.set_actor_rotation(unreal.Rotator(pitch=-35.0, yaw=40.0, roll=0.0), False)
            except Exception: pass
        if "SkyLight" in cname(a):
            try:
                a.set_editor_property("intensity", 1.0)
                a.set_editor_property("real_time_capture", True)
            except Exception: pass

    # Layers: inland ground, beach, shallows, ocean
    if plane(unreal.Vector(ox+300, oy+1400, oz-4), 120, 120, ground, "TidebornEnv_Ground"): C["planes"] += 1
    for i,(dx,dy,sx,sy) in enumerate(((50,-50,80,45),(900,-180,55,38),(-700,-140,55,36),(200,400,50,45))):
        if plane(unreal.Vector(ox+dx, oy+dy, oz-1), sx, sy, sand, "TidebornEnv_Sand_%d"%i): C["planes"] += 1
    if plane(unreal.Vector(ox+150, oy-1300, oz-25), 100, 45, water, "TidebornEnv_Shallows"): C["planes"] += 1
    if plane(unreal.Vector(ox+150, oy-2800, oz-55), 170, 120, water, "TidebornEnv_Ocean"): C["planes"] += 1

    rng = random.Random(42)
    # Horseshoe: open center at spawn facing -Y ocean; rocks on left/right/back only
    placements = []
    # left arm
    for i in range(5):
        placements.append((ox - 550 + i*40, oy - 200 + i*180, oz, "Boulder", 1.0))
    # right arm
    for i in range(5):
        placements.append((ox + 700 + i*30, oy - 150 + i*170, oz, "Boulder", 1.0))
    # back ridge (inland +Y)
    for i in range(4):
        placements.append((ox - 200 + i*280, oy + 700, oz, "Boulder", 1.15))
    # driftwood on beach
    for i in range(4):
        placements.append((ox - 100 + i*220, oy - 350 + (i%2)*80, oz, "Trunk", 0.9))

    for i,(x,y,z,kind,scmul) in enumerate(placements):
        mesh = boulder if kind == "Boulder" else stump
        mat = rock if kind == "Boulder" else bark
        if not mesh: continue
        r = bounds_r(mesh)
        sc = max(0.4, min(350.0 / max(r, 1.0), 2.2)) * scmul * rng.uniform(0.85, 1.1)
        yaw = rng.uniform(0, 360)
        if spawn(mesh, unreal.Vector(x+rng.uniform(-30,30), y+rng.uniform(-30,30), z), yaw,
                 unreal.Vector(sc, sc, sc*rng.uniform(0.9,1.05)),
                 "TidebornEnv_%s_%02d" % (kind, i), mat):
            C["props"] += 1

    # Gameplay — open sand in middle of horseshoe
    for a in actors():
        lab = label(a); cn = cname(a)
        if "PlayerStart" in cn or lab == "PlayerStart":
            a.set_actor_location(unreal.Vector(ox+120, oy+40, oz+95), False, True)
            a.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=-90.0, roll=0.0), False)
            C["moved"] += 1
        if "Gather" in lab and "Stone" in lab:
            a.set_actor_location(unreal.Vector(ox+420, oy+280, oz+30), False, True)
            apply_actor(a, rock); C["moved"] += 1
        if "Kelp" in lab:
            a.set_actor_location(unreal.Vector(ox-80, oy-420, oz+35), False, True)
            apply_actor(a, creature); C["moved"] += 1
        if "Burr" in lab or "Hound" in lab:
            a.set_actor_location(unreal.Vector(ox+780, oy+620, oz+50), False, True)
            apply_actor(a, creature); C["moved"] += 1
        if "ShoreGate" in lab or ("Gate" in lab and "Tideborn" in lab):
            a.set_actor_location(unreal.Vector(ox+200, oy+1100, oz+80), False, True)
            a.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0), False)
            apply_actor(a, gate); C["moved"] += 1
    for i,a in enumerate([a for a in actors() if "Gather" in label(a) and "Wood" in label(a)]):
        a.set_actor_location(unreal.Vector(ox+500+i*140, oy+200, oz+30), False, True)
        apply_actor(a, bark); C["moved"] += 1

    # Re-apply planes
    for a in actors():
        lab = label(a)
        if lab.startswith("TidebornEnv_Sand"): apply_actor(a, sand)
        elif lab.startswith("TidebornEnv_Ground"): apply_actor(a, ground)
        elif "Ocean" in lab or "Shallows" in lab: apply_actor(a, water)
        elif "Trunk" in lab: apply_actor(a, bark)
        elif "Boulder" in lab: apply_actor(a, rock)

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    except Exception:
        try: unreal.EditorLevelLibrary.save_current_level()
        except Exception: pass
    try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception: pass

    # One solid verify shot from spawn looking at ocean through open horseshoe
    shot(
        "TidebornCoveVerify",
        unreal.Vector(ox+120, oy+80, oz+160),
        unreal.Rotator(pitch=-5.0, yaw=-90.0, roll=0.0),
    )
    shot(
        "TidebornCoveOverview",
        unreal.Vector(ox+150, oy+2000, oz+1100),
        unreal.Rotator(pitch=-40.0, yaw=-90.0, roll=0.0),
    )

    lines.append("---")
    for k,v in C.items(): lines.append("%s=%s"%(k,v))
    lines.append("DONE")
    RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
    log("DONE")

if __name__ == "__main__":
    main()
