# -*- coding: utf-8 -*-
"""Dump TidebornEnv actors: label, loc, scale, materials."""
from __future__ import annotations
import pathlib, unreal
ROOT=pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn")
OUT=ROOT/"Tools"/"art"/"cove_dump.txt"
lines=[]
def log(m):
    t=str(m); unreal.log("[Dump] "+t); lines.append(t)
try: unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
except Exception as e: log("load "+str(e))
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    try: lab=a.get_actor_label() or ""
    except: lab=""
    cn=a.get_class().get_name() if a.get_class() else ""
    if not (lab.startswith("Tideborn") or "Sand" in lab or "Water" in lab or "Ocean" in lab or "Shallow" in lab or "Ground" in lab or "PlayerStart" in cn or "Rock" in lab or "Trunk" in lab or "Kelp" in lab or "Hound" in lab or "Gate" in lab or "Gather" in lab):
        continue
    loc=a.get_actor_location(); sc=a.get_actor_scale3d(); rot=a.get_actor_rotation()
    mats=[]
    for comp in a.get_components_by_class(unreal.StaticMeshComponent):
        try:
            mesh=comp.get_editor_property("static_mesh")
            mn=mesh.get_name() if mesh else "?"
        except: mn="?"
        for i in range(4):
            try:
                m=comp.get_material(i)
                if m: mats.append("%s[%d]=%s"%(mn,i,m.get_name()))
            except: break
        break
    hy=50.0*sc.y; hx=50.0*sc.x
    log("%s | %s | loc=(%.0f,%.0f,%.0f) sc=(%.1f,%.1f,%.1f) yaw=%.0f | Y[%.0f..%.0f] X[%.0f..%.0f] | %s"%(
        lab, cn, loc.x,loc.y,loc.z, sc.x,sc.y,sc.z, rot.yaw, loc.y-hy,loc.y+hy, loc.x-hx,loc.x+hx, ";".join(mats) or "-"))
OUT.write_text("\n".join(lines)+"\nDONE\n", encoding="utf-8")
log("wrote %d lines"%len(lines))
