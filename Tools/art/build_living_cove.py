# -*- coding: utf-8 -*-
"""Build a living Tideborn coastal cove — fix PBR, layout, gameplay, verify shots.

Pass bar (parent must Read PNGs): sand reads as sand (not white/grey grid),
water edge visible, rocks/trunks spaced with rock/bark textures, no checkerboard
on gather/creatures/gate, no template text/floor, spawn faces ocean.
"""
from __future__ import annotations

import math
import pathlib
import random

import unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "living_cove_result.txt"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
TEX = "/Game/Tideborn/Art/Textures"
MAT = "/Game/Tideborn/Art/Materials"
MESH = "/Game/Tideborn/Art/Meshes"
OLD = "/Game/Tideborn/Meshes"

lines = []
counts = {"destroyed": 0, "planes": 0, "props": 0, "moved": 0, "mats": 0, "tex_fixed": 0, "mat_apply": 0}


def log(m):
    t = str(m)
    unreal.log("[LivingCove] " + t)
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


def load(path):
    if path and unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    return None


def destroy(a, why):
    try:
        lab = label(a)
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
        counts["destroyed"] += 1
        log("destroy %s (%s)" % (lab, why))
    except Exception as e:
        log("destroy fail %s" % e)


def clear_world():
    for a in actors():
        lab = label(a)
        cn = cname(a)
        if lab.startswith("TidebornEnv_") or lab.startswith("TidebornShore_"):
            destroy(a, "env")
            continue
        if lab.startswith("SM_") or "Floor" in lab or lab in ("Floor",):
            destroy(a, "greybox")
            continue
        if "TextRender" in cn or (lab.startswith("Text") and "Tideborn" not in lab):
            destroy(a, "text")
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
            if any(x in mn for x in ("cube", "cylinder", "ramp", "plane", "floor", "shape", "1m")):
                destroy(a, "template " + mesh_name)


def fix_normal_textures():
    """Mark all *nor* / *Normal* textures as normal maps so PBR mats compile."""
    if not unreal.EditorAssetLibrary.does_directory_exist(TEX):
        log("no tex dir")
        return
    for ap in unreal.EditorAssetLibrary.list_assets(TEX, recursive=True):
        low = ap.lower()
        if not any(k in low for k in ("nor_gl", "normalgl", "normal", "_nor")):
            continue
        if "rough" in low or "ao" in low or "diffuse" in low or "color" in low:
            continue
        tex = load(ap)
        if not isinstance(tex, unreal.Texture2D):
            continue
        try:
            tex.set_editor_property("srgb", False)
            tex.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP
            )
            try:
                tex.set_editor_property(
                    "lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLDNORMALMAP
                )
            except Exception:
                pass
            unreal.EditorAssetLibrary.save_asset(ap)
            counts["tex_fixed"] += 1
            log("normalmap " + ap)
        except Exception as e:
            log("tex fix fail %s: %s" % (ap, e))
    log("tex_fixed=%d" % counts["tex_fixed"])


def find_tex(folder_suffix, keys):
    base = TEX + "/" + folder_suffix
    if not unreal.EditorAssetLibrary.does_directory_exist(base):
        return None
    for ap in unreal.EditorAssetLibrary.list_assets(base, recursive=False):
        name = ap.split(".")[-1].lower()
        for k in keys:
            if k.lower() in name:
                return ap
    return None


