# -*- coding: utf-8 -*-
"""Fix broken Tideborn cove and capture verification screenshots.

Problems from Jon's shot:
- Default grey floor still present
- coast_land_rocks meshes exploded/piled (bad for dressing)
- Sand/water not visible
Must self-verify via HighResShot before claiming ready.
"""
from __future__ import annotations

import math
import pathlib
import random

import unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "fix_verify_result.txt"
SHOT_DIR = ROOT / "Saved" / "Screenshots" / "WindowsEditor"
OUT_SHOT = ROOT / "Tools" / "art" / "verify_cove.png"

MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"
MESH_DIR = "/Game/Tideborn/Art/Meshes"
MAT_DIR = "/Game/Tideborn/Art/Materials"
OLD_MESH_DIR = "/Game/Tideborn/Meshes"

lines = []
counts = {"destroyed": 0, "sand": 0, "water": 0, "props": 0, "moved": 0}


def log(m):
    t = str(m)
    unreal.log("[TidebornFix] " + t)
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
    global counts
    try:
        lab = label(a)
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
        counts["destroyed"] += 1
        log("destroyed %s (%s)" % (lab, why))
    except Exception as e:
        log("destroy fail %s: %s" % (label(a), e))


def clear_bad():
    """Remove greybox floor, template text, broken env, prior env/shore props."""
    keep_prefixes = (
        "Tideborn_Gather", "Tideborn_P2_", "Tideborn_Beacon", "TidebornLandmark",
        "BP_", "PlayerStart",
    )
    # Never destroy these class-ish labels
    for a in actors():
        lab = label(a)
        cn = cname(a)
        low = lab.lower()

        # Always wipe prior env dressing to rebuild clean
        if lab.startswith("TidebornEnv_") or lab.startswith("TidebornShore_"):
            destroy(a, "rebuild env")
            continue

        # Template / greybox
        if lab.startswith("SM_") or lab.startswith("Brush") or "Floor" in lab or lab == "Floor":
            destroy(a, "greybox")
            continue
        if "TextRender" in cn or "ThirdPerson" in lab or lab.startswith("Text"):
            # floating 'ThirdPerson' text
            if "Tideborn" not in lab:
                destroy(a, "template text")
                continue

        # Default template platforms often named differently
        if cn == "StaticMeshActor" and not lab.startswith("Tideborn"):
            # Inspect mesh name
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
            if any(x in mn for x in ("cube", "cylinder", "ramp", "plane", "floor", "template", "shape")):
                # Keep our new planes if labeled TidebornEnv - already handled
                if not lab.startswith("Tideborn"):
                    destroy(a, "template mesh " + mesh_name)
                    continue


def load_asset(path):
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    return None


def find_mesh(keys):
    # Prefer small readable meshes
    search_dirs = [MESH_DIR, OLD_MESH_DIR]
    for d in search_dirs:
        if not unreal.EditorAssetLibrary.does_directory_exist(d):
            continue
        assets = unreal.EditorAssetLibrary.list_assets(d, recursive=True)
        for key in keys:
            for ap in assets:
                if key.lower() in ap.lower():
                    asset = unreal.EditorAssetLibrary.load_asset(ap)
                    if isinstance(asset, unreal.StaticMesh):
                        # Skip huge coast kits that exploded in previous build
                        if "coast_land_rocks" in ap.lower():
                            continue
                        return asset, ap
    return None, None


def mesh_bounds_radius(mesh):
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
                # Force opaque look
                try:
                    comp.set_editor_property("cast_shadow", True)
                except Exception:
                    pass
            except Exception:
                pass
    return a


def spawn_plane(loc, scale, mat, lab):
    plane = load_asset("/Engine/BasicShapes/Plane")
    if not plane:
        log("ERROR no plane")
        return None
    return spawn_sm(plane, loc, unreal.Rotator(0, 0, 0), scale, lab, mat)


def build_ground(origin, sand, ground):
    ox, oy, oz = origin.x, origin.y, origin.z
    # Raise slightly so we never sit under leftover collision
    z = oz - 1.0
    # Very large inland ground
    if spawn_plane(unreal.Vector(ox + 600, oy + 400, z), unreal.Vector(80, 70, 1), ground or sand, "TidebornEnv_Ground"):
        counts["sand"] += 1
    # Shore sand strip toward -Y (ocean)
    for i, (dx, dy, sx, sy) in enumerate((
        (200, -350, 70, 28),
        (900, -300, 55, 24),
        (-300, -320, 45, 22),
        (500, 50, 35, 30),
    )):
        if spawn_plane(unreal.Vector(ox + dx, oy + dy, z + 1), unreal.Vector(sx, sy, 1), sand or ground, "TidebornEnv_Sand_%d" % i):
            counts["sand"] += 1
    log("ground/sand planes=%d" % counts["sand"])


