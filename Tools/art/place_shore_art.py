import unreal
from pathlib import Path

RESULT = Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\place_shore_result.txt")
lines = []

def log(m):
    unreal.log("[TidebornShore] " + str(m))
    lines.append(str(m))

MESH_DST = "/Game/Tideborn/Art/Meshes"
MAT_DST = "/Game/Tideborn/Art/Materials"

def find_player_start():
    try:
        for a in unreal.EditorLevelLibrary.get_all_level_actors():
            cls = a.get_class().get_name()
            label = a.get_actor_label()
            if "PlayerStart" in cls or "PlayerStart" in label:
                return a.get_actor_location()
    except Exception as e:
        log(f"ps fail {e}")
    return unreal.Vector(0, 0, 100)

def load_mat(name):
    return unreal.EditorAssetLibrary.load_asset(f"{MAT_DST}/{name}")

def place_sm(asset_path, loc, scale, label):
    sm = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not sm:
        log(f"missing {asset_path}")
        return None
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(sm, loc, unreal.Rotator(0, 0, 0))
    if actor:
        actor.set_actor_scale3d(unreal.Vector(*scale))
        actor.set_actor_label(label)
        log(f"placed {label}")
    return actor

def apply_mat_to_actor(actor, mat):
    if not actor or not mat:
        return
    for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
        try:
            comp.set_material(0, mat)
        except Exception:
            pass

def tweak_lights():
    try:
        for actor in unreal.EditorLevelLibrary.get_all_level_actors():
            name = actor.get_class().get_name()
            if "DirectionalLight" in name:
                try:
                    actor.set_editor_property("intensity", 10.0)
                    actor.set_editor_property("light_color", unreal.LinearColor(1.0, 0.82, 0.65, 1.0))
                except Exception:
                    pass
            if "SkyLight" in name:
                try:
                    actor.set_editor_property("intensity", 1.4)
                    actor.set_editor_property("real_time_capture", True)
                except Exception:
                    pass
            if "ExponentialHeightFog" in name:
                try:
                    actor.set_editor_property("fog_density", 0.012)
                except Exception:
                    pass
        log("lighting tweaked")
    except Exception as e:
        log(f"light fail {e}")

def main():
    spawn = find_player_start()
    log(f"spawn {spawn}")

    # Clear prior TidebornShore_* actors
    try:
        for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
            if a.get_actor_label().startswith("TidebornShore_"):
                unreal.EditorLevelLibrary.destroy_actor(a)
                log(f"removed {a.get_actor_label()}")
    except Exception as e:
        log(f"cleanup {e}")

    wood = load_mat("M_Tideborn_WoodACG") or load_mat("M_Tideborn_Wood") or load_mat("M_Tideborn_Bark")
    rock = load_mat("M_Tideborn_RockShore") or load_mat("M_Tideborn_RockBoulder") or load_mat("M_Tideborn_RockACG")
    bark = load_mat("M_Tideborn_Bark") or load_mat("M_Tideborn_BarkACG")

    placements = [
        (f"{MESH_DST}/coast_land_rocks_02_1k", (450, 250, -20), (1, 1, 1), "TidebornShore_RocksA", rock),
        (f"{MESH_DST}/coast_land_rocks_03_1k", (700, -180, -20), (1, 1, 1), "TidebornShore_RocksB", rock),
        (f"{MESH_DST}/boulder_01_1k", (320, -320, 0), (1.5, 1.5, 1.5), "TidebornShore_Boulder", rock),
        (f"{MESH_DST}/dead_tree_trunk_1k", (200, 420, 0), (1.2, 1.2, 1.2), "TidebornShore_Trunk", bark or wood),
    ]
    for path, offset, scale, label, mat in placements:
        loc = unreal.Vector(spawn.x + offset[0], spawn.y + offset[1], spawn.z + offset[2])
        actor = place_sm(path, loc, scale, label)
        apply_mat_to_actor(actor, mat)

    # Retint existing gather/foundation/gate if labeled
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        label = a.get_actor_label().lower()
        mat = None
        if any(k in label for k in ("foundation", "build", "wood", "stump", "gather")):
            mat = wood or bark
        if any(k in label for k in ("stone", "gate", "rock", "shore")):
            mat = rock
        if mat:
            apply_mat_to_actor(a, mat)
            log(f"mat -> {a.get_actor_label()}")

    tweak_lights()
    unreal.EditorLevelLibrary.save_current_level()
    RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log("DONE")

if __name__ == "__main__":
    main()