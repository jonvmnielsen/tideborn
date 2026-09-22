# -*- coding: utf-8 -*-
"""Build a living Tideborn shore cove on ThirdPersonMap.

Run via UnrealEditor-Cmd with the editor CLOSED:
  UnrealEditor-Cmd.exe Tideborn.uproject -ExecutePythonScript=Tools/art/build_world.py -unattended -nosplash

Idempotent: destroys prior TidebornEnv_* actors before re-dressing.
Does NOT destroy Tideborn_* gameplay actors, PlayerStart, or essential lights.
"""
from __future__ import annotations

import math
import pathlib
import random

import unreal

RESULT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\build_world_result.txt")
MAP_PATH = "/Game/ThirdPerson/Maps/ThirdPersonMap"

MESH_DIR = "/Game/Tideborn/Art/Meshes"
MAT_DIR = "/Game/Tideborn/Art/Materials"
HDRI_DIR = "/Game/Tideborn/Art/HDRI"

# Preferred mesh asset name fragments (imported CC0)
MESH_KEYS = [
    "boulder_01",
    "coast_land_rocks_02",
    "coast_land_rocks_03",
    "dead_tree_trunk",
]

lines = []
counts = {
    "inventory_hidden": 0,
    "inventory_destroyed": 0,
    "ground_planes": 0,
    "water_planes": 0,
    "env_props": 0,
    "gameplay_moved": 0,
    "lights_tweaked": 0,
}


def log(msg):
    text = str(msg)
    unreal.log("[TidebornBuildWorld] " + text)
    lines.append(text)


def actor_sub():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def level_sub():
    return unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def load_map():
    try:
        unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
        log("loaded map " + MAP_PATH)
    except Exception as e:
        log("load_map warn: " + str(e))