def make_pbr(name, folder, tile=1.0, water=False):
    """Rebuild a lit PBR material with optional UV tiling."""
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)

    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not mat:
        log("FAIL mat " + name)
        return None

    mel = unreal.MaterialEditingLibrary
    if water:
        try:
            mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
            mat.set_editor_property("two_sided", True)
        except Exception:
            pass
        # Simple water: blue base + opacity + low roughness
        col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
        col.set_editor_property("constant", unreal.LinearColor(0.05, 0.22, 0.38, 1.0))
        mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
        op = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 120)
        op.set_editor_property("r", 0.55)
        mel.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
        rg = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 200)
        rg.set_editor_property("r", 0.05)
        mel.connect_material_property(rg, "", unreal.MaterialProperty.MP_ROUGHNESS)
        mel.recompile_material(mat)
        unreal.EditorAssetLibrary.save_asset(path)
        counts["mats"] += 1
        log("water mat " + name)
        return mat

    bc_p = find_tex(folder, ["Diffuse", "Color", "albedo", "BaseColor", "_col"])
    nrm_p = find_tex(folder, ["nor_gl", "NormalGL", "Normal", "nor"])
    rough_p = find_tex(folder, ["Rough", "roughness"])
    bc = load(bc_p) if bc_p else None
    nrm = load(nrm_p) if nrm_p else None
    rough = load(rough_p) if rough_p else None
    log("%s bc=%s nrm=%s rough=%s" % (name, bool(bc), bool(nrm), bool(rough)))

    # UV tiling
    uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -700, 0)
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -550, 0)
    sc = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -700, 80)
    sc.set_editor_property("r", float(tile))
    mel.connect_material_expressions(uv, "", mul, "A")
    mel.connect_material_expressions(sc, "", mul, "B")

    if bc:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, -120)
        ts.set_editor_property("texture", bc)
        mel.connect_material_expressions(mul, "", ts, "UVs")
        mel.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    else:
        col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, -120)
        col.set_editor_property("constant", unreal.LinearColor(0.55, 0.45, 0.3, 1.0))
        mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)

    if nrm:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, 40)
        ts.set_editor_property("texture", nrm)
        try:
            ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        except Exception:
            try:
                ts.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
            except Exception:
                pass
        mel.connect_material_expressions(mul, "", ts, "UVs")
        mel.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_NORMAL)

    if rough:
        ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -350, 200)
        ts.set_editor_property("texture", rough)
        try:
            ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        except Exception:
            pass
        mel.connect_material_expressions(mul, "", ts, "UVs")
        mel.connect_material_property(ts, "R", unreal.MaterialProperty.MP_ROUGHNESS)

    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    counts["mats"] += 1
    log("pbr " + name)
    return mat


def make_creature_mat(name, rgb):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not mat:
        return None
    mel = unreal.MaterialEditingLibrary
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
    col.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 100)
    r.set_editor_property("r", 0.65)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    counts["mats"] += 1
    return mat


def apply_all_slots(actor, mat):
    n = 0
    if not mat:
        return 0
    classes = [unreal.StaticMeshComponent]
    try:
        classes.append(unreal.SkeletalMeshComponent)
    except Exception:
        pass
    for cls in classes:
        try:
            comps = actor.get_components_by_class(cls)
        except Exception:
            continue
        for comp in comps:
            for i in range(8):
                try:
                    comp.set_material(i, mat)
                    n += 1
                except Exception:
                    break
    return n


def find_mesh(keys, skip=("coast_land",)):
    for d in (MESH, OLD):
        if not unreal.EditorAssetLibrary.does_directory_exist(d):
            continue
        for ap in unreal.EditorAssetLibrary.list_assets(d, recursive=True):
            low = ap.lower()
            if any(s in low for s in skip):
                continue
            if any(k.lower() in low for k in keys):
                asset = load(ap)
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


def spawn_sm(mesh, loc, yaw, scale, lab, mat=None):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = sub.spawn_actor_from_object(mesh, loc, unreal.Rotator(pitch=0.0, yaw=float(yaw), roll=0.0))
    if not a:
        return None
    a.set_actor_scale3d(scale)
    a.set_actor_label(lab)
    if mat:
        apply_all_slots(a, mat)
    return a


def spawn_plane(loc, scale_xy, mat, lab):
    plane = load("/Engine/BasicShapes/Plane")
    if not plane:
        return None
    return spawn_sm(
        plane,
        loc,
        0.0,
        unreal.Vector(scale_xy[0], scale_xy[1], 1.0),
        lab,
        mat,
    )


