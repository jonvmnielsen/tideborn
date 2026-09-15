import unreal
import pathlib

RESULT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\phase1_fix_result.txt")
lines = []

def log(m):
    unreal.log("[TidebornP1Fix] " + str(m))
    lines.append(str(m))

def find_player_start():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = subsystem.get_all_level_actors()
    for a in actors:
        if isinstance(a, unreal.PlayerStart) or a.get_class().get_name().startswith("PlayerStart"):
            return a.get_actor_location()
        if a.get_actor_label() and "PlayerStart" in a.get_actor_label():
            return a.get_actor_location()
    return unreal.Vector(900.0, 1110.0, 92.0)

def main():
    map_path = "/Game/ThirdPerson/Maps/ThirdPersonMap"
    try:
        unreal.EditorLoadingAndSavingUtils.load_map(map_path)
    except Exception as e:
        log("load_map: " + str(e))

    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in list(subsystem.get_all_level_actors()):
        label = a.get_actor_label() or ""
        if label.startswith("Tideborn_Gather_") or label in ("Tideborn_InteractMarker", "Tideborn_InteractStub"):
            log("destroy " + label)
            subsystem.destroy_actor(a)

    ps = find_player_start()
    log("PlayerStart=" + str(ps))

    # Ring of obvious nodes right in front of spawn (toward +X like old marker)
    specs = [
        ("Tideborn_Gather_Wood_A", "Wood", unreal.Vector(ps.x + 220.0, ps.y, ps.z + 40.0)),
        ("Tideborn_Gather_Wood_B", "Wood", unreal.Vector(ps.x + 220.0, ps.y + 160.0, ps.z + 40.0)),
        ("Tideborn_Gather_Stone_A", "Stone", unreal.Vector(ps.x + 220.0, ps.y - 160.0, ps.z + 40.0)),
    ]

    for label, item_id, loc in specs:
        actor = subsystem.spawn_actor_from_class(unreal.TidebornGatherNode, loc, unreal.Rotator())
        if not actor:
            raise RuntimeError("spawn failed " + label)
        actor.set_actor_label(label)
        try:
            actor.set_editor_property("item_id", unreal.Name(item_id))
        except Exception:
            actor.set_editor_property("ItemId", unreal.Name(item_id))
        try:
            actor.set_editor_property("remaining_uses", 20)
        except Exception:
            pass
        log("spawned " + label + " " + item_id + " @ " + str(loc))

    # Verify character comps still present
    bp = unreal.EditorAssetLibrary.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
    subsystem_so = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    LIB = unreal.SubobjectDataBlueprintFunctionLibrary
    names = []
    for h in subsystem_so.k2_gather_subobject_data_for_blueprint(bp):
        try:
            data = subsystem_so.k2_find_subobject_data_from_handle(h)
            names.append(str(LIB.get_variable_name(data)))
        except Exception:
            pass
    log("BP comps: " + ", ".join(names))
    for need in ("TidebornInventory", "TidebornCrafting", "TidebornBuild", "TidebornSave", "TidebornInteract"):
        log(("OK " if any(need in n for n in names) else "MISSING ") + need)

    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log("DONE")

if __name__ == "__main__":
    main()