def label_of(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def class_name(a):
    try:
        return a.get_class().get_name()
    except Exception:
        return ""


def is_protected(a):
    """Keep Tideborn gameplay, PlayerStart, and lighting we still need."""
    lab = label_of(a)
    cls = class_name(a)
    low = lab.lower()
    if lab.startswith("Tideborn_") and not lab.startswith("TidebornEnv_"):
        return True
    if lab.startswith("Tideborn_P2_") or lab.startswith("TidebornArt_"):
        return True
    if "PlayerStart" in cls or "PlayerStart" in lab:
        return True
    if any(k in cls for k in ("DirectionalLight", "SkyLight", "SkyAtmosphere",
                              "ExponentialHeightFog", "VolumetricCloud",
                              "PostProcessVolume", "SphereReflectionCapture",
                              "PlayerCameraManager")):
        return True
    # Keep WorldSettings / GameMode
    if "WorldSettings" in cls or "GameMode" in cls:
        return True
    return False


def looks_like_default_greybox(a):
    """Heuristic for template Third Person grey platforms / boxes / BSP floors."""
    if is_protected(a):
        return False
    lab = label_of(a)
    cls = class_name(a)
    low = lab.lower()
    # Explicit env we own — skip
    if lab.startswith("TidebornEnv_"):
        return False
    # Common TP template names
    keywords = (
        "sm_chute", "sm_ramp", "sm_quarter", "floor", "platform", "block",
        "cube", "box", "bsp", "brush", "prototype", "levelpro", "grey", "gray",
        "template", "grid",
    )
    if any(k in low for k in keywords):
        return True
    # Large static mesh actors using engine / LevelPrototyping meshes
    try:
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            sm = comp.get_editor_property("static_mesh")
            if not sm:
                continue
            path = sm.get_path_name().lower()
            if "/levelprototyping/" in path or "/engine/basicshapes/" in path:
                # size gate: only hide big ones (template floors)
                try:
                    extent = a.get_actor_bounds(True)[1]  # origin, extent
                    if extent.x > 200 or extent.y > 200 or extent.z > 50:
                        return True
                except Exception:
                    return True
    except Exception:
        pass
    if "Brush" in cls or "BSP" in cls:
        return True
    return False


def inventory_and_clear_greybox():
    sub = actor_sub()
    actors = list(sub.get_all_level_actors())
    log("--- inventory (%d actors) ---" % len(actors))
    for a in actors:
        lab = label_of(a)
        cls = class_name(a)
        if looks_like_default_greybox(a) or (lab and any(
            k in lab.lower() for k in ("floor", "platform", "blockout", "proto")
        ) and not is_protected(a)):
            log("greybox candidate: %s [%s]" % (lab, cls))
    # Destroy/hide large default floors/boxes
    for a in list(sub.get_all_level_actors()):
        if not looks_like_default_greybox(a):
            continue
        lab = label_of(a)
        # Prefer hide for safety on ambiguous; destroy obvious prototype floors
        low = lab.lower()
        destroy = any(k in low for k in (
            "floor", "sm_chute", "sm_ramp", "sm_quarter", "platform", "block", "cube"
        )) or "LevelPrototyping" in (a.get_path_name() if hasattr(a, "get_path_name") else "")
        try:
            if destroy:
                sub.destroy_actor(a)
                counts["inventory_destroyed"] += 1
                log("destroyed greybox: " + lab)
            else:
                a.set_actor_hidden_in_game(True)
                a.set_is_temporarily_hidden_in_editor(True)
                counts["inventory_hidden"] += 1
                log("hid greybox: " + lab)
        except Exception as e:
            log("greybox clear fail %s: %s" % (lab, e))


def clear_prior_env():
    sub = actor_sub()
    for a in list(sub.get_all_level_actors()):
        lab = label_of(a)
        if lab.startswith("TidebornEnv_"):
            try:
                sub.destroy_actor(a)
                log("removed prior " + lab)
            except Exception as e:
                log("remove fail " + lab + ": " + str(e))


def find_asset(folder, substrings):
    try:
        assets = unreal.EditorAssetLibrary.list_assets(folder, recursive=True)
    except Exception:
        return None
    for ap in assets:
        low = ap.lower()
        if all(s.lower() in low for s in substrings):
            return ap
        if any(s.lower() in low for s in substrings) and len(substrings) == 1:
            return ap
    # looser: any match
    for ap in assets:
        low = ap.lower()
        for s in substrings:
            if s.lower() in low:
                return ap
    return None


def load_mat(name_fragment):
    path = find_asset(MAT_DIR, [name_fragment])
    if not path:
        # try exact common names
        for candidate in (
            "%s/M_Tideborn_%s" % (MAT_DIR, name_fragment),
            "%s/%s" % (MAT_DIR, name_fragment),
        ):
            if unreal.EditorAssetLibrary.does_asset_exist(candidate):
                path = candidate
                break
    if not path:
        return None
    return unreal.EditorAssetLibrary.load_asset(path)


def load_mesh(key):
    path = find_asset(MESH_DIR, [key])
    if not path:
        return None
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if isinstance(asset, unreal.StaticMesh):
        return asset
    return None


def try_create_landscape():
    """Attempt a small Landscape; fall back False if API unavailable."""
    try:
        # UE5 Python landscape creation is limited; try LandscapeEditor or spawn.
        if not hasattr(unreal, "Landscape"):
            log("Landscape class missing — will use ground planes")
            return False
        # Check existing
        for a in actor_sub().get_all_level_actors():
            if "Landscape" in class_name(a):
                log("Landscape already present: " + label_of(a))
                return True
        # Full LandscapeProxy creation via Editor is unreliable unattended;
        # document limitation and use planes.
        log("SKIP real Landscape create (unattended API hard) — using sand/ground planes")
        return False
    except Exception as e:
        log("landscape attempt: " + str(e))
        return False


def spawn_plane(location, scale, material, label):
    """Spawn engine plane (100uu) scaled to cover area."""
    plane = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
    if not plane:
        log("ERROR: missing /Engine/BasicShapes/Plane")
        return None
    sub = actor_sub()
    actor = sub.spawn_actor_from_object(plane, location, unreal.Rotator(0, 0, 0))
    if not actor:
        return None
    actor.set_actor_scale3d(scale)
    actor.set_actor_label(label)
    if material:
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            try:
                comp.set_material(0, material)
                # translucent water handled by caller material or dynamic
            except Exception:
                pass
    return actor


def make_water_material():
    """Create or load a simple translucent blue water material."""
    path = "/Game/Tideborn/Art/Materials/M_Tideborn_WaterSimple"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    try:
        if not unreal.EditorAssetLibrary.does_directory_exist(MAT_DIR):
            unreal.EditorAssetLibrary.make_directory(MAT_DIR)
        factory = unreal.MaterialFactoryNew()
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_Tideborn_WaterSimple", MAT_DIR, unreal.Material, factory
        )
        if not mat:
            return None
        mel = unreal.MaterialEditingLibrary
        # translucent blend
        try:
            mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        except Exception:
            try:
                mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
            except Exception:
                pass
        try:
            mat.set_editor_property("two_sided", True)
        except Exception:
            pass
        # constant color blue-green
        const = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
        const.set_editor_property("constant", unreal.LinearColor(0.05, 0.25, 0.45, 1.0))
        mel.connect_material_property(const, "", unreal.MaterialProperty.MP_BASE_COLOR)
        opacity = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 120)
        opacity.set_editor_property("r", 0.45)
        mel.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
        mel.recompile_material(mat)
        unreal.EditorAssetLibrary.save_asset(path)
        log("created water material " + path)
        return mat
    except Exception as e:
        log("water material fail: " + str(e))
        return None