def build_water(origin, water_mat):
    ox, oy, oz = origin.x, origin.y, origin.z
    # Ocean in front of spawn looking toward -Y from PlayerStart yaw 90 means +X look?
    # Place ocean as big plane clearly visible: around spawn -Y
    w = spawn_plane(
        unreal.Vector(ox + 400, oy - 1800, oz - 35),
        unreal.Vector(120, 70, 1),
        water_mat,
        "TidebornEnv_Ocean",
    )
    if w:
        counts["water"] += 1
    log("water=%d" % counts["water"])


def dress_props(origin, rock_mat, bark_mat):
    rng = random.Random(7)
    boulder, bp = find_mesh(["boulder_01"])
    stump, sp = find_mesh(["dead_tree_trunk", "WoodStump", "SM_WoodStump"])
    stone, stp = find_mesh(["SM_StoneCluster", "StoneCluster"])
    log("boulder=%s stump=%s stone=%s" % (bp, sp, stp))

    usable = []
    for mesh, path, mat, name, sc_range in (
        (boulder, bp, rock_mat, "Boulder", (1.2, 2.5)),
        (stump, sp, bark_mat, "Trunk", (0.9, 1.6)),
        (stone, stp, rock_mat, "Stone", (1.0, 2.0)),
    ):
        if mesh:
            r = mesh_bounds_radius(mesh)
            log("%s bounds_radius=%.1f" % (name, r))
            # If mesh is enormous (coast kit leftover), skip
            if r > 5000:
                log("SKIP %s too large radius" % name)
                continue
            usable.append((mesh, mat, name, sc_range, r))

    if not usable:
        log("ERROR no usable prop meshes")
        return

    ox, oy, oz = origin.x, origin.y, origin.z
    # Place along a shore arc with spacing - NO stacking
    placements = []
    # Shore arc
    for i in range(14):
        t = i / 13.0
        x = ox + (-200 + t * 1600) + rng.uniform(-40, 40)
        y = oy + (-450 + math.sin(t * math.pi) * 80) + rng.uniform(-30, 30)
        placements.append((x, y, oz, "shore"))
    # Inland path
    for i in range(10):
        t = i / 9.0
        x = ox + 300 + t * 900 + rng.uniform(-50, 50)
        y = oy + 100 + t * 700 + rng.uniform(-40, 40)
        placements.append((x, y, oz, "path"))

    for i, (x, y, z, zone) in enumerate(placements):
        mesh, mat, name, sc_range, radius = usable[i % len(usable)]
        # Scale so visual size ~150-400 uu
        target = rng.uniform(180, 380)
        base_sc = target / max(radius, 1.0)
        base_sc = max(0.15, min(base_sc, 3.0))
        sc = base_sc * rng.uniform(sc_range[0] / 1.5, sc_range[1] / 1.5)
        yaw = rng.uniform(0, 360)
        a = spawn_sm(
            mesh,
            unreal.Vector(x, y, z),
            unreal.Rotator(0, yaw, 0),
            unreal.Vector(sc, sc, sc),
            "TidebornEnv_%s_%02d" % (name, i),
            mat,
        )
        if a:
            counts["props"] += 1
    log("props=%d" % counts["props"])


def tweak_lights():
    for a in actors():
        cn = cname(a)
        if "DirectionalLight" in cn:
            try:
                a.set_editor_property("intensity", 12.0)
                a.set_editor_property("light_color", unreal.LinearColor(1.0, 0.78, 0.55, 1.0))
                a.set_actor_rotation(unreal.Rotator(-35, 40, 0), False)
            except Exception:
                pass
        if "SkyLight" in cn:
            try:
                a.set_editor_property("intensity", 1.6)
                a.set_editor_property("real_time_capture", True)
            except Exception:
                pass
        if "ExponentialHeightFog" in cn:
            try:
                a.set_editor_property("fog_density", 0.02)
                a.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.45, 0.55, 0.7, 1.0))
            except Exception:
                pass
    log("lights tweaked")


