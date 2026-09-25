# -*- coding: utf-8 -*-
"""Cove living v4b — fix blown exposure; keep warm sand/cyan kill/waterline."""
from __future__ import annotations
import pathlib, unreal

ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v4b_result.txt"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
MAT = "/Game/Tideborn/Art/Materials"
lines = []

def log(m):
    t = str(m); unreal.log("[LivingV4b] " + t); lines.append(t)

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

def apply(a, mat):
    if not mat or not a: return
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        for i in range(8):
            try: comp.set_material(i, mat)
            except Exception: break

try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e:
    log("load " + str(e))

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Kill fill light that blew the shot
for a in list(actors()):
    lab = label(a)
    if lab == "TidebornEnv_FillLight" or ("PointLight" in cname(a) and "Tideborn" in lab):
        try:
            eas.destroy_actor(a); log("destroy " + lab)
        except Exception as e:
            log("destroy fail " + str(e))

# Re-apply warm sand (ensure still warm after reload)
sand = load(MAT + "/MI_Tideborn_SandWarm") or load(MAT + "/M_Tideborn_Sand")
for a in actors():
    lab = label(a)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_SandRamp") or "SandRamp" in lab:
        apply(a, sand); log("reapply sand -> " + lab)

for a in actors():
    cn = cname(a)
    if "DirectionalLight" in cn:
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 1.4)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.90, 0.72, 1.0))
            except Exception: pass
            try: c.set_editor_property("indirect_lighting_intensity", 1.6)
            except Exception: pass
            try: c.set_editor_property("shadow_amount", 0.45)
            except Exception: pass
            try: c.set_editor_property("dynamic_shadow_distance_movable_light", 20000.0)
            except Exception: pass
        a.set_actor_rotation(unreal.Rotator(pitch=-42, yaw=35, roll=0), False)
        log("DirectionalLight 1.4 warm")
    if "SkyLight" in cn:
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("intensity", 2.8)
            except Exception: pass
            try: c.set_editor_property("real_time_capture", True)
            except Exception: pass
            try: c.set_editor_property("lower_hemisphere_is_black", False)
            except Exception: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.96, 0.90, 1.0))
            except Exception: pass
        log("SkyLight 2.8")
    if "ExponentialHeightFog" in cn:
        for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
            try: c.set_editor_property("fog_density", 0.12)
            except Exception: pass
            try: c.set_editor_property("fog_inscattering_color", unreal.LinearColor(0.68, 0.66, 0.60, 1.0))
            except Exception: pass
            try: c.set_editor_property("fog_max_opacity", 0.55)
            except Exception: pass
        log("Fog density~0.12 warm-grey")
    if "PostProcess" in cn or label(a) == "TidebornEnv_PostProcess":
        try:
            try: a.set_editor_property("unbound", True)
            except Exception:
                try: a.set_editor_property("b_unbound", True)
                except Exception: pass
            s = a.get_editor_property("settings")
            try:
                s.set_editor_property("override_white_temp", True)
                s.set_editor_property("white_temp", 5200.0)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_bias", True)
                s.set_editor_property("auto_exposure_bias", 0.15)
                s.set_editor_property("override_auto_exposure_min_brightness", True)
                s.set_editor_property("auto_exposure_min_brightness", 0.5)
                s.set_editor_property("override_auto_exposure_max_brightness", True)
                s.set_editor_property("auto_exposure_max_brightness", 1.2)
            except Exception as e:
                log("exp warn " + str(e))
            try:
                s.set_editor_property("override_bloom_intensity", True)
                s.set_editor_property("bloom_intensity", 0.15)
            except Exception: pass
            try:
                s.set_editor_property("override_auto_exposure_method", True)
                # AEM_Manual = 2 often; try histogram with tight range
            except Exception: pass
            try: a.set_editor_property("settings", s)
            except Exception: pass
            log("PP bias~0.15 white_temp~5200 bloom low")
        except Exception as e:
            log("PP fail " + str(e))

# Weak ambient fill via low-intensity skylight already; optional tiny directional only
# Soften any remaining PointLights near cove
for a in actors():
    if "PointLight" in cname(a):
        for c in a.get_components_by_class(unreal.PointLightComponent):
            try:
                intens = c.get_editor_property("intensity")
                if intens and intens > 500:
                    c.set_editor_property("intensity", 350.0)
                    c.set_editor_property("light_color", unreal.LinearColor(1.0, 0.85, 0.65, 1.0))
                    c.set_editor_property("cast_shadows", False)
                    log("muted PointLight " + label(a))
            except Exception:
                pass

# CONFIRM locks
for a in actors():
    lab = label(a)
    if lab in ("TidebornEnv_SandBase", "TidebornEnv_Shallows", "TidebornEnv_Ocean", "TidebornEnv_SandRamp"):
        loc = a.get_actor_location(); sc = a.get_actor_scale3d()
        hy = 50.0 * sc.y
        mats = []
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            for i in range(2):
                try:
                    m = comp.get_material(i)
                    if m: mats.append(m.get_name())
                except Exception: break
            break
        log("CONFIRM %s Z=%.0f Y[%.0f..%.0f] sc=(%.1f,%.1f,%.1f) mats=%s" % (
            lab, loc.z, loc.y-hy, loc.y+hy, sc.x, sc.y, sc.z, ",".join(mats) or "-"))

try:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("save_current_level -> True")
except Exception as e:
    log("save: %s" % e)
try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("save_dirty -> True")
except Exception as e:
    log("save_dirty: %s" % e)

log("DONE")
RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
