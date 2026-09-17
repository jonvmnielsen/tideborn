import unreal
import pathlib

RESULT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\phase_ui_wire_result.txt")
lines = []
LIB = unreal.SubobjectDataBlueprintFunctionLibrary

def log(m):
    unreal.log("[TidebornUI] " + str(m))
    lines.append(str(m))

def var_name(handle, subsystem):
    try:
        data = subsystem.k2_find_subobject_data_from_handle(handle)
        return str(LIB.get_variable_name(data))
    except Exception:
        return "?"

def main():
    char_path = "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter"
    bp = unreal.EditorAssetLibrary.load_asset(char_path)
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = list(subsystem.k2_gather_subobject_data_for_blueprint(bp))
    names = [var_name(h, subsystem) for h in handles]
    log("existing=" + ", ".join(names))
    if any("TidebornUI" in n for n in names):
        log("UI already present")
    else:
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
        params.set_editor_property("new_class", unreal.TidebornUIComponent)
        params.set_editor_property("blueprint_context", bp)
        result = subsystem.add_new_subobject(params)
        new_handle = result[0] if isinstance(result, (tuple, list)) else result
        try:
            subsystem.rename_subobject(new_handle, unreal.Text("TidebornUI"))
        except Exception:
            pass
        log("added TidebornUI")

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(char_path)
    RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log("DONE")

if __name__ == "__main__":
    main()
