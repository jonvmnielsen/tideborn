# -*- coding: utf-8 -*-
import time, pathlib, unreal
cfg = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\_shot_cfg_active.txt")
raw = cfg.read_text(encoding="utf-8-sig").strip().split("|")
name, loc_s, rot_s = raw[0].strip(), raw[1].strip(), raw[2].strip()
loc = [float(x) for x in loc_s.split(",")]
rot = [float(x) for x in rot_s.split(",")]
SHOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\Screenshots\WindowsEditor")
SHOT.mkdir(parents=True, exist_ok=True)
target = SHOT / (name + ".png")
if target.exists():
    try: target.unlink()
    except Exception: pass
auto = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\AutoScreenshot.png")
try:
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e:
    unreal.log("load "+str(e))
for cmd in ("ShowFlag.ModeWidgets 0","ShowFlag.Selection 0","ShowFlag.SelectionOutline 0","ShowFlag.Bounds 0","ShowFlag.Collision 0","ShowFlag.LightRadius 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
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
for i in range(90):
    time.sleep(0.5)
    if target.exists() and target.stat().st_size > 20000:
        ok = True
        break
    if auto.exists() and auto.stat().st_size > 20000:
        try:
            import shutil
            shutil.copy2(str(auto), str(target))
            ok = True
            break
        except Exception as e:
            unreal.log("copy auto "+str(e))
    try:
        unreal.SystemLibrary.execute_console_command(None, "r.ScreenPercentage 100")
    except Exception:
        pass
# final grace: screenshot may flush after loop
time.sleep(2.0)
if not ok and target.exists() and target.stat().st_size > 20000:
    ok = True
if not ok and auto.exists() and auto.stat().st_size > 20000:
    try:
        import shutil
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
unreal.log("[Shot] end ok=%s" % ok)