def build_ground(sand_mat, ground_mat, origin):
    """Large cove: sand shore strip (south/ocean edge) + inland ground."""
    # Plane default 100x100; scale 40 => 4000uu (~40m)
    # Layout: ocean along -Y edge; shore band; inland +Y
    ox, oy, oz = origin.x, origin.y, origin.z

    # Inland ground (larger)
    g = spawn_plane(
        unreal.Vector(ox + 800, oy + 600, oz - 5),
        unreal.Vector(55, 45, 1),
        ground_mat or sand_mat,
        "TidebornEnv_Ground_Inland",
    )
    if g:
        counts["ground_planes"] += 1

    # Shore sand strip closer to ocean (-Y)
    for i, (dx, dy, sx, sy) in enumerate((
        (400, -200, 50, 18),
        (1200, -150, 40, 16),
        (-200, -180, 30, 14),
    )):
        p = spawn_plane(
            unreal.Vector(ox + dx, oy + dy, oz - 2),
            unreal.Vector(sx, sy, 1),
            sand_mat or ground_mat,
            "TidebornEnv_SandShore_%d" % (i + 1),
        )
        if p:
            counts["ground_planes"] += 1

    # Extra sand tongue toward inland path
    p = spawn_plane(
        unreal.Vector(ox + 600, oy + 150, oz - 3),
        unreal.Vector(25, 20, 1),
        sand_mat or ground_mat,
        "TidebornEnv_SandPath",
    )
    if p:
        counts["ground_planes"] += 1
    log("ground planes=%d" % counts["ground_planes"])


def build_water(origin):
    water_mat = make_water_material()
    ox, oy, oz = origin.x, origin.y, origin.z
    # Ocean along -Y, slightly below shore
    w = spawn_plane(
        unreal.Vector(ox + 600, oy - 1400, oz - 40),
        unreal.Vector(80, 50, 1),
        water_mat,
        "TidebornEnv_Ocean",
    )
    if w:
        counts["water_planes"] += 1
        # Ensure translucent look even if material assign failed
        if water_mat:
            for comp in w.get_components_by_class(unreal.StaticMeshComponent):
                try:
                    comp.set_material(0, water_mat)
                except Exception:
                    pass
    # Try WaterBody if plugin present
    try:
        wb_cls = getattr(unreal, "WaterBodyOcean", None) or getattr(unreal, "WaterBodyLake", None)
        if wb_cls:
            log("WaterBody class present but skipping spawn (plugin may need setup) — plane used")
        else:
            log("WaterBody plugin not available — translucent plane used")
    except Exception:
        pass
    log("water planes=%d" % counts["water_planes"])


