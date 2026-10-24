# -*- coding: utf-8 -*-
import time, pathlib, shutil, unreal
NAME="V6_Overview_20260925_193157"
BASE="V6_Overview"
LOC=(1000, 1800, 550)
ROT=(-50.0, -90.0, 0)
OUT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\shots_v6")
OUT.mkdir(parents=True, exist_ok=True)
SHOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\Screenshots")
# CLEAR all prior screenshots so newest is unambiguous
if SHOT.exists():
    for p in list(SHOT.rglob("*.png")):
        try: p.unlink()
        except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: unreal.log(str(e))
for cmd in ("r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1","ShowFlag.Atmosphere 1","ShowFlag.Fog 1","r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
time.sleep(12)
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(*LOC), unreal.Rotator(pitch=ROT[0], yaw=ROT[1], roll=ROT[2]))
except Exception as e: unreal.log("cam "+str(e))
time.sleep(3)
# Both capture paths; folder was cleared so newest wins
try: unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,NAME)
except Exception as e: unreal.log("auto "+str(e))
try: unreal.SystemLibrary.execute_console_command(None,"HighResShot 1920x1080")
except Exception: pass
ok=False; src=None
t0=time.time()
for i in range(100):
    time.sleep(0.5)
    cands=[]
    if SHOT.exists():
        for p in SHOT.rglob("*.png"):
            try:
                if p.stat().st_size>80000: cands.append(p)
            except Exception: pass
    # Prefer exact NAME
    for p in cands:
        if NAME in p.name:
            src=p; break
    if src is None and cands:
        cands.sort(key=lambda p:p.stat().st_mtime, reverse=True)
        src=cands[0]
    if src and src.stat().st_size>80000:
        # ensure file is newer than script start
        if src.stat().st_mtime >= (t0 - 30):
            break
        else:
            src=None
time.sleep(2)
alt=OUT/(NAME+".png")
alt2=OUT/(BASE+".png")
if src:
    try:
        shutil.copy2(str(src), str(alt))
        shutil.copy2(str(src), str(alt2))
        ok=True
        unreal.log("[V6] CLEAR-shot %s -> %s (%d)"%(src.name, alt.name, alt.stat().st_size))
    except Exception as e:
        unreal.log("copy "+str(e))
pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\_shot_done_v6.txt").write_text(
    "name=%s ok=%s size=%s src=%s\n"%(NAME, ok, alt.stat().st_size if alt.exists() else 0, src), encoding="utf-8")
