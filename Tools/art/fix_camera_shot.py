# -*- coding: utf-8 -*-
import pathlib, unreal
ROOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
RESULT = ROOT / "Tools" / "art" / "cam_verify_result.txt"
lines = []
def log(m):
    unreal.log("[CamFix] "+str(m)); lines.append(str(m))
try:
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e:
    log("load "+str(e))
origin = unreal.Vector(1000, 1000, 100)
cam_loc = unreal.Vector(1150, 1080, 260)
cam_rot = unreal.Rotator(pitch=-8.0, yaw=-90.0, roll=0.0)
log("setting cam %s %s" % (cam_loc, cam_rot))
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(cam_loc, cam_rot)
except Exception as e:
    log("cam1 fail "+str(e))
    try:
        unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(cam_loc, cam_rot)
    except Exception as e2:
        log("cam2 fail "+str(e2))
# second angle: wider cove overview
cam2 = unreal.Vector(1000, 1600, 700)
rot2 = unreal.Rotator(pitch=-25.0, yaw=-90.0, roll=0.0)
shot_dir = ROOT / "Saved" / "Screenshots" / "WindowsEditor"
shot_dir.mkdir(parents=True, exist_ok=True)
for name, loc, rot in (("TidebornCoveVerify", cam_loc, cam_rot), ("TidebornCoveOverview", cam2, rot2)):
    try:
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
    except Exception:
        pass
    try:
        unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, name)
        log("shot "+name)
    except Exception as e:
        log("shot fail "+name+" "+str(e))
RESULT.write_text("\n".join(lines)+"\n", encoding="utf-8")
log("DONE")
