# -*- coding: utf-8 -*-
"""v9b: reposition BeachSlope so lip reads at shore; keep sand out of mid-ocean."""
from __future__ import annotations
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cove_living_v9b_result.txt"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
lines=[]
def log(m):
    t=str(m); unreal.log("[V9b] "+t); lines.append(t)
def actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
def label(a):
    try: return a.get_actor_label() or ""
    except: return ""
def cname(a):
    try: return a.get_class().get_name() or ""
    except: return ""
def unhide(a):
    try:
        a.set_actor_hidden_in_game(False); a.set_is_temporarily_hidden_in_editor(False)
        root=a.root_component
        if root:
            try: root.set_visibility(True,True)
            except: pass
    except: pass

try: unreal.EditorLoadingAndSavingUtils.load_map(MAP)
except Exception as e: log(str(e))

for a in actors():
    lab=label(a); cn=cname(a)
    if lab=="TidebornEnv_BeachSlope":
        # Mesh: land +Y (Z~0 local), water -Y (Z~-240). halfY=600.
        # Put LAND end at Y=760 so above-water band covers shore (~510..760).
        half_y = 600.0
        land_y = 760.0
        center_y = land_y - half_y  # 160
        place_z = 118.0  # land ~118; above water until ~Y 520
        a.set_actor_location(unreal.Vector(1000.0, center_y, place_z), False, True)
        a.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.15))  # exaggerate drop a bit
        a.set_actor_rotation(unreal.Rotator(0, 0, 0), False)
        unhide(a)
        log("BeachSlope landY=760 centerY=%.0f Z=118 scZ=1.15 -> waterEndY=%.0f" % (center_y, center_y-half_y))
    if lab=="TidebornEnv_SandBase":
        a.set_actor_location(unreal.Vector(1000,1500,106),False,True)
        a.set_actor_scale3d(unreal.Vector(45,18,1)); log("LOCK SandBase")
    if "SkyAtmosphere" in cn or "VolumetricCloud" in cn or "ExponentialHeightFog" in cn:
        unhide(a)
    if "SkyLight" in cn:
        unhide(a)
        for c in a.get_components_by_class(unreal.SkyLightComponent):
            try: c.set_editor_property("intensity", 0.28)
            except: pass
            try: c.recapture_sky()
            except: pass
    if "DirectionalLight" in cn:
        # Stronger side light for slope lip
        a.set_actor_rotation(unreal.Rotator(pitch=-22.0, yaw=-40.0, roll=0.0), False)
        for c in a.get_components_by_class(unreal.DirectionalLightComponent):
            try: c.set_editor_property("intensity", 3.6)
            except: pass
            try: c.set_editor_property("light_color", unreal.LinearColor(1.0,0.78,0.52,1.0))
            except: pass
        log("DirLight side yaw=-40")
    if lab=="TidebornEnv_SkyDome":
        unhide(a)

for cmd in ("r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1","ShowFlag.Atmosphere 1","ShowFlag.Fog 1"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except: pass

# dump slope + sand Y
for a in actors():
    lab=label(a)
    if lab in ("TidebornEnv_BeachSlope","TidebornEnv_SandBase","TidebornEnv_Ocean","TidebornEnv_Shallows","TidebornEnv_FoamSeg_00","TidebornEnv_WetSand_00"):
        loc=a.get_actor_location(); sc=a.get_actor_scale3d()
        try:
            origin, extent = a.get_actor_bounds(False, False)
            log("%s loc=(%.0f,%.0f,%.1f) scZ=%.2f boundsY=[%.0f..%.0f] boundsZ=[%.1f..%.1f]" % (
                lab, loc.x, loc.y, loc.z, sc.z,
                origin.y-extent.y, origin.y+extent.y, origin.z-extent.z, origin.z+extent.z))
        except Exception as e:
            log("%s loc=(%.0f,%.0f,%.1f) bounds_fail %s" % (lab, loc.x, loc.y, loc.z, e))

try: log("save %s"%unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except Exception as e: log(str(e))
try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
except: pass
log("DONE"); RESULT.write_text("\n".join(lines)+"\n",encoding="utf-8")
