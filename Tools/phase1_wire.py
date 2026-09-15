import unreal
import pathlib

RESULT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\phase1_wire_result.txt")
LIB = unreal.SubobjectDataBlueprintFunctionLibrary
lines = []

def log(m):
    unreal.log("[TidebornP1] " + str(m))
    lines.append(str(m))

def var_name(handle, subsystem):
    try:
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        return str(LIB.get_variable_name(data))
    except Exception:
        try:
            return str(LIB.get_display_name(handle))
        except Exception:
            return "<?>"

def ensure_component(bp, subsystem, parent, cls, name):
    handles = list(subsystem.k2_gather_subobject_data_for_blueprint(bp))
    for h in handles:
        n = var_name(h, subsystem)
        if name in n or cls.__name__.replace("Tideborn", "") in n:
            # softer match on known names
            if name in n:
                log("already: " + name)
                return False
    for h in handles:
        n = var_name(h, subsystem)
        if name in n:
            log("already: " + name)
            return False

    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", parent)
    params.set_editor_property("new_class", cls)
    params.set_editor_property("blueprint_context", bp)
    result = subsystem.add_new_subobject(params)
    new_handle = result[0] if isinstance(result, (tuple, list)) else result
    if not new_handle:
        raise RuntimeError("failed add " + name)
    try:
        subsystem.rename_subobject(new_handle, unreal.Text(name))
    except Exception:
        try:
            subsystem.rename_subobject(new_handle, name)
        except Exception as e:
            log("rename skip " + name + ": " + str(e))
    log("added: " + name)
    return True

def wire_character():
    char_path = "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter"
    bp = unreal.EditorAssetLibrary.load_asset(char_path)
    if not bp:
        raise RuntimeError("BP missing")
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = list(subsystem.k2_gather_subobject_data_for_blueprint(bp))
    parent = handles[0]
    for h in handles:
        try:
            data = subsystem.k2_find_subobject_data_from_handle(h)
            if LIB.is_root_component(data) or LIB.is_default_scene_root(data):
                parent = h
                break
        except Exception:
            pass

    # re-check existing names
    names = [var_name(h, subsystem) for h in handles]
    log("existing=" + ", ".join(names))

    def has(name):
        return any(name in n for n in names)

    added = False
    comps = [
        (unreal.TidebornInventoryComponent, "TidebornInventory"),
        (unreal.TidebornCraftingComponent, "TidebornCrafting"),
        (unreal.TidebornBuildComponent, "TidebornBuild"),
        (unreal.TidebornSaveComponent, "TidebornSave"),
    ]
    for cls, name in comps:
        if has(name):
            log("already: " + name)
            continue
        ensure_component(bp, subsystem, parent, cls, name)
        added = True
        # refresh names after add
        handles = list(subsystem.k2_gather_subobject_data_for_blueprint(bp))
        names = [var_name(h, subsystem) for h in handles]

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(char_path)
    log("character saved")
    return added

def find_player_start():
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if isinstance(a, unreal.PlayerStart) or a.get_class().get_name().startswith("PlayerStart"):
            return a.get_actor_location()
        if a.get_actor_label() and "PlayerStart" in a.get_actor_label():
            return a.get_actor_location()
    return unreal.Vector(0.0, 0.0, 100.0)

def place_gather_nodes():
    map_path = "/Game/ThirdPerson/Maps/ThirdPersonMap"
    try:
        unreal.EditorLoadingAndSavingUtils.load_map(map_path)
    except Exception as e:
        log("load_map: " + str(e))

    for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        label = a.get_actor_label() or ""
        if label.startswith("Tideborn_Gather_"):
            unreal.EditorLevelLibrary.destroy_actor(a)

    ps = find_player_start()
    log("PlayerStart=" + str(ps))

    specs = [
        ("Tideborn_Gather_Wood_A", "Wood", unreal.Vector(ps.x + 250.0, ps.y + 80.0, ps.z), unreal.Vector(0.55, 0.55, 1.0)),
        ("Tideborn_Gather_Wood_B", "Wood", unreal.Vector(ps.x + 320.0, ps.y - 40.0, ps.z), unreal.Vector(0.55, 0.55, 1.0)),
        ("Tideborn_Gather_Stone_A", "Stone", unreal.Vector(ps.x + 280.0, ps.y + 180.0, ps.z), unreal.Vector(0.7, 0.7, 0.5)),
    ]

    placed = []
    for label, item_id, loc, scale in specs:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.TidebornGatherNode, loc, unreal.Rotator())
        if not actor:
            raise RuntimeError("spawn failed " + label)
        actor.set_actor_label(label)
        actor.set_actor_scale3d(scale)
        try:
            actor.set_editor_property("item_id", unreal.Name(item_id))
        except Exception:
            try:
                actor.set_editor_property("ItemId", unreal.Name(item_id))
            except Exception as e:
                log("set item_id fail: " + str(e))
        try:
            actor.set_editor_property("amount_per_gather", 1)
            actor.set_editor_property("remaining_uses", 12)
        except Exception:
            pass
        placed.append(label + "@" + str(loc) + "->" + item_id)

    unreal.EditorLevelLibrary.save_current_level()
    log("placed: " + "; ".join(placed))

def main():
    log("Phase1 wire start")
    log("Inv=" + str(unreal.TidebornInventoryComponent))
    log("Gather=" + str(unreal.TidebornGatherNode))
    wire_character()
    place_gather_nodes()
    RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log("DONE")

if __name__ == "__main__":
    main()
