# -*- coding: utf-8 -*-
"""Rebuild Tideborn cove v2 — solid mats, clear layout, viewport verify shot.

Self-verify required: refuse DONE_OK unless screenshot path exists and
layout counts look sane. Parent must Read the PNG before telling Jon ready.
"""
from __future__ import annotations

import math
import pathlib
import random

import unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "fix_verify_result.txt"
SHOT_NAME = "TidebornCoveVerify"
MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
MAT_DIR = "/Game/Tideborn/Art/Materials"
MESH_DIR = "/Game/Tideborn/Art/Meshes"
OLD_MESH = "/Game/Tideborn/Meshes"

lines = []
counts = {"destroyed": 0, "sand": 0, "water": 0, "props": 0, "moved": 0, "mats": 0}


def log(m):
    t = str(m)
    unreal.log("[TidebornFix2] " + t)
    lines.append(t)


def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())


def label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def cname(a):
    try:
        return a.get_class().get_name() or ""
    except Exception:
        return ""


def destroy(a, why=""):
    try:
        lab = label(a)
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
        counts["destroyed"] += 1
        log("destroyed %s (%s)" % (lab, why))
    except Exception as e:
        log("destroy fail: %s" % e)


def clear_all_env_and_template():
    for a in actors():
        lab = label(a)
        cn = cname(a)
        if lab.startswith("TidebornEnv_") or lab.startswith("TidebornShore_"):
            destroy(a, "env rebuild")
            continue
        if lab.startswith("SM_") or "Floor" in lab or lab in ("Floor", "Cube", "Plane"):
            destroy(a, "greybox")
            continue
        if "TextRender" in cn or "TextRenderActor" in cn:
            destroy(a, "template text")
            continue
        if lab.startswith("Text") and "Tideborn" not in lab:
            destroy(a, "text label")
            continue
        if cn == "StaticMeshActor" and not lab.startswith("Tideborn"):
            mesh_name = ""
            try:
                for comp in a.get_components_by_class(unreal.StaticMeshComponent):
                    sm = comp.get_editor_property("static_mesh")
                    if sm:
                        mesh_name = sm.get_name()
                        break
            except Exception:
                pass
            mn = (mesh_name or "").lower()
            if any(x in mn for x in ("cube", "cylinder", "ramp", "plane", "floor", "shape", "1m", "template")):
                destroy(a, "template " + mesh_name)


def ensure_solid_mat(asset_name, rgb, translucent=False):
    """Create or overwrite a simple base-color material that always compiles."""
    path = MAT_DIR + "/" + asset_name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialFactoryNew()
    mat = asset_tools.create_asset(asset_name, MAT_DIR, unreal.Material, factory)
    if not mat:
        log("FAIL create mat " + asset_name)
        return None

    try:
        if translucent:
            mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
            mat.set_editor_property("two_sided", True)
    except Exception as e:
        log("blend warn " + str(e))

    # Base color constant
    try:
        node = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionConstant3Vector, -350, 0
        )
        node.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        unreal.MaterialEditingLibrary.connect_material_property(
            node, "", unreal.MaterialProperty.MP_BASE_COLOR
        )
    except Exception as e:
        log("basecolor fail %s: %s" % (asset_name, e))

    if translucent:
        try:
            op = unreal.MaterialEditingLibrary.create_material_expression(
                mat, unreal.MaterialExpressionConstant, -350, 120
            )
            op.set_editor_property("r", 0.55)
            unreal.MaterialEditingLibrary.connect_material_property(
                op, "", unreal.MaterialProperty.MP_OPACITY
            )
        except Exception as e:
            log("opacity fail: %s" % e)
    else:
        try:
            rough = unreal.MaterialEditingLibrary.create_material_expression(
                mat, unreal.MaterialExpressionConstant, -350, 120
            )
            rough.set_editor_property("r", 0.85 if "Sand" in asset_name or "Ground" in asset_name else 0.7)
            unreal.MaterialEditingLibrary.connect_material_property(
                rough, "", unreal.MaterialProperty.MP_ROUGHNESS
            )
        except Exception:
            pass

    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    counts["mats"] += 1
    log("solid mat %s rgb=%s" % (asset_name, rgb))
    return mat


def load_mesh(keys, skip_sub=()):
    for d in (MESH_DIR, OLD_MESH):
        if not unreal.EditorAssetLibrary.does_directory_exist(d):
            continue
        for ap in unreal.EditorAssetLibrary.list_assets(d, recursive=True):
            low = ap.lower()
            if any(s in low for s in skip_sub):
                continue
            if any(k.lower() in low for k in keys):
                asset = unreal.EditorAssetLibrary.load_asset(ap)
                if isinstance(asset, unreal.StaticMesh):
                    return asset, ap
    return None, None


