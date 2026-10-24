# -*- coding: utf-8 -*-
import time, pathlib, shutil, unreal
NAME='V11_Verify_20260925_230401'
LOC=(1050.0, 1600.0, 200.0)
ROT=(-5.0, -90.0, 0.0)
ROOT = pathlib.Path(r'C:\Users\User\Desktop\AI\Grok\Tideborn')
SHOT = ROOT / 'Saved' / 'Screenshots' / 'WindowsEditor'
SHOT.mkdir(parents=True, exist_ok=True)
for p in list(SHOT.glob('V11_Verify*.png')):
    try: p.unlink()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.load_map('/Game/ThirdPerson/Maps/ThirdPersonMap')
except Exception as e: unreal.log(str(e))
for cmd in ('r.SkyAtmosphere 1','r.VolumetricCloud 1','r.Fog 1','ShowFlag.Atmosphere 1','ShowFlag.Fog 1','ShowFlag.Cloud 1','ShowFlag.ModeWidgets 0','ShowFlag.Selection 0','r.DefaultFeature.AutoExposure 0','r.ScreenPercentage 100'):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
try:
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        cn = a.get_class().get_name() if a.get_class() else ''
        if 'SkyLight' in cn:
            for c in a.get_components_by_class(unreal.SkyLightComponent):
                try: c.recapture_sky()
                except Exception: pass
except Exception: pass
time.sleep(12)
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(*LOC), unreal.Rotator(pitch=ROT[0], yaw=ROT[1], roll=ROT[2]))
except Exception as e: unreal.log('cam '+str(e))
time.sleep(6)
try: unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,NAME)
except Exception as e: unreal.log('auto '+str(e))
try: unreal.SystemLibrary.execute_console_command(None,'HighResShot 1920x1080')
except Exception: pass
time.sleep(25)
ok=False; final=None
for i in range(240):
    cands=sorted(SHOT.glob('V11_Verify*.png'), key=lambda p:p.stat().st_mtime, reverse=True)
    for c in cands:
        if c.stat().st_size>50000:
            final=c; ok=True; break
    if ok: break
    time.sleep(0.5)
time.sleep(4)
dst=ROOT/'Tools'/'art'/'shots_v11'; dst.mkdir(parents=True, exist_ok=True)
if final and final.exists():
    shutil.copy2(str(final), str(dst/(NAME+'.png')))
    shutil.copy2(str(final), str(dst/'V11_Verify.png'))
(ROOT/'Tools'/'art'/'_shot_done_v11_Verify.txt').write_text('name=%s ok=%s size=%s path=%s\n'%(NAME,ok, final.stat().st_size if final else 0, final), encoding='utf-8')
unreal.log('[V11Shot] %s ok=%s path=%s'%(NAME,ok,final))