def build_layout(ox, oy, oz, sand, ground, water, rock, bark):
    # Large ground behind beach
    if spawn_plane(unreal.Vector(ox + 500, oy + 1200, oz - 3), (100, 100), ground, "TidebornEnv_Ground"):
        counts["planes"] += 1
    # Beach sand strips (toward ocean = -Y)
    for i, (dx, dy, sx, sy, dz) in enumerate((
        (0, -100, 70, 40, -1),
        (800, -180, 50, 35, -1),
        (-600, -150, 45, 32, -1),
        (200, 350, 45, 40, -1),
        (500, -600, 60, 25, -1),
    )):
        if spawn_plane(unreal.Vector(ox + dx, oy + dy, oz + dz), (sx, sy), sand, "TidebornEnv_Sand_%d" % i):
            counts["planes"] += 1
    # Ocean further out / lower
    if spawn_plane(unreal.Vector(ox + 200, oy - 2400, oz - 45), (150, 100), water, "TidebornEnv_Ocean"):
        counts["planes"] += 1
    # Shallow water near shore
    if spawn_plane(unreal.Vector(ox + 200, oy - 1100, oz - 20), (90, 35), water, "TidebornEnv_Shallows"):
        counts["planes"] += 1

    boulder, _ = find_mesh(["boulder_01"])
    stump, _ = find_mesh(["dead_tree_trunk"])
    stone, _ = find_mesh(["SM_StoneCluster", "StoneCluster"])
    rng = random.Random(21)
    usable = []
    for mesh, mat, name in ((boulder, rock, "Boulder"), (stump, bark, "Trunk"), (stone, rock, "Stone")):
        if mesh:
            r = bounds_r(mesh)
            if r < 2500:
                usable.append((mesh, mat, name, r))
                log("%s r=%.1f" % (name, r))
    if not usable:
        log("ERROR no props")
        return

    spots = []
    # Shore arc — generous spacing
    for i in range(16):
        t = i / 15.0
        spots.append((ox - 500 + t * 2000 + rng.uniform(-60, 60),
                      oy - 550 + math.sin(t * math.pi) * 150 + rng.uniform(-40, 40),
                      oz, "shore"))
    # Inland path toward gate
    for i in range(10):
        t = i / 9.0
        spots.append((ox + 250 + t * 1100 + rng.uniform(-80, 80),
                      oy + 250 + t * 900 + rng.uniform(-60, 60),
                      oz, "path"))

    for i, (x, y, z, zone) in enumerate(spots):
        mesh, mat, name, radius = usable[i % len(usable)]
        target = rng.uniform(220, 480)
        sc = max(0.25, min(target / max(radius, 1.0), 2.6))
        a = spawn_sm(
            mesh,
            unreal.Vector(x, y, z),
            rng.uniform(0, 360),
            unreal.Vector(sc, sc, sc * rng.uniform(0.9, 1.05)),
            "TidebornEnv_%s_%02d" % (name, i),
            mat,
        )
        if a:
            counts["props"] += 1
    log("planes=%d props=%d" % (counts["planes"], counts["props"]))


def relocate_gameplay(ox, oy, oz, mats):
    rock, bark, creature, gate_mat, wood = mats
    for a in actors():
        lab = label(a)
        cn = cname(a)
        if "PlayerStart" in cn or lab == "PlayerStart":
            a.set_actor_location(unreal.Vector(ox + 180, oy + 80, oz + 95), False, True)
            a.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=-90.0, roll=0.0), False)
            counts["moved"] += 1
        if "Gather" in lab and "Stone" in lab:
            a.set_actor_location(unreal.Vector(ox + 380, oy + 220, oz + 35), False, True)
            apply_all_slots(a, rock)
            counts["moved"] += 1
        if "Kelp" in lab:
            a.set_actor_location(unreal.Vector(ox - 120, oy - 380, oz + 40), False, True)
            apply_all_slots(a, creature)
            counts["moved"] += 1
        if "Burr" in lab or "Hound" in lab:
            a.set_actor_location(unreal.Vector(ox + 820, oy + 520, oz + 55), False, True)
            apply_all_slots(a, creature)
            counts["moved"] += 1
        if "ShoreGate" in lab or ("Gate" in lab and "Tideborn" in lab):
            a.set_actor_location(unreal.Vector(ox + 1250, oy + 1050, oz + 90), False, True)
            apply_all_slots(a, gate_mat)
            counts["moved"] += 1
        if "Beacon" in lab or "Landmark" in lab or "PathPost" in lab:
            apply_all_slots(a, wood)

    woods = [a for a in actors() if "Gather" in label(a) and "Wood" in label(a)]
    for i, a in enumerate(woods):
        a.set_actor_location(unreal.Vector(ox + 520 + i * 150, oy + 140, oz + 35), False, True)
        apply_all_slots(a, bark)
        counts["moved"] += 1

    beacons = [a for a in actors() if "Beacon" in label(a) or "Landmark" in label(a)]
    for i, a in enumerate(beacons[:4]):
        t = (i + 1) / 5.0
        a.set_actor_location(unreal.Vector(ox + 200 + t * 1000, oy + 50 + t * 950, oz + 40), False, True)
        counts["moved"] += 1
    log("moved=%d" % counts["moved"])


def reapply_env_mats(sand, ground, water, rock, bark):
    n = 0
    for a in actors():
        lab = label(a)
        if lab.startswith("TidebornEnv_Sand"):
            n += apply_all_slots(a, sand)
        elif lab.startswith("TidebornEnv_Ground"):
            n += apply_all_slots(a, ground)
        elif "Ocean" in lab or "Shallows" in lab:
            n += apply_all_slots(a, water)
        elif "Trunk" in lab:
            n += apply_all_slots(a, bark)
        elif lab.startswith("TidebornEnv_"):
            n += apply_all_slots(a, rock)
    counts["mat_apply"] = n
    log("mat_apply=%d" % n)