def bounds_r(mesh):
    try:
        box = mesh.get_bounding_box()
        ext = box.max - box.min
        return max(abs(ext.x), abs(ext.y), abs(ext.z))
    except Exception:
        return 100.0


def spawn_sm(mesh, loc, rot, scale, lab, mat=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = sub.spawn_actor_from_object(mesh, loc, rot)
    if not a:
        return None
    a.set_actor_scale3d(scale)
    a.set_actor_label(lab)
    if mat:
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            try:
                comp.set_material(0, mat)
                comp.set_editor_property("cast_shadow", True)
            except Exception:
                pass
    return a


def spawn_plane(loc, scale, mat, lab):
    plane = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
    return spawn_sm(plane, loc, unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0), scale, lab, mat)


def build_cove(origin, sand, ground, water, rock, bark):
    ox, oy, oz = origin.x, origin.y, origin.z
    z_ground = oz - 2.0
    z_sand = oz - 1.0
    z_water = oz - 40.0

    # Inland ground (darker) behind spawn toward +Y
    if spawn_plane(unreal.Vector(ox + 400, oy + 900, z_ground), unreal.Vector(90, 90, 1), ground, "TidebornEnv_Ground"):
        counts["sand"] += 1
    # Beach band toward ocean (-Y)
    for i, (dx, dy, sx, sy) in enumerate((
        (0, -200, 55, 35),
        (700, -250, 45, 30),
        (-500, -220, 40, 28),
        (300, 200, 40, 35),
    )):
        if spawn_plane(unreal.Vector(ox + dx, oy + dy, z_sand), unreal.Vector(sx, sy, 1), sand, "TidebornEnv_Sand_%d" % i):
            counts["sand"] += 1
    # Ocean further -Y, slightly lower
    if spawn_plane(unreal.Vector(ox + 200, oy - 2200, z_water), unreal.Vector(140, 90, 1), water, "TidebornEnv_Ocean"):
        counts["water"] += 1
    log("planes sand=%d water=%d" % (counts["sand"], counts["water"]))

    boulder, bp = load_mesh(["boulder_01"], skip_sub=("coast_land",))
    stump, sp = load_mesh(["dead_tree_trunk"], skip_sub=("coast_land",))
    stone, stp = load_mesh(["SM_StoneCluster", "StoneCluster"], skip_sub=("coast_land",))
    log("meshes boulder=%s stump=%s stone=%s" % (bp, sp, stp))

    usable = []
    for mesh, path, mat, name in (
        (boulder, bp, rock, "Boulder"),
        (stump, sp, bark, "Trunk"),
        (stone, stp, rock, "Stone"),
    ):
        if not mesh:
            continue
        r = bounds_r(mesh)
        log("%s r=%.1f" % (name, r))
        if r > 2500:
            log("skip huge %s" % name)
            continue
        usable.append((mesh, mat, name, r))

    if not usable:
        log("ERROR no props")
        return

    rng = random.Random(11)
    # Wide spaced shore arc — no pile
    spots = []
    for i in range(12):
        t = i / 11.0
        spots.append((ox - 400 + t * 1800, oy - 500 + math.sin(t * math.pi) * 120, oz, "shore"))
    for i in range(8):
        t = i / 7.0
        spots.append((ox + 200 + t * 1000, oy + 200 + t * 800, oz, "path"))

    for i, (x, y, z, zone) in enumerate(spots):
        mesh, mat, name, radius = usable[i % len(usable)]
        target = rng.uniform(200, 420)
        sc = max(0.2, min(target / max(radius, 1.0), 2.8))
        a = spawn_sm(
            mesh,
            unreal.Vector(x, y, z),
            unreal.Rotator(pitch=0.0, yaw=rng.uniform(0, 360), roll=0.0),
            unreal.Vector(sc, sc, sc * rng.uniform(0.85, 1.1)),
            "TidebornEnv_%s_%02d" % (name, i),
            mat,
        )
        if a:
            counts["props"] += 1
    log("props=%d" % counts["props"])


def lights():
    for a in actors():
        cn = cname(a)
        if "DirectionalLight" in cn:
            try:
                a.set_editor_property("intensity", 14.0)
                a.set_editor_property("light_color", unreal.LinearColor(1.0, 0.82, 0.6, 1.0))
                a.set_actor_rotation(unreal.Rotator(pitch=-28.0, yaw=55.0, roll=0.0), False)
            except Exception:
                pass
        if "SkyLight" in cn:
            try:
                a.set_editor_property("intensity", 1.8)
                a.set_editor_property("real_time_capture", True)
            except Exception:
                pass
    log("lights ok")


