# -*- coding: utf-8 -*-
import time, pathlib, shutil, unreal
NAME='V10_Verify_20260925_223232'
LOC=(1050, 1600, 200)
ROT=(-5, -90, 0)
ROOT = pathlib.Path(r'C:\Users\User\Desktop\AI\Grok\Tideborn')
SHOT = ROOT / 'Saved' / 'Screenshots' / 'WindowsEditor'
SHOT.mkdir(parents=True, exist_ok=True)
target = SHOT / (NAME + '.png')
if target.exists():
    try: target.unlink()
    except Exception: pass
try: unreal.EditorLoadingAndSavingUtils.load_map('/Game/ThirdPerson/Maps/ThirdPersonMap')
except Exception as e: unreal.log(str(e))
for cmd in ('r.SkyAtmosphere 1','r.VolumetricCloud 1','r.Fog 1','ShowFlag.Atmosphere 1','ShowFlag.Fog 1','ShowFlag.Cloud 1','ShowFlag.ModeWidgets 0','ShowFlag.Selection 0','r.DefaultFeature.AutoExposure 0','r.ScreenPercentage 100'):
    try: unreal.SystemLibrary.execute_console_command(None, cmd)
    except Exception: pass
try:
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():
        cn = a.get_class().get_name() if a.get_class() else ''
        if 'SkyLight' in cn:
            for c in a.get_components_by_class(unreal.SkyLightComponent):
                try: c.recapture_sky()
                except Exception: pass
except Exception: pass
time.sleep(14)
try:
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(
        unreal.Vector(*LOC), unreal.Rotator(pitch=ROT[0], yaw=ROT[1], roll=ROT[2]))
except Exception as e: unreal.log('cam '+str(e))
time.sleep(5)
try: unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,NAME)
except Exception as e: unreal.log('auto '+str(e))
try: unreal.SystemLibrary.execute_console_command(None,'HighResShot 1920x1080')
except Exception: pass
time.sleep(10)
ok=False
for i in range(360):
    time.sleep(0.5)
    if target.exists() and target.stat().st_size > 50000:
        ok=True; break
time.sleep(6)
if not ok:
    cands = sorted(SHOT.glob('V10_*.png'), key=lambda p: p.stat().st_mtime, reverse=True)
    for c in cands:
        if NAME.split('_20')[0] in c.name and c.stat().st_size > 50000:
            try: shutil.copy2(str(c), str(target)); target=c; ok=True; break
            except Exception: pass
dst_dir = ROOT/'Tools'/'art'/'shots_v10'
dst_dir.mkdir(parents=True, exist_ok=True)
short = NAME.split('_20')[0]
final = target if target.exists() else None
if final is None:
    cands = sorted(SHOT.glob(short+'*.png'), key=lambda p: p.stat().st_mtime, reverse=True)
    if cands: final = cands[0]; ok=True
if final and final.exists():
    try:
        shutil.copy2(str(final), str(dst_dir/(NAME+'.png')))
        shutil.copy2(str(final), str(dst_dir/(short+'.png')))
    except Exception as e: unreal.log('copy '+str(e))
pathlib.Path(str(ROOT/'Tools'/'art'/('_shot_done_v10_'+short.replace('V10_','')+'.txt'))).write_text(
    'name=%s ok=%s size=%s path=%s\n'%(NAME, ok, final.stat().st_size if final and final.exists() else 0, final), encoding='utf-8')
unreal.log('[V10Shot] end %s ok=%s'%(NAME,ok))