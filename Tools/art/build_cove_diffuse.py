# -*- coding: utf-8 -*-
"""Fix mats to diffuse+rough only (reliable compile), rebuild layout, fresh shots."""
from __future__ import annotations
import math, pathlib, random, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "living_cove_result.txt"
SHOT_DIR = ROOT / "Saved" / "Screenshots" / "WindowsEditor"
TEX = "/Game/Tideborn/Art/Textures"
MAT = "/Game/Tideborn/Art/Materials"
MESH = "/Game/Tideborn/Art/Meshes"
OLD = "/Game/Tideborn/Meshes"
lines = []
counts = {"destroyed": 0, "planes": 0, "props": 0, "moved": 0, "mats": 0, "mat_apply": 0}

def log(m):
    t = str(m); unreal.log("[Cove3] " + t); lines.append(t)

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
        counts["destroyed"] += 1
        log("destroy %s (%s)" % (label(a), why))
    except Exception as e:
        log("destroy fail " + str(e))

def clear_env():
    for a in actors():
        lab = label(a); cn = cname(a)
        if lab.startswith("TidebornEnv_") or lab.startswith("TidebornShore_"):
            destroy(a, "env"); continue
        if lab.startswith("SM_") or "Floor" in lab:
            destroy(a, "grey"); continue
        if "TextRender" in cn:
            destroy(a, "text"); continue
        if cn == "StaticMeshActor" and not lab.startswith("Tideborn"):
            mesh_name = ""
            try:
                for comp in a.get_components_by_class(unreal.StaticMeshComponent):
                    sm = comp.get_editor_property("static_mesh")
                    if sm: mesh_name = sm.get_name(); break
            except Exception:
                pass
            mn = (mesh_name or "").lower()
            if any(x in mn for x in ("cube","cylinder","ramp","plane","floor","shape","1m")):
                destroy(a, "tpl " + mesh_name)

def find_tex(folder, keys):
    base = TEX + "/" + folder
    if not unreal.EditorAssetLibrary.does_directory_exist(base):
        return None
    for ap in unreal.EditorAssetLibrary.list_assets(base, recursive=False):
        name = ap.split(".")[-1].lower()
        for k in keys:
            if k.lower() in name:
                return ap
    return None

def make_diff(name, folder, tile=4.0, fallback_rgb=(0.5, 0.4, 0.3), water=False):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not mat:
        return None
    mel = unreal.MaterialEditingLibrary
    if water:
        try:
            mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
            mat.set_editor_property("two_sided", True)
        except Exception:
            pass
        col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
        col.set_editor_property("constant", unreal.LinearColor(0.04, 0.2, 0.36, 1.0))
        mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
        op = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 100)
        op.set_editor_property("r", 0.5)
        mel.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
        rg = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 180)
        rg.set_editor_property("r", 0.04)
        mel.connect_material_property(rg, "", unreal.MaterialProperty.MP_ROUGHNESS)
        mel.recompile_material(mat)
        unreal.EditorAssetLibrary.save_asset(path)
        counts["mats"] += 1
        log("water " + name)
        return mat

    bc = load(find_tex(folder, ["Diffuse", "Color", "albedo", "BaseColor"]))
    rough = load(find_tex(folder, ["Rough", "roughness"]))

    uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -700, 0)
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -550, 0)
    sc = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -700, 60)
    sc.set_editor_property("r", float(tile))
    mel.connect_material_expressions(uv, "", mul, "A")
    mel.connect_material_expressions(sc, "", mul, "B")

    if bc:
        # Force color sampler
        try:
            bc.set_editor_property("srgb", True)
            unreal.EditorAssetLibrary.save_asset(bc.get_path_name())
        except Exception:
            pass
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, -80)
        ts.set_editor_property("texture", bc)
        mel.connect_material_expressions(mul, "", ts, "UVs")
        mel.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
        log("%s +diffuse" % name)
    else:
        col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, -80)
        col.set_editor_property("constant", unreal.LinearColor(fallback_rgb[0], fallback_rgb[1], fallback_rgb[2], 1.0))
        mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
        log("%s +fallback color" % name)

    if rough:
        try:
            rough.set_editor_property("srgb", False)
            unreal.EditorAssetLibrary.save_asset(rough.get_path_name())
        except Exception:
            pass
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, 120)
        ts.set_editor_property("texture", rough)
        try:
            ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        except Exception:
            pass
        mel.connect_material_expressions(mul, "", ts, "UVs")
        mel.connect_material_property(ts, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    else:
        rg = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 120)
        rg.set_editor_property("r", 0.85)
        mel.connect_material_property(rg, "", unreal.MaterialProperty.MP_ROUGHNESS)

    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    counts["mats"] += 1
    return mat