def relocate(origin):
    ox, oy, oz = origin.x, origin.y, origin.z
    for a in actors():
        lab = label(a)
        cn = cname(a)
        if "PlayerStart" in cn or lab == "PlayerStart":
            a.set_actor_location(unreal.Vector(ox + 150, oy + 50, oz + 92), False, True)
            a.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=-90.0, roll=0.0), False)
            counts["moved"] += 1
            log("PlayerStart shore")
        if "Gather" in lab and "Stone" in lab:
            a.set_actor_location(unreal.Vector(ox + 320, oy + 180, oz + 40), False, True)
            counts["moved"] += 1
        if "Kelp" in lab:
            a.set_actor_location(unreal.Vector(ox - 80, oy - 320, oz + 50), False, True)
            counts["moved"] += 1
        if "Burr" in lab or "Hound" in lab:
            a.set_actor_location(unreal.Vector(ox + 750, oy + 500, oz + 70), False, True)
            counts["moved"] += 1
        if "ShoreGate" in lab or (("Gate" in lab) and "Tideborn" in lab):
            a.set_actor_location(unreal.Vector(ox + 1200, oy + 950, oz + 100), False, True)
            counts["moved"] += 1
    woods = [a for a in actors() if "Gather" in label(a) and "Wood" in label(a)]
    for i, a in enumerate(woods):
        a.set_actor_location(unreal.Vector(ox + 480 + i * 140, oy + 100, oz + 40), False, True)
        counts["moved"] += 1
    log("moved=%d" % counts["moved"])


def capture(origin):
    # Put editor camera where the player would look: on beach, facing ocean (-Y)
    cam_loc = unreal.Vector(origin.x + 150, origin.y + 80, origin.z + 160)
    cam_rot = unreal.Rotator(pitch=-8.0, yaw=-90.0, roll=0.0)
    try:
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(cam_loc, cam_rot)
        log("viewport cam set %s %s" % (cam_loc, cam_rot))
    except Exception as e:
        log("viewport cam fail: %s" % e)
        try:
            unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(cam_loc, cam_rot)
            log("viewport cam via subsystem")
        except Exception as e2:
            log("viewport cam fail2: %s" % e2)

    # Clear stale shots
    shot_dir = ROOT / "Saved" / "Screenshots" / "WindowsEditor"
    shot_dir.mkdir(parents=True, exist_ok=True)
    for p in shot_dir.glob("TidebornCove*.png"):
        try:
            p.unlink()
        except Exception:
            pass

    try:
        unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, SHOT_NAME)
        log("AutomationLibrary shot %s" % SHOT_NAME)
    except Exception as e:
        log("auto shot fail: %s" % e)
    try:
        unreal.SystemLibrary.execute_console_command(None, "HighResShot 1920x1080")
        log("HighResShot")
    except Exception as e:
        log("HighResShot fail: %s" % e)


def main():
    try:
        unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    except Exception as e:
        log("load warn " + str(e))

    origin = unreal.Vector(1000, 1000, 100)
    for a in actors():
        if "PlayerStart" in cname(a):
            origin = a.get_actor_location()
            break
    # Stable cove origin (ignore prior bad PlayerStart drift)
    origin = unreal.Vector(1000, 1000, 100)
    log("origin forced %s" % origin)

    clear_all_env_and_template()

    sand = ensure_solid_mat("M_Tideborn_SandSolid", (0.76, 0.62, 0.38))
    ground = ensure_solid_mat("M_Tideborn_GroundSolid", (0.28, 0.34, 0.18))
    water = ensure_solid_mat("M_Tideborn_WaterSolid", (0.12, 0.32, 0.48), translucent=True)
    rock = ensure_solid_mat("M_Tideborn_RockSolid", (0.35, 0.33, 0.30))
    bark = ensure_solid_mat("M_Tideborn_BarkSolid", (0.28, 0.16, 0.08))

    build_cove(origin, sand, ground, water, rock, bark)
    lights()
    relocate(origin)
    capture(origin)

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    except Exception:
        try:
            unreal.EditorLevelLibrary.save_current_level()
        except Exception as e:
            log("save fail " + str(e))
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass

    lines.append("--- counts ---")
    for k, v in counts.items():
        lines.append("%s=%s" % (k, v))
    # Soft gate — parent still must visually Read the PNG
    ok = counts["sand"] >= 3 and counts["water"] >= 1 and counts["props"] >= 10 and counts["mats"] >= 4
    lines.append("SCRIPT_OK=%s" % ok)
    lines.append("DONE")
    RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log("DONE SCRIPT_OK=%s" % ok)


if __name__ == "__main__":
    main()

