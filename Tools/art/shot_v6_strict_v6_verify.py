# -*- coding: utf-8 -*-
import time, pathlib, shutil, unreal
NAME="V6_Verify_20260925_192647"
BASE="V6_Verify"
LOC=(1050, 1600, 200)
ROT=(-5.0, -90.0, 0)
OUT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\shots_v6")
OUT.mkdir(parents=True, exist_ok=True)
for p in list(OUT.glob(BASE+"*.png")):
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
time.sleep(2)
try: unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,NAME)
except Exception as e: unreal.log(str(e))
SHOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\Screenshots")
ok=False; src=None
t0=time.time()
for i in range(120):
    time.sleep(0.5)
    if not SHOT.exists(): continue
    for p in SHOT.rglob("*.png"):
        try:
            if NAME in p.name and p.stat().st_size>50000:
                src=p; break
        except Exception: pass
    if src: break
time.sleep(3)
alt=OUT/(NAME+".png")
alt2=OUT/(BASE+".png")
if src:
    try:
        shutil.copy2(str(src), str(alt))
        shutil.copy2(str(src), str(alt2))
        ok=True
        unreal.log("[V6] STRICT copied %s -> %s size=%d"%(src,alt,alt.stat().st_size))
    except Exception as e:
        unreal.log("copy "+str(e))
pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\_shot_done_v6.txt").write_text(
    "name=%s ok=%s alt=%s src=%s\n"%(NAME,ok, alt.stat().st_size if alt.exists() else 0, src), encoding="utf-8")