def scatter_props(origin):
    rng = random.Random(42)
    meshes = []
    for key in MESH_KEYS:
        m = load_mesh(key)
        if m:
            meshes.append((key, m))
            log("mesh ok: " + key)
        else:
            log("mesh MISSING: " + key)
    if not meshes:
        # fallback to Tideborn gameplay meshes for some density
        for fallback in (
            "/Game/Tideborn/Meshes/SM_StoneCluster",
            "/Game/Tideborn/Meshes/SM_WoodStump",
        ):
            if unreal.EditorAssetLibrary.does_asset_exist(fallback):
                asset = unreal.EditorAssetLibrary.load_asset(fallback)
                if isinstance(asset, unreal.StaticMesh):
                    meshes.append((fallback.split("/")[-1], asset))
        log("using fallback meshes count=%d" % len(meshes))
    if not meshes:
        log("ERROR: no prop meshes available")
        return

    ox, oy, oz = origin.x, origin.y, origin.z
    # Dense scatter 28 instances along shore + inland path
    placements = []
    # Shore line cluster (-Y)
    for i in range(16):
        placements.append((
            ox + rng.uniform(-400, 1600),
            oy + rng.uniform(-500, 50),
            oz + rng.uniform(-5, 15),
            "shore",
        ))
    # Inland path toward gate (+X / +Y)
    for i in range(12):
        placements.append((
            ox + rng.uniform(200, 1400),
            oy + rng.uniform(50, 900),
            oz + rng.uniform(-5, 20),
            "inland",
        ))

    sub = actor_sub()
    idx = 0
    for x, y, z, zone in placements:
        key, mesh = meshes[idx % len(meshes)]
        yaw = rng.uniform(0, 360)
        sc = rng.uniform(0.7, 1.8)
        if "boulder" in key.lower():
            sc = rng.uniform(0.9, 2.2)
        if "trunk" in key.lower() or "tree" in key.lower():
            sc = rng.uniform(0.8, 1.5)
        actor = sub.spawn_actor_from_object(
            mesh,
            unreal.Vector(x, y, z),
            unreal.Rotator(0, yaw, 0),
        )
        if actor:
            actor.set_actor_scale3d(unreal.Vector(sc, sc, sc))
            actor.set_actor_label("TidebornEnv_%s_%02d_%s" % (zone, idx + 1, key[:20]))
            counts["env_props"] += 1
        idx += 1
    log("env props=%d" % counts["env_props"])


def tweak_lighting():
    sub = actor_sub()
    has_dir = has_sky = has_fog = has_atmo = False
    for a in sub.get_all_level_actors():
        cls = class_name(a)
        try:
            if "DirectionalLight" in cls:
                has_dir = True
                # warm sunset
                try:
                    a.set_editor_property("intensity", 10.0)
                except Exception:
                    pass
                try:
                    # light color warm
                    lc = a.get_component_by_class(unreal.DirectionalLightComponent)
                    if lc:
                        lc.set_editor_property("intensity", 10.0)
                        lc.set_editor_property(
                            "light_color", unreal.Color(255, 178, 120, 255)
                        )
                        # pitch toward horizon
                        a.set_actor_rotation(unreal.Rotator(-25, -40, 0), False)
                except Exception as e:
                    log("dir light detail: " + str(e))
                counts["lights_tweaked"] += 1
            if "SkyLight" in cls:
                has_sky = True
                try:
                    a.set_editor_property("real_time_capture", True)
                except Exception:
                    pass
                try:
                    sc = a.get_component_by_class(unreal.SkyLightComponent)
                    if sc:
                        sc.set_editor_property("real_time_capture", True)
                        sc.set_editor_property("intensity", 1.15)
                except Exception:
                    pass
                counts["lights_tweaked"] += 1
            if "ExponentialHeightFog" in cls:
                has_fog = True
                try:
                    fc = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
                    if fc:
                        fc.set_editor_property("fog_density", 0.018)
                        fc.set_editor_property(
                            "fog_inbounds_color",
                            unreal.LinearColor(0.85, 0.55, 0.35, 1.0),
                        )
                except Exception:
                    pass
                counts["lights_tweaked"] += 1
            if "SkyAtmosphere" in cls:
                has_atmo = True
                counts["lights_tweaked"] += 1
        except Exception as e:
            log("light tweak err: " + str(e))

    # Spawn missing essentials
    if not has_dir:
        try:
            d = sub.spawn_actor_from_class(
                unreal.DirectionalLight, unreal.Vector(0, 0, 400), unreal.Rotator(-25, -40, 0)
            )
            if d:
                d.set_actor_label("TidebornEnv_DirectionalSunset")
                counts["lights_tweaked"] += 1
                log("spawned DirectionalLight")
        except Exception as e:
            log("spawn dir fail: " + str(e))
    if not has_sky:
        try:
            s = sub.spawn_actor_from_class(
                unreal.SkyLight, unreal.Vector(0, 0, 300), unreal.Rotator()
            )
            if s:
                s.set_actor_label("TidebornEnv_SkyLight")
                try:
                    sc = s.get_component_by_class(unreal.SkyLightComponent)
                    if sc:
                        sc.set_editor_property("real_time_capture", True)
                except Exception:
                    pass
                counts["lights_tweaked"] += 1
                log("spawned SkyLight")
        except Exception as e:
            log("spawn sky fail: " + str(e))
    if not has_fog:
        try:
            f = sub.spawn_actor_from_class(
                unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0), unreal.Rotator()
            )
            if f:
                f.set_actor_label("TidebornEnv_HeightFog")
                counts["lights_tweaked"] += 1
                log("spawned ExponentialHeightFog")
        except Exception as e:
            log("spawn fog fail: " + str(e))
    if not has_atmo:
        try:
            atmo_cls = getattr(unreal, "SkyAtmosphere", None)
            if atmo_cls:
                at = sub.spawn_actor_from_class(atmo_cls, unreal.Vector(0, 0, 0), unreal.Rotator())
                if at:
                    at.set_actor_label("TidebornEnv_SkyAtmosphere")
                    counts["lights_tweaked"] += 1
                    log("spawned SkyAtmosphere")
        except Exception as e:
            log("spawn atmo fail: " + str(e))

    # HDRI Backdrop if available
    hdri = find_asset(HDRI_DIR, ["industrial_sunset", "puresky", "hdri", "HDRI"])
    try:
        hdri_cls = getattr(unreal, "HDRIBackdrop", None)
        if hdri_cls and hdri:
            # remove prior
            for a in list(sub.get_all_level_actors()):
                if label_of(a).startswith("TidebornEnv_HDRI"):
                    sub.destroy_actor(a)
            hb = sub.spawn_actor_from_class(
                hdri_cls, unreal.Vector(0, 0, 0), unreal.Rotator()
            )
            if hb:
                hb.set_actor_label("TidebornEnv_HDRIBackdrop")
                tex = unreal.EditorAssetLibrary.load_asset(hdri)
                try:
                    hb.set_editor_property("cubemap", tex)
                except Exception:
                    try:
                        # some versions use different prop
                        for comp in hb.get_components_by_class(unreal.ActorComponent):
                            pass
                    except Exception:
                        pass
                log("HDRI Backdrop placed with " + str(hdri))
            else:
                log("HDRI Backdrop spawn returned None")
        else:
            log("HDRI Backdrop plugin/class or texture unavailable (hdri=%s) — lights only" % hdri)
    except Exception as e:
        log("HDRI backdrop fail: " + str(e))

    log("lights_tweaked=%d dir=%s sky=%s fog=%s atmo=%s" % (
        counts["lights_tweaked"], has_dir, has_sky, has_fog, has_atmo
    ))


