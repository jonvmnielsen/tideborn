import unreal
import pathlib

def log(m):
    unreal.log("[TidebornP0] " + str(m))

ACTIONS = "/Game/ThirdPerson/Input/Actions"
INPUT_DIR = "/Game/ThirdPerson/Input"
MAP = "/Game/ThirdPerson/Maps/ThirdPersonMap"
RESULT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\phase0_result.txt")

def load(path):
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    return None

def make_key_e():
    k = unreal.Key()
    k.set_editor_property("key_name", "E")
    return k

def create_ia_interact():
    dest_path = ACTIONS + "/IA_Interact"
    if unreal.EditorAssetLibrary.does_asset_exist(dest_path):
        log("IA_Interact exists")
        return load(dest_path)
    src = load(ACTIONS + "/IA_Jump")
    if not src:
        raise RuntimeError("IA_Jump missing")
    action = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset("IA_Interact", ACTIONS, src)
    if not action:
        action = unreal.EditorAssetLibrary.duplicate_asset(ACTIONS + "/IA_Jump", dest_path)
    if not action:
        raise RuntimeError("Could not create IA_Interact")
    try:
        action.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
    except Exception as e:
        log(str(e))
    unreal.EditorAssetLibrary.save_asset(dest_path)
    log("Created IA_Interact")
    return load(dest_path) or action

def add_e_mapping(action):
    imc_path = INPUT_DIR + "/IMC_Default"
    imc = load(imc_path)
    mappings = list(imc.get_editor_property("mappings"))
    key_e = make_key_e()
    for m in mappings:
        try:
            if m.get_editor_property("action") == action:
                kn = str(m.get_editor_property("key").get_editor_property("key_name"))
                if kn == "E":
                    log("E mapping already present")
                    return
        except Exception:
            pass
    mapping = unreal.EnhancedActionKeyMapping()
    mapping.set_editor_property("action", action)
    mapping.set_editor_property("key", key_e)
    mappings.append(mapping)
    imc.set_editor_property("mappings", mappings)
    unreal.EditorAssetLibrary.save_asset(imc_path)
    log("Mapped E -> IA_Interact")

def place_stub():
    try:
        unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    except Exception as e:
        log("load_map " + str(e))
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label() == "Tideborn_InteractStub":
            unreal.EditorLevelLibrary.destroy_actor(a)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.TriggerBox, unreal.Vector(350.0, 0.0, 110.0), unreal.Rotator()
    )
    if not actor:
        raise RuntimeError("spawn failed")
    actor.set_actor_label("Tideborn_InteractStub")
    actor.set_actor_scale3d(unreal.Vector(1.5, 1.5, 1.5))
    try:
        tags = list(actor.tags)
        tags.append("TidebornInteract")
        actor.tags = tags
    except Exception as e:
        log("tags " + str(e))
    unreal.EditorLevelLibrary.save_current_level()
    log("Placed Tideborn_InteractStub")

def main():
    log("Start v4")
    action = create_ia_interact()
    add_e_mapping(action)
    place_stub()
    RESULT.write_text("OK v4\nIA_Interact\nIMC E\nTriggerBox Tideborn_InteractStub\n", encoding="utf-8")
    log("DONE Phase 0 asset setup v4")

if __name__ == "__main__":
    main()
