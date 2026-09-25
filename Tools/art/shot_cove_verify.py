# -*- coding: utf-8 -*-
import time, pathlib, shutil, unreal
name = "TidebornCoveVerify"
loc = [1050.0, 1550.0, 200.0]
rot = [-5.0, -90.0, 0.0]
SHOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\Screenshots\WindowsEditor")
SHOT.mkdir(parents=True, exist_ok=True)
target = SHOT / (name + ".png")
if target.exists():
    try: target.unlink()
    except Exception: pass
auto = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\AutoScreenshot.png")
if auto.exists():
    try: auto.unlink()
    except Exception: pass
try:
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e:
    unreal.log("load "+str(e))
for cmd in (
    "r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1",
    "ShowFlag.Atmosphere 1","ShowFlag.Fog 1","ShowFlag.Cloud 1",
    "ShowFlag.ModeWidgets 0","ShowFlag.Selection 0","ShowFlag.SelectionOutline 0",
    "ShowFlag.Bounds 0","ShowFlag.Collision 0","ShowFlag.LightRadius 0",
    "r.ScreenPercentage 100","r.DefaultFeature.AutoExposure 0","r.EyeAdaptationQuality 0",
):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
time.sleep(12)
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(loc[0], loc[1], loc[2]),
        unreal.Rotator(pitch=rot[0], yaw=rot[1], roll=rot[2]),
    )
except Exception as e:
    unreal.log("cam "+str(e))
unreal.log("[Shot] begin "+name)
try:
    unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, name)
except Exception as e:
    unreal.log("auto fail "+str(e))
try:
    unreal.SystemLibrary.execute_console_command(None, "HighResShot 1920x1080")
except Exception as e:
    unreal.log("hrs fail "+str(e))
ok = False
for i in range(140):
    time.sleep(0.5)
    if target.exists() and target.stat().st_size > 20000:
        ok = True
        break
    if auto.exists() and auto.stat().st_size > 20000:
        try:
            shutil.copy2(str(auto), str(target))
            ok = True
            break
        except Exception as e:
            unreal.log("copy auto "+str(e))
time.sleep(4.0)
if (not ok) and auto.exists() and auto.stat().st_size > 20000:
    try:
        shutil.copy2(str(auto), str(target))
        ok = True
    except Exception:
        pass
done = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\_shot_done.txt")
done.write_text("name=%s ok=%s target=%s auto=%s\n" % (
    name, ok,
    target.stat().st_size if target.exists() else 0,
    auto.stat().st_size if auto.exists() else 0,
), encoding="utf-8")
unreal.log("[Shot] end ok=%s size=%s" % (ok, target.stat().st_size if target.exists() else 0))