def find_player_start():
    sub = actor_sub()
    for a in sub.get_all_level_actors():
        if isinstance(a, unreal.PlayerStart) or "PlayerStart" in class_name(a) or "PlayerStart" in label_of(a):
            return a
    return None


def relayout_gameplay(origin):
    """Place PlayerStart on sandy shore facing inland; arrange gather/creatures/gate."""
    sub = actor_sub()
    ox, oy, oz = origin.x, origin.y, origin.z

    # Shore spawn facing inland (+Y)
    shore = unreal.Vector(ox + 200, oy - 80, oz + 100)
    inland_yaw = 90.0  # face +Y

    ps = find_player_start()
    if ps:
        ps.set_actor_location(shore, False, True)
        ps.set_actor_rotation(unreal.Rotator(0, inland_yaw, 0), False)
        counts["gameplay_moved"] += 1
        log("PlayerStart -> shore %s yaw=%s" % (shore, inland_yaw))
    else:
        try:
            ps = sub.spawn_actor_from_class(unreal.PlayerStart, shore, unreal.Rotator(0, inland_yaw, 0))
            if ps:
                ps.set_actor_label("PlayerStart")
                counts["gameplay_moved"] += 1
                log("spawned PlayerStart")
        except Exception as e:
            log("PlayerStart fail: " + str(e))

    def move_matching(pred, loc, rot=None, tag=""):
        moved = 0
        for a in sub.get_all_level_actors():
            lab = label_of(a)
            cls = class_name(a)
            if pred(lab, cls, a):
                a.set_actor_location(loc, False, True)
                if rot is not None:
                    a.set_actor_rotation(rot, False)
                moved += 1
                counts["gameplay_moved"] += 1
                log("moved %s -> %s (%s)" % (lab or cls, loc, tag))
        return moved

    # Wood / Stone gather nodes near shore
    wood_n = 0
    stone_n = 0
    for a in sub.get_all_level_actors():
        lab = label_of(a).lower()
        cls = class_name(a).lower()
        if "gather" in lab or "gather" in cls or "woodstump" in lab or "stonecluster" in lab:
            if "wood" in lab or "stump" in lab or "wood" in cls:
                loc = unreal.Vector(ox + 350 + wood_n * 120, oy + 40, oz + 40)
                a.set_actor_location(loc, False, True)
                wood_n += 1
                counts["gameplay_moved"] += 1
                log("gather wood -> " + str(loc))
            elif "stone" in lab or "rock" in lab or "stone" in cls:
                loc = unreal.Vector(ox + 280 + stone_n * 130, oy + 160, oz + 40)
                a.set_actor_location(loc, False, True)
                stone_n += 1
                counts["gameplay_moved"] += 1
                log("gather stone -> " + str(loc))
            else:
                # generic gather alternate
                loc = unreal.Vector(ox + 400 + (wood_n + stone_n) * 100, oy + 80, oz + 40)
                a.set_actor_location(loc, False, True)
                counts["gameplay_moved"] += 1
                log("gather generic -> " + str(loc))

    # Kelp-back along shore
    move_matching(
        lambda lab, cls, a: ("kelp" in lab.lower()) or ("KelpBack" in cls) or ("TidebornKelpBack" in cls),
        unreal.Vector(ox + 80, oy - 320, oz + 60),
        unreal.Rotator(0, 20, 0),
        "kelp shore",
    )
    # Burr-hound slightly inland
    move_matching(
        lambda lab, cls, a: ("burr" in lab.lower()) or ("BurrHound" in cls) or ("TidebornBurrHound" in cls),
        unreal.Vector(ox + 650, oy + 420, oz + 80),
        unreal.Rotator(0, -30, 0),
        "hound inland",
    )
    # Shore Gate vista up the path
    move_matching(
        lambda lab, cls, a: ("shoregate" in lab.lower().replace("_", ""))
        or ("ShoreGate" in cls)
        or ("TidebornShoreGate" in cls)
        or ("gate" in lab.lower() and "tideborn" in lab.lower()),
        unreal.Vector(ox + 1100, oy + 950, oz + 120),
        unreal.Rotator(0, 180, 0),
        "gate vista",
    )
    # Beacons / path posts along path to gate
    beacon_i = 0
    for a in sub.get_all_level_actors():
        lab = label_of(a)
        cls = class_name(a)
        if ("beacon" in lab.lower()) or ("pathpost" in lab.lower().replace("_", "")) or ("LandmarkBeacon" in cls):
            t = 0.25 + beacon_i * 0.22
            loc = unreal.Vector(
                ox + 200 + (1100 - 200) * t,
                oy - 80 + (950 + 80) * t + ((-70) if beacon_i % 2 == 0 else 70),
                oz + 50,
            )
            a.set_actor_location(loc, False, True)
            beacon_i += 1
            counts["gameplay_moved"] += 1
            log("beacon %d -> %s" % (beacon_i, loc))

    log("gameplay_moved=%d wood=%d stone=%d beacons=%d" % (
        counts["gameplay_moved"], wood_n, stone_n, beacon_i
    ))


