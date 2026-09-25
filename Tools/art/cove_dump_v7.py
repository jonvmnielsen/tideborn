# -*- coding: utf-8 -*-
"""v7 dump: PostProcess + SkyLight + DirectionalLight + Fog + key mats/actors."""
from __future__ import annotations
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
OUT = ROOT / "Tools" / "art" / "cove_dump_v7.txt"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines = []
def log(m):
    t = str(m); unreal.log("[DumpV7] " + t); lines.append(t)
def label(a):
    try: return a.get_actor_label() or ""
    except Exception: return ""
def cname(a):
    try: return a.get_class().get_name() or ""
    except Exception: return ""
def safe_get(obj, prop):
    try: return obj.get_editor_property(prop)
    except Exception: return "<err>"
try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log("load " + str(e))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = list(eas.get_all_level_actors())

log("=== PostProcessVolume ===")
for a in actors:
    cn = cname(a); lab = label(a)
    if "PostProcess" not in cn and lab != "TidebornEnv_PostProcess":
        continue
    log("actor lab=%s class=%s unbound=%s" % (lab, cn, safe_get(a, "unbound")))
    try:
        s = a.get_editor_property("settings")
    except Exception as e:
        log("  settings err " + str(e)); continue
    for p in ("white_temp","white_tint","color_saturation","color_contrast","color_gamma",
              "color_gain","color_offset","color_saturation_shadows","color_gain_shadows",
              "color_saturation_midtones","color_gain_midtones","color_saturation_highlights",
              "color_gain_highlights","auto_exposure_bias","auto_exposure_method",
              "override_white_temp","override_color_gain","override_color_saturation",
              "override_auto_exposure_bias","override_auto_exposure_method",
              "color_grading_lut","override_color_grading_lut","color_grading_intensity",
              "override_color_grading_intensity","look_up_table","scene_color_tint",
              "override_scene_color_tint"):
        log("  %s = %s" % (p, safe_get(s, p)))

log("")
log("=== SkyLight ===")
for a in actors:
    if "SkyLight" not in cname(a):
        continue
    log("actor lab=%s class=%s" % (label(a), cname(a)))
    for c in a.get_components_by_class(unreal.SkyLightComponent):
        for p in ("intensity","light_color","source_type","cubemap","source_cubemap_angle",
                  "real_time_capture","indirect_lighting_intensity","occlusion_max_distance",
                  "lower_hemisphere_is_black","lower_hemisphere_color"):
            v = safe_get(c, p)
            if p == "cubemap" and v is not None and v != "<err>":
                try: v = v.get_path_name()
                except Exception: pass
            log("  %s = %s" % (p, v))

log("")
log("=== DirectionalLight ===")
for a in actors:
    if "DirectionalLight" not in cname(a):
        continue
    rot = a.get_actor_rotation()
    log("actor lab=%s class=%s rot=(%.1f,%.1f,%.1f)" % (label(a), cname(a), rot.pitch, rot.yaw, rot.roll))
    for c in a.get_components_by_class(unreal.DirectionalLightComponent):
        for p in ("intensity","light_color","indirect_lighting_intensity","atmosphere_sun_light",
                  "cast_shadows","temperature","use_temperature"):
            log("  %s = %s" % (p, safe_get(c, p)))

log("")
log("=== ExponentialHeightFog ===")
for a in actors:
    if "ExponentialHeightFog" not in cname(a) and "HeightFog" not in cname(a):
        continue
    log("actor lab=%s class=%s" % (label(a), cname(a)))
    for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
        for p in ("fog_density","fog_height_falloff","fog_inscattering_color",
                  "directional_inscattering_color","directional_inscattering_exponent",
                  "volumetric_fog","volumetric_fog_albedo","start_distance"):
            log("  %s = %s" % (p, safe_get(c, p)))

log("")
log("=== SkyAtmosphere / VolumetricCloud present ===")
for a in actors:
    cn = cname(a)
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn or "SkyDome" in label(a):
        log("KEEP %s lab=%s hidden=%s" % (cn, label(a), a.is_hidden_ed()))

log("")
log("=== Mouth corridor Boulder/WLB X[800,1200] Y[200,900] ===")
mouth = 0
for a in actors:
    lab = label(a)
    if not (("Boulder" in lab) or lab.startswith("TidebornEnv_WLB_")):
        continue
    loc = a.get_actor_location(); sc = a.get_actor_scale3d()
    if 800 <= loc.x <= 1200 and 200 <= loc.y <= 900:
        log("MOUTH %s loc=(%.0f,%.0f,%.1f) sc=(%.2f,%.2f)" % (lab, loc.x, loc.y, loc.z, sc.x, sc.y))
        mouth += 1
log("mouth_count=%d" % mouth)

log("")
log("=== Key shore actors ===")
for a in actors:
    lab = label(a)
    if not any(k in lab for k in ("SandBase","Ocean","Shallows","WetSand","SandRamp","ShoreEdge","Ground")):
        continue
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
    log("%s loc=(%.0f,%.0f,%.1f) sc=(%.2f,%.2f) Y[%.0f..%.0f] %s" % (
        lab, loc.x, loc.y, loc.z, sc.x, sc.y, loc.y - hy, loc.y + hy, ",".join(mats) or "-"))

OUT.write_text("\n".join(lines) + "\nDONE\n", encoding="utf-8")
log("wrote %s (%d lines)" % (OUT, len(lines)))
