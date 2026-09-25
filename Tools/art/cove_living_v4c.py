# -*- coding: utf-8 -*-
"""Cove living v4c — kill remaining cyan (BurrHound/gate), keep exposure sane, sand warm."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v4c_result.txt"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
MAT = "/Game/Tideborn/Art/Materials"
lines = []

def log(m):
    t = str(m); unreal.log("[LivingV4c] " + t); lines.append(t)

def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())

def label(a):
    try: return a.get_actor_label() or ""
    except Exception: return ""

def cname(a):
    try: return a.get_class().get_name() or ""
    except Exception: return ""

def load(p):
    return unreal.EditorAssetLibrary.load_asset(p) if p and unreal.EditorAssetLibrary.does_asset_exist(p) else None

def make_solid(name, rgb, rough=0.9):
    path = MAT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    # Force opaque / no translucent cyan look
    try:
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    except Exception:
        pass
    try:
        mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception:
        pass
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 0)
    col.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 100)
    r.set_editor_property("r", float(rough))
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    em = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -350, 200)
    em.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
    mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    # zero metallic
    m = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 160)
    m.set_editor_property("r", 0.0)
    mel.connect_material_property(m, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path)
    log("mat %s rgb=(%.2f,%.2f,%.2f)" % (name, rgb[0], rgb[1], rgb[2]))
    return mat

def force_apply(a, mat):
    if not a or not mat: return 0
    n = 0
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        try: comp.modify()
        except Exception: pass
        # kill vertex color influence where possible
        try: comp.set_editor_property("overlay_material", None)
        except Exception: pass
        for i in range(16):
            try:
                comp.set_material(i, mat)
                n += 1
            except Exception:
                break
        try:
            # clear override array then set
            comp.set_editor_property("override_materials", [mat] * 8)
        except Exception:
            pass
    # Also walk child actor components
    try:
        for ch in a.get_components_by_class(unreal.ChildActorComponent):
            child = ch.get_editor_property("child_actor")
            if child:
                n += force_apply(child, mat)
    except Exception:
        pass
    return n

try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e:
    log("load " + str(e))

# Brown wood, olive creature, warm sand — no teal anywhere
sand = make_solid("MI_Tideborn_SandWarm", (0.78, 0.62, 0.40), rough=0.95)
# also rewrite master
sand2 = make_solid("M_Tideborn_Sand", (0.78, 0.62, 0.40), rough=0.95)
wood = make_solid("MI_Tideborn_WoodMuted", (0.36, 0.24, 0.14), rough=0.92)
creature = make_solid("MI_Tideborn_CreatureMuted", (0.42, 0.34, 0.22), rough=0.8)  # brownish, NOT green-cyan
creature2 = make_solid("M_Tideborn_CreatureSolid", (0.40, 0.32, 0.20), rough=0.8)
gate = make_solid("M_Tideborn_GateSolid", (0.32, 0.22, 0.13), rough=0.9)
rock = make_solid("M_Tideborn_RockShore", (0.40, 0.38, 0.34), rough=0.78)

# Dump ALL materials on critical actors before/after
targets = []
for a in actors():
    lab = label(a)
    if any(k in lab for k in ("ShoreGate", "Kelp", "Burr", "Hound", "Gather", "SandBase", "SandRamp", "Beacon", "Landmark", "PathPost")):
        targets.append(a)
    # also any static mesh near gate with cyan-looking default
    if lab.startswith("Tideborn") and ("Gate" in lab or "P2_" in lab):
        if a not in targets:
            targets.append(a)

for a in targets:
    lab = label(a)
    before = []
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        cn = comp.get_class().get_name() if comp.get_class() else "?"
        for i in range(8):
            try:
                m = comp.get_material(i)
                if m: before.append("%s[%d]=%s" % (cn, i, m.get_name()))
            except Exception: break
    log("BEFORE %s | %s" % (lab, ";".join(before) or "-"))

    if "Sand" in lab:
        n = force_apply(a, sand)
    elif "Gate" in lab or "Beacon" in lab or "Landmark" in lab or "PathPost" in lab or "Post" in lab:
        n = force_apply(a, gate)
    elif "Kelp" in lab or "Burr" in lab or "Hound" in lab:
        n = force_apply(a, creature)
    elif "Gather" in lab:
        n = force_apply(a, rock if "Stone" in lab else wood)
    else:
        n = force_apply(a, rock)
    log("force_apply %s slots=%d" % (lab, n))

    after = []
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        cn = comp.get_class().get_name() if comp.get_class() else "?"
        for i in range(8):
            try:
                m = comp.get_material(i)
                if m: after.append("%s[%d]=%s" % (cn, i, m.get_name()))
            except Exception: break
    log("AFTER %s | %s" % (lab, ";".join(after) or "-"))

    # Kill cyan lights on these actors
    for comp in a.get_components_by_class(unreal.LightComponent):
        try:
            col = comp.get_editor_property("light_color")
            # if cyan-ish (G and B high, R low), mute to warm
            try:
                r, g, b = float(col.r), float(col.g), float(col.b)
            except Exception:
                r = g = b = 1.0
            if b > 0.5 and g > 0.4 and r < 0.7:
                comp.set_editor_property("light_color", unreal.LinearColor(1.0, 0.75, 0.45, 1.0))
                log("muted cyan light on " + lab)
            try: comp.set_editor_property("intensity", min(float(comp.get_editor_property("intensity") or 0), 400.0))
            except Exception: pass
        except Exception:
            pass

# Also scan EVERY Tideborn actor for materials with cyan/teal/water/emissive in name (except ocean/shallows)
for a in actors():
    lab = label(a)
    if not lab.startswith("Tideborn"): continue
    if lab in ("TidebornEnv_Ocean", "TidebornEnv_Shallows"): continue
    for comp in a.get_components_by_class(unreal.PrimitiveComponent):
        for i in range(8):
            try:
                m = comp.get_material(i)
                if not m: continue
                mn = (m.get_name() or "").lower()
                if any(k in mn for k in ("cyan", "teal", "emissive", "glow", "neon", "ice", "water", "default", "worldgrid", "basicshape")):
                    if "wateropaque" in mn or "watersimple" in mn: continue
                    replace = sand if "Sand" in lab else (creature if any(x in lab for x in ("Kelp","Burr","Hound")) else rock)
                    if "Gate" in lab: replace = gate
                    comp.set_material(i, replace)
                    log("scrub %s mat[%d] %s -> %s" % (lab, i, mn, replace.get_name() if replace else "?"))
            except Exception:
                break

# Exposure keep sane (reassert)
for a in actors():
    cn = cname(a)
    if "DirectionalLight" in cn:
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 1.5)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.90, 0.72, 1.0))
            except Exception: pass
            try: c.set_editor_property("indirect_lighting_intensity", 1.5)
            except Exception: pass
        log("DirLight keep 1.5")
    if "SkyLight" in cn:
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("intensity", 2.5)
            except Exception: pass
        log("SkyLight keep 2.5")
    if "PostProcess" in cn or label(a) == "TidebornEnv_PostProcess":
        try:
            s = a.get_editor_property("settings")
            s.set_editor_property("override_auto_exposure_bias", True)
            s.set_editor_property("auto_exposure_bias", 0.1)
            s.set_editor_property("override_white_temp", True)
            s.set_editor_property("white_temp", 5000.0)
            s.set_editor_property("override_bloom_intensity", True)
            s.set_editor_property("bloom_intensity", 0.1)
            a.set_editor_property("settings", s)
            log("PP keep bias 0.1 temp 5000")
        except Exception as e:
            log("PP " + str(e))

for a in actors():
    lab = label(a)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_SandRamp", "TidebornEnv_Shallows", "TidebornEnv_Ocean",
               "Tideborn_P2_ShoreGate", "Tideborn_P2_BurrHound", "Tideborn_P2_KelpBack"):
        loc = a.get_actor_location(); sc = a.get_actor_scale3d()
        mats = []
        for comp in a.get_components_by_class(unreal.PrimitiveComponent):
            for i in range(4):
                try:
                    m = comp.get_material(i)
                    if m: mats.append(m.get_name())
                except Exception: break
        log("CONFIRM %s Z=%.0f loc=(%.0f,%.0f) sc=(%.1f,%.1f) mats=%s" % (
            lab, loc.z, loc.x, loc.y, sc.x, sc.y, ",".join(mats[:6]) or "-"))

try:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("save_current_level -> True")
except Exception as e:
    log("save " + str(e))
try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("save_dirty -> True")
except Exception as e:
    log("save_dirty " + str(e))

log("DONE")
RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