def save_all():
    try:
        level_sub().save_current_level()
        log("saved current level")
    except Exception as e:
        log("save_current_level: " + str(e))
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        log("saved dirty packages")
    except Exception as e:
        log("save_dirty: " + str(e))


def write_result():
    lines.append("--- counts ---")
    for k, v in counts.items():
        lines.append("%s=%s" % (k, v))
    lines.append("DONE")
    try:
        RESULT.parent.mkdir(parents=True, exist_ok=True)
        RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        log("wrote " + str(RESULT))
    except Exception as e:
        unreal.log_error("[TidebornBuildWorld] result write fail: " + str(e))


def main():
    log("=== Tideborn build_world start ===")
    load_map()
    clear_prior_env()
    inventory_and_clear_greybox()

    ps = find_player_start()
    origin = ps.get_actor_location() if ps else unreal.Vector(0, 0, 100)
    log("origin=%s" % origin)

    sand = load_mat("Sand") or load_mat("M_Tideborn_Sand")
    ground = load_mat("Ground") or load_mat("M_Tideborn_Ground")
    log("sand_mat=%s ground_mat=%s" % (bool(sand), bool(ground)))

    try_create_landscape()
    build_ground(sand, ground, origin)
    build_water(origin)
    scatter_props(origin)
    tweak_lighting()
    relayout_gameplay(origin)
    save_all()
    write_result()
    log("=== Tideborn build_world complete ===")


if __name__ == "__main__":
    main()
