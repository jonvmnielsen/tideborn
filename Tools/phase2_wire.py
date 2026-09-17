import unreal
import pathlib

RESULT = pathlib.Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\phase2_wire_result.txt")
lines = []

def log(m):
    unreal.log("[TidebornP2] " + str(m))
    lines.append(str(m))

def find_player_start():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in sub.get_all_level_actors():
        if isinstance(a, unreal.PlayerStart) or a.get_class().get_name().startswith("PlayerStart"):
            return a.get_actor_location()
    return unreal.Vector(900.0, 1110.0, 92.0)

def main():
    try:
        unreal.EditorLoadingAndSavingUtils.load_map("/Game/ThirdPerson/Maps/ThirdPersonMap")
    except Exception as e:
        log("load_map " + str(e))

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in list(sub.get_all_level_actors()):
        label = a.get_actor_label() or ""
        if label.startswith("Tideborn_P2_"):
            sub.destroy_actor(a)
            log("destroy " + label)

    ps = find_player_start()
    log("PS=" + str(ps))

    # Path toward +X from spawn
    hound = sub.spawn_actor_from_class(unreal.TidebornBurrHound, unreal.Vector(ps.x + 700.0, ps.y + 250.0, ps.z + 100.0), unreal.Rotator())
    hound.set_actor_label("Tideborn_P2_BurrHound")
    log("hound")

    kelp = sub.spawn_actor_from_class(unreal.TidebornKelpBack, unreal.Vector(ps.x + 450.0, ps.y - 220.0, ps.z + 100.0), unreal.Rotator())
    kelp.set_actor_label("Tideborn_P2_KelpBack")
    log("kelp")

    gate = sub.spawn_actor_from_class(unreal.TidebornShoreGate, unreal.Vector(ps.x + 1100.0, ps.y, ps.z + 200.0), unreal.Rotator())
    gate.set_actor_label("Tideborn_P2_ShoreGate")
    log("gate")

    # Path posts between PlayerStart and Shore Gate (warm lights → cyan vista)
    beacon_class = unreal.TidebornLandmarkBeacon
    offsets = (0.28, 0.52, 0.78)  # fractions along PS → gate
    for i, t in enumerate(offsets):
        loc = unreal.Vector(
            ps.x + (1100.0 * t),
            ps.y + ((-80.0) if i % 2 == 0 else 90.0),
            ps.z + 40.0,
        )
        beacon = sub.spawn_actor_from_class(beacon_class, loc, unreal.Rotator())
        beacon.set_actor_label("Tideborn_P2_PathPost_%d" % (i + 1))
        log("beacon_%d @ %s" % (i + 1, loc))

    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    RESULT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log("DONE")

if __name__ == "__main__":
    main()
