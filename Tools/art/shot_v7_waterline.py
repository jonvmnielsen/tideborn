# -*- coding: utf-8 -*-
import time, pathlib, unreal
NAME="V7_Waterline_20260925_201044"
LOC=(1050, 750, 160)
ROT=(-12.0, -90.0, 0)
try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: unreal.log(str(e))
for cmd in ("r.SkyAtmosphere 1","r.VolumetricCloud 1","r.Fog 1","ShowFlag.Atmosphere 1","ShowFlag.Fog 1","r.DefaultFeature.AutoExposure 0"):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
time.sleep(14)
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(*LOC), unreal.Rotator(pitch=ROT[0], yaw=ROT[1], roll=ROT[2]))
except Exception as e: unreal.log("cam "+str(e))
time.sleep(4)
try: unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,NAME)
except Exception as e: unreal.log("auto "+str(e))
try: unreal.SystemLibrary.execute_console_command(None,"HighResShot 1920x1080")
except Exception: pass
time.sleep(25)
pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\_shot_done_v7.txt").write_text("name=%s requested\n"%NAME, encoding="utf-8")
