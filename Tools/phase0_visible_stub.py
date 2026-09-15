import unreal
import pathlib

RESULT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\phase0_visible_stub.txt")

def log(m):
    unreal.log("[TidebornP0] " + str(m))

def find_player_start():
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if isinstance(a, unreal.PlayerStart) or a.get_class().get_name().startswith("PlayerStart"):
            return a.get_actor_location()
        if a.get_actor_label() and "PlayerStart" in a.get_actor_label():
            return a.get_actor_location()
    # fallback near typical TP template spawn
    return unreal.Vector(0.0, 0.0, 100.0)

def main():
    map_path = "/Game/ThirdPerson/Maps/ThirdPersonMap"
    try:
        unreal.EditorLoadingAndSavingUtils.load_map(map_path)
    except Exception as e:
        log("load_map: " + str(e))

    for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
        label = a.get_actor_label() or ""
        if label in ("Tideborn_InteractStub", "Tideborn_InteractMarker"):
            unreal.EditorLevelLibrary.destroy_actor(a)

    ps = find_player_start()
    log("PlayerStart=" + str(ps))
    # Place large cube a few meters in front of spawn
    loc = unreal.Vector(ps.x + 300.0, ps.y, ps.z)

    cube = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, loc, unreal.Rotator())
    if not cube:
        raise RuntimeError("cube spawn failed")
    cube.set_actor_label("Tideborn_InteractMarker")
    cube.set_actor_scale3d(unreal.Vector(1.0, 1.0, 2.0))
    mesh_comp = cube.static_mesh_component
    cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
    if cube_mesh:
        mesh_comp.set_static_mesh(cube_mesh)
    # Try a loud color via create/set - BasicShapeMaterial is fine; scale makes it obvious
    mat = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
    if mat:
        mesh_comp.set_material(0, mat)

    trigger = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.TriggerBox, loc + unreal.Vector(0, 0, 100), unreal.Rotator()
    )
    if trigger:
        trigger.set_actor_label("Tideborn_InteractStub")
        trigger.set_actor_scale3d(unreal.Vector(2.0, 2.0, 2.0))
        try:
            tags = list(trigger.tags)
            tags.append("TidebornInteract")
            trigger.tags = tags
        except Exception as e:
            log(str(e))

    # List confirmation
    found = []
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        label = a.get_actor_label() or ""
        if "Tideborn" in label:
            found.append(label + "@" + str(a.get_actor_location()))
    log("found=" + "; ".join(found))

    unreal.EditorLevelLibrary.save_current_level()
    RESULT.write_text("OK marker at PlayerStart+300: " + str(loc) + "\n" + "\n".join(found) + "\n", encoding="utf-8")
    log("DONE marker at spawn")

if __name__ == "__main__":
    main()