def lights():
    for a in actors():
        cn = cname(a)
        if "DirectionalLight" in cn:
            try:
                a.set_editor_property("intensity", 7.5)
                a.set_editor_property("light_color", unreal.LinearColor(1.0, 0.84, 0.62, 1.0))
                a.set_actor_rotation(unreal.Rotator(pitch=-28.0, yaw=48.0, roll=0.0), False)
            except Exception:
                pass
        if "SkyLight" in cn:
            try:
                a.set_editor_property("intensity", 1.3)
                a.set_editor_property("real_time_capture", True)
            except Exception:
                pass
        if "ExponentialHeightFog" in cn:
            try:
                a.set_editor_property("fog_density", 0.018)
            except Exception:
                pass
    log("lights")


def capture(ox, oy, oz):
    for cmd in (
        "ShowFlag.ModeWidgets 0",
        "ShowFlag.Selection 0",
        "ShowFlag.SelectionOutline 0",
        "ShowFlag.Bounds 0",
        "ShowFlag.Collision 0",
        "ShowFlag.Navigation 0",
        "ShowFlag.LightRadius 0",
        "ShowFlag.BSP 0",
    ):
        try:
            unreal.SystemLibrary.execute_console_command(None, cmd)
        except Exception:
            pass

    shots = (
        ("TidebornCoveVerify", unreal.Vector(ox + 180, oy + 40, oz + 170),
         unreal.Rotator(pitch=-5.0, yaw=-90.0, roll=0.0)),
        ("TidebornCoveOverview", unreal.Vector(ox + 200, oy + 1600, oz + 850),
         unreal.Rotator(pitch=-28.0, yaw=-90.0, roll=0.0)),
        ("TidebornCoveSide", unreal.Vector(ox - 900, oy - 200, oz + 280),
         unreal.Rotator(pitch=-8.0, yaw=20.0, roll=0.0)),
    )
    for name, loc, rot in shots:
        try:
            unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
        except Exception as e:
            log("cam fail " + str(e))
        try:
            unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, name)
            log("shot " + name)
        except Exception as e:
            log("shot fail %s %s" % (name, e))


def main():
    try:
        unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    except Exception as e:
        log("load " + str(e))

    ox, oy, oz = 1000.0, 1000.0, 100.0
    log("origin %.0f %.0f %.0f" % (ox, oy, oz))

    clear_world()
    fix_normal_textures()

    sand = make_pbr("M_Tideborn_Sand", "Sand", tile=12.0)
    ground = make_pbr("M_Tideborn_Ground", "Ground", tile=8.0)
    rock = make_pbr("M_Tideborn_RockBoulder", "RockBoulder", tile=2.0)
    rock2 = make_pbr("M_Tideborn_RockACG", "RockACG", tile=2.0)
    bark = make_pbr("M_Tideborn_Bark", "Bark", tile=1.5)
    water = make_pbr("M_Tideborn_WaterSimple", "Sand", water=True)
    creature = make_creature_mat("M_Tideborn_CreatureSolid", (0.22, 0.42, 0.28))
    gate_mat = make_creature_mat("M_Tideborn_GateSolid", (0.4, 0.3, 0.18))
    wood = make_pbr("M_Tideborn_Wood", "Wood", tile=2.0) or bark
    if not rock:
        rock = rock2

    build_layout(ox, oy, oz, sand, ground, water, rock, bark)
    lights()
    relocate_gameplay(ox, oy, oz, (rock, bark, creature, gate_mat, wood))
    reapply_env_mats(sand, ground, water, rock, bark)
    capture(ox, oy, oz)

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    except Exception:
        try:
            unreal.EditorLevelLibrary.save_current_level()
        except Exception as e:
            log("save " + str(e))
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass

    lines.append("--- counts ---")
    for k, v in counts.items():
        lines.append("%s=%s" % (k, v))
    ok = counts["planes"] >= 5 and counts["props"] >= 15 and counts["mats"] >= 5 and counts["tex_fixed"] >= 1
    lines.append("SCRIPT_OK=%s" % ok)
    lines.append("DONE")
    RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log("DONE SCRIPT_OK=%s" % ok)


if __name__ == "__main__":
    main()
