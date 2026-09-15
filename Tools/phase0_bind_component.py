import unreal
import pathlib

RESULT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\phase0_bind_result.txt")
LIB = unreal.SubobjectDataBlueprintFunctionLibrary

def log(m):
    unreal.log("[TidebornP0] " + str(m))

def var_name(handle, subsystem):
    try:
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        return str(LIB.get_variable_name(data))
    except Exception as e:
        try:
            return str(LIB.get_display_name(handle))
        except Exception:
            return "<?>"

def add_interact_component():
    char_path = "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter"
    bp = unreal.EditorAssetLibrary.load_asset(char_path)
    if not bp:
        raise RuntimeError("BP_ThirdPersonCharacter missing")

    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = list(subsystem.k2_gather_subobject_data_for_blueprint(bp))
    log("handles=" + str(len(handles)))

    for h in handles:
        n = var_name(h, subsystem)
        log("subobj: " + n)
        if "TidebornInteract" in n:
            log("Already present")
            RESULT.write_text("OK already had component\n", encoding="utf-8")
            return

    # Prefer DefaultSceneRoot / first scene component as parent
    parent = handles[0]
    for h in handles:
        try:
            data = subsystem.k2_find_subobject_data_from_handle(h)
            if LIB.is_root_component(data) or LIB.is_default_scene_root(data):
                parent = h
                break
        except Exception:
            pass

    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", parent)
    params.set_editor_property("new_class", unreal.TidebornInteractComponent)
    params.set_editor_property("blueprint_context", bp)

    result = subsystem.add_new_subobject(params)
    # May return (handle, FText) or just handle depending on version
    new_handle = result
    fail_reason = None
    if isinstance(result, (tuple, list)):
        new_handle = result[0]
        if len(result) > 1:
            fail_reason = result[1]

    if fail_reason:
        log("fail_reason=" + str(fail_reason))
    if not new_handle:
        raise RuntimeError("add_new_subobject failed: " + str(fail_reason))

    try:
        subsystem.rename_subobject(new_handle, unreal.Text("TidebornInteract"))
    except Exception:
        try:
            subsystem.rename_subobject(new_handle, "TidebornInteract")
        except Exception as e:
            log("rename skip: " + str(e))

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(char_path)
    log("Added and saved")
    RESULT.write_text("OK added TidebornInteractComponent\n", encoding="utf-8")

def main():
    log("Bind v2 start")
    log("cls=" + str(unreal.TidebornInteractComponent))
    add_interact_component()
    log("DONE bind v2")

if __name__ == "__main__":
    main()