def relocate_gameplay(origin):
    ox, oy, oz = origin.x, origin.y, origin.z
    # Spawn faces ocean (-Y)
    for a in actors():
        lab = label(a)
        cn = cname(a)
        if "PlayerStart" in cn or lab == "PlayerStart":
            a.set_actor_location(unreal.Vector(ox + 200, oy - 50, oz + 100), False, True)
            a.set_actor_rotation(unreal.Rotator(0, -90, 0), False)  # face -Y ocean
            counts["moved"] += 1
            log("PlayerStart to shore facing ocean")
        if "Gather" in lab and "Stone" in lab:
            a.set_actor_location(unreal.Vector(ox + 350, oy + 120, oz + 40), False, True)
            counts["moved"] += 1
        if "Gather" in lab and "Wood" in lab:
            # stagger woods
            pass
        if "Kelp" in lab:
            a.set_actor_location(unreal.Vector(ox - 50, oy - 280, oz + 60), False, True)
            counts["moved"] += 1
        if "Burr" in lab or "Hound" in lab:
            a.set_actor_location(unreal.Vector(ox + 700, oy + 450, oz + 80), False, True)
            counts["moved"] += 1
        if "ShoreGate" in lab or "Gate" in lab:
            a.set_actor_location(unreal.Vector(ox + 1100, oy + 900, oz + 120), False, True)
            counts["moved"] += 1

    woods = [a for a in actors() if "Gather" in label(a) and "Wood" in label(a)]
    for i, a in enumerate(woods):
        a.set_actor_location(unreal.Vector(ox + 450 + i * 120, oy + 80, oz + 40), False, True)
        counts["moved"] += 1

    beacons = [a for a in actors() if "Beacon" in label(a) or "Landmark" in label(a)]
    for i, a in enumerate(beacons[:3]):
        t = (i + 1) / 4.0
        a.set_actor_location(
            unreal.Vector(ox + 200 + t * 900, oy - 50 + t * 900, oz + 50),
            False, True,
        )
        counts["moved"] += 1
    log("gameplay_moved=%d" % counts["moved"])


def capture_shot(origin):
    """Place a camera looking at the cove and take a high-res shot."""
    try:
        SHOT_DIR.mkdir(parents=True, exist_ok=True)
        # Spawn camera
        cam_loc = unreal.Vector(origin.x + 200, origin.y - 50, origin.z + 220)
        # Look toward shore rocks and ocean (-Y)
        cam = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
            unreal.CameraActor, cam_loc, unreal.Rotator(-12, -90, 0)
        )
        if cam:
            cam.set_actor_label("TidebornEnv_VerifyCam")
        # Console highres shot
        unreal.SystemLibrary.execute_console_command(None, "HighResShot 1920x1080")
        log("HighResShot requested")
        # Also try EditorUtility
        try:
            unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, "TidebornCoveVerify")
            log("AutomationLibrary screenshot requested")
        except Exception as e:
            log("AutomationLibrary shot fail: " + str(e))
        return True
    except Exception as e:
        log("capture fail: " + str(e))
        return False


def main():
    try:
        unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    except Exception as e:
        log("load warn " + str(e))

    # Origin from PlayerStart if any
    origin = unreal.Vector(1000, 1000, 100)
    for a in actors():
        if "PlayerStart" in cname(a):
            origin = a.get_actor_location()
            break

    log("origin %s" % origin)
    clear_bad()

    sand = load_asset(MAT_DIR + "/M_Tideborn_Sand") or load_asset(MAT_DIR + "/M_Tideborn_Ground")
    ground = load_asset(MAT_DIR + "/M_Tideborn_Ground") or sand
    rock = load_asset(MAT_DIR + "/M_Tideborn_RockBoulder") or load_asset(MAT_DIR + "/M_Tideborn_RockShore") or load_asset(MAT_DIR + "/M_Tideborn_RockACG")
    bark = load_asset(MAT_DIR + "/M_Tideborn_Bark") or load_asset(MAT_DIR + "/M_Tideborn_BarkACG")
    water = load_asset(MAT_DIR + "/M_Tideborn_WaterSimple")
    log("mats sand=%s ground=%s rock=%s bark=%s water=%s" % (bool(sand), bool(ground), bool(rock), bool(bark), bool(water)))

    build_ground(origin, sand, ground)
    build_water(origin, water)
    dress_props(origin, rock, bark)
    tweak_lights()
    relocate_gameplay(origin)
    capture_shot(origin)

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    except Exception:
        unreal.EditorLevelLibrary.save_current_level()
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass

    lines.append("--- counts ---")
    for k, v in counts.items():
        lines.append("%s=%s" % (k, v))
    lines.append("DONE")
    RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log("DONE")


if __name__ == "__main__":
    main()