def make_solid(name, rgb):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew()
    )
    mel = unreal.MaterialEditingLibrary
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
    col.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rg = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 100)
    rg.set_editor_property("r", 0.7)
    mel.connect_material_property(rg, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    counts["mats"] += 1
    return mat

def apply_mat(actor, mat):
    n = 0
    if not mat: return 0
    for cls in (unreal.StaticMeshComponent,):
        try:
            for comp in actor.get_components_by_class(cls):
                for i in range(8):
                    try:
                        comp.set_material(i, mat); n += 1
                    except Exception:
                        break
        except Exception:
            pass
    return n

def find_mesh(keys):
    for d in (MESH, OLD):
        if not unreal.EditorAssetLibrary.does_directory_exist(d): continue
        for ap in unreal.EditorAssetLibrary.list_assets(d, recursive=True):
            low = ap.lower()
            if "coast_land" in low: continue
            if any(k.lower() in low for k in keys):
                asset = load(ap)
                if isinstance(asset, unreal.StaticMesh):
                    return asset, ap
    return None, None

def bounds_r(mesh):
    try:
        box = mesh.get_bounding_box(); ext = box.max - box.min
        return max(abs(ext.x), abs(ext.y), abs(ext.z))
    except Exception:
        return 100.0

def spawn_sm(mesh, loc, yaw, scale, lab, mat=None):
    a = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_object(
        mesh, loc, unreal.Rotator(pitch=0.0, yaw=float(yaw), roll=0.0)
    )
    if not a: return None
    a.set_actor_scale3d(scale); a.set_actor_label(lab)
    if mat: apply_mat(a, mat)
    return a

def spawn_plane(loc, sx, sy, mat, lab):
    plane = load("/Engine/BasicShapes/Plane")
    return spawn_sm(plane, loc, 0.0, unreal.Vector(sx, sy, 1.0), lab, mat)

def main():
    try:
        unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
    except Exception as e:
        log("load " + str(e))

    # Delete stale screenshots so new ones are unambiguous
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    for p in SHOT_DIR.glob("TidebornCove*.png"):
        try: p.unlink(); log("rm shot " + p.name)
        except Exception as e: log("rm fail " + str(e))

    ox, oy, oz = 1000.0, 1000.0, 100.0
    clear_env()

    sand = make_diff("M_Tideborn_Sand", "Sand", tile=14.0, fallback_rgb=(0.72, 0.58, 0.35))
    ground = make_diff("M_Tideborn_Ground", "Ground", tile=10.0, fallback_rgb=(0.25, 0.32, 0.16))
    rock = make_diff("M_Tideborn_RockBoulder", "RockBoulder", tile=2.5, fallback_rgb=(0.4, 0.38, 0.35))
    bark = make_diff("M_Tideborn_Bark", "Bark", tile=2.0, fallback_rgb=(0.3, 0.17, 0.08))
    wood = make_diff("M_Tideborn_Wood", "Wood", tile=2.0, fallback_rgb=(0.35, 0.22, 0.1))
    water = make_diff("M_Tideborn_WaterSimple", "Sand", water=True)
    creature = make_solid("M_Tideborn_CreatureSolid", (0.2, 0.4, 0.26))
    gate = make_solid("M_Tideborn_GateSolid", (0.42, 0.32, 0.18))

    # Ground + beach + ocean
    if spawn_plane(unreal.Vector(ox+400, oy+1100, oz-3), 110, 110, ground, "TidebornEnv_Ground"):
        counts["planes"] += 1
    for i,(dx,dy,sx,sy) in enumerate(((0,-80,75,42),(850,-200,55,36),(-650,-160,50,34),(250,300,48,42),(450,-650,65,28))):
        if spawn_plane(unreal.Vector(ox+dx, oy+dy, oz-1), sx, sy, sand, "TidebornEnv_Sand_%d"%i):
            counts["planes"] += 1
    if spawn_plane(unreal.Vector(ox+200, oy-1200, oz-22), 95, 40, water, "TidebornEnv_Shallows"):
        counts["planes"] += 1
    if spawn_plane(unreal.Vector(ox+200, oy-2500, oz-48), 160, 110, water, "TidebornEnv_Ocean"):
        counts["planes"] += 1

    boulder,_ = find_mesh(["boulder_01"])
    stump,_ = find_mesh(["dead_tree_trunk"])
    stone,_ = find_mesh(["SM_StoneCluster","StoneCluster"])
    rng = random.Random(33)
    usable = []
    for mesh, mat, name in ((boulder, rock, "Boulder"), (stump, bark, "Trunk"), (stone, rock, "Stone")):
        if mesh:
            r = bounds_r(mesh)
            if r < 2500:
                usable.append((mesh, mat, name, r)); log("%s r=%.1f"%(name,r))

    spots = []
    for i in range(18):
        t = i/17.0
        spots.append((ox-550+t*2100+rng.uniform(-70,70), oy-580+math.sin(t*math.pi)*160+rng.uniform(-50,50), oz))
    for i in range(12):
        t = i/11.0
        spots.append((ox+200+t*1200+rng.uniform(-90,90), oy+200+t*1000+rng.uniform(-70,70), oz))

    for i,(x,y,z) in enumerate(spots):
        mesh, mat, name, radius = usable[i % len(usable)]
        sc = max(0.3, min(rng.uniform(240,500)/max(radius,1.0), 2.5))
        if spawn_sm(mesh, unreal.Vector(x,y,z), rng.uniform(0,360), unreal.Vector(sc,sc,sc), "TidebornEnv_%s_%02d"%(name,i), mat):
            counts["props"] += 1

    # lights
    for a in actors():
        cn = cname(a)
        if "DirectionalLight" in cn:
            try:
                a.set_editor_property("intensity", 6.5)
                a.set_editor_property("light_color", unreal.LinearColor(1.0, 0.86, 0.65, 1.0))
                a.set_actor_rotation(unreal.Rotator(pitch=-30.0, yaw=45.0, roll=0.0), False)
            except Exception: pass
        if "SkyLight" in cn:
            try:
                a.set_editor_property("intensity", 1.25)
                a.set_editor_property("real_time_capture", True)
            except Exception: pass

    # gameplay
    for a in actors():
        lab = label(a); cn = cname(a)
        if "PlayerStart" in cn or lab == "PlayerStart":
            a.set_actor_location(unreal.Vector(ox+160, oy+60, oz+95), False, True)
            a.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=-90.0, roll=0.0), False)
            counts["moved"] += 1
        if "Gather" in lab and "Stone" in lab:
            a.set_actor_location(unreal.Vector(ox+400, oy+240, oz+35), False, True)
            apply_mat(a, rock); counts["moved"] += 1
        if "Kelp" in lab:
            a.set_actor_location(unreal.Vector(ox-140, oy-400, oz+40), False, True)
            apply_mat(a, creature); counts["moved"] += 1
        if "Burr" in lab or "Hound" in lab:
            a.set_actor_location(unreal.Vector(ox+850, oy+540, oz+55), False, True)
            apply_mat(a, creature); counts["moved"] += 1
        if "ShoreGate" in lab or ("Gate" in lab and "Tideborn" in lab):
            a.set_actor_location(unreal.Vector(ox+1280, oy+1080, oz+90), False, True)
            apply_mat(a, gate); counts["moved"] += 1
    for i,a in enumerate([a for a in actors() if "Gather" in label(a) and "Wood" in label(a)]):
        a.set_actor_location(unreal.Vector(ox+540+i*150, oy+160, oz+35), False, True)
        apply_mat(a, bark); counts["moved"] += 1
    for i,a in enumerate([a for a in actors() if "Beacon" in label(a) or "Landmark" in label(a)][:4]):
        t=(i+1)/5.0
        a.set_actor_location(unreal.Vector(ox+220+t*1000, oy+80+t*980, oz+40), False, True)
        apply_mat(a, wood); counts["moved"] += 1

    # re-apply env
    for a in actors():
        lab = label(a)
        if lab.startswith("TidebornEnv_Sand"): counts["mat_apply"] += apply_mat(a, sand)
        elif lab.startswith("TidebornEnv_Ground"): counts["mat_apply"] += apply_mat(a, ground)
        elif "Ocean" in lab or "Shallows" in lab: counts["mat_apply"] += apply_mat(a, water)
        elif "Trunk" in lab: counts["mat_apply"] += apply_mat(a, bark)
        elif lab.startswith("TidebornEnv_"): counts["mat_apply"] += apply_mat(a, rock)

    for cmd in ("ShowFlag.ModeWidgets 0","ShowFlag.Selection 0","ShowFlag.SelectionOutline 0","ShowFlag.Bounds 0","ShowFlag.Collision 0","ShowFlag.LightRadius 0"):
        try: unreal.SystemLibrary.execute_console_command(None, cmd)
        except Exception: pass

    shots = (
        ("TidebornCoveVerify", unreal.Vector(ox+160, oy+20, oz+165), unreal.Rotator(pitch=-4.0, yaw=-90.0, roll=0.0)),
        ("TidebornCoveOverview", unreal.Vector(ox+250, oy+1700, oz+900), unreal.Rotator(pitch=-30.0, yaw=-90.0, roll=0.0)),
        ("TidebornCoveSide", unreal.Vector(ox-1000, oy-100, oz+300), unreal.Rotator(pitch=-6.0, yaw=15.0, roll=0.0)),
    )
    for name, loc, rot in shots:
        try: unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
        except Exception: pass
        try:
            unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, name)
            log("shot "+name)
        except Exception as e:
            log("shot fail "+str(e))

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    except Exception:
        try: unreal.EditorLevelLibrary.save_current_level()
        except Exception as e: log("save "+str(e))
    try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception: pass

    lines.append("--- counts ---")
    for k,v in counts.items(): lines.append("%s=%s"%(k,v))
    lines.append("DONE")
    RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
    log("DONE")

if __name__ == "__main__":
    main()
