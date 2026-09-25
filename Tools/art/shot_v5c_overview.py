# -*- coding: utf-8 -*-
import time, pathlib, shutil, unreal
NAME = "V5c_Overview"
OUT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\shots_v5c")
OUT.mkdir(parents=True, exist_ok=True)
SHOT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\Screenshots\WindowsEditor")
SHOT.mkdir(parents=True, exist_ok=True)
target = SHOT / (NAME + ".png")
alt = OUT / (NAME + ".png")
for p in (target, alt):
    if p.exists():
        try: p.unlink()
        except Exception: pass
try:
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e:
    unreal.log("load "+str(e))
for cmd in ("r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1",
            "ShowFlag.Atmosphere 1","ShowFlag.Fog 1","ShowFlag.Cloud 1",
            "ShowFlag.ModeWidgets 0","ShowFlag.Selection 0","ShowFlag.SelectionOutline 0",
            "r.DefaultFeature.AutoExposure 0","r.EyeAdaptationQuality 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
time.sleep(10)
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(1100.0, 1800.0, 850.0),
        unreal.Rotator(pitch=-48.0, yaw=-90.0, roll=0.0),
    )
except Exception as e:
    unreal.log("cam "+str(e))
unreal.log("[V5cShot] begin "+NAME)
try: unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, NAME)
except Exception as e: unreal.log("auto "+str(e))
try: unreal.SystemLibrary.execute_console_command(None, "HighResShot 1920x1080")
except Exception as e: unreal.log("hrs "+str(e))
ok=False
for i in range(90):
    time.sleep(0.5)
    if target.exists() and target.stat().st_size>50000:
        ok=True; break
time.sleep(2)
# copy newest large png into OUT under NAME
src=None
if target.exists() and target.stat().st_size>50000:
    src=target
else:
    cands=[]
    for d in (SHOT, pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved")):
        if not d.exists(): continue
        for p in d.rglob("*.png"):
            try:
                if p.stat().st_size>50000: cands.append(p)
            except Exception: pass
    cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    if cands: src=cands[0]
if src:
    try:
        shutil.copy2(str(src), str(alt)); ok=True
        unreal.log("[V5cShot] alt="+str(alt)+" from="+str(src))
    except Exception as e:
        unreal.log("copy "+str(e))
done=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\_shot_done_v5c.txt")
done.write_text("name=%s ok=%s alt=%s\n"%(NAME, ok, alt.stat().st_size if alt.exists() else 0), encoding="utf-8")
unreal.log("[V5cShot] end ok=%s"%ok)