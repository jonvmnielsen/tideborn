"""Generate Tideborn readable grey-to-real blockout meshes and export FBX."""
import bpy
import math
from mathutils import Vector
from pathlib import Path

OUT = Path(r"C:\Users\User\Desktop\AI\Grok\Tideborn\Content\Tideborn\Meshes")
OUT.mkdir(parents=True, exist_ok=True)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def shade_smooth(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

def mat(name, color):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.75
    return m

def assign(obj, material):
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)

def export_fbx(path):
    # select all mesh
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(
        filepath=str(path),
        use_selection=True,
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Z',
        axis_up='Y',
        mesh_smooth_type='FACE',
        add_leaf_bones=False,
    )

def join_selected(name):
    objs = [o for o in bpy.context.selected_objects if o.type == 'MESH']
    if not objs:
        return None
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    objs[0].name = name
    return objs[0]

# --- Wood stump ---
def make_wood_stump():
    reset()
    bark = mat("M_WoodBark", (0.35, 0.2, 0.08))
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.45, depth=1.2, location=(0, 0, 0.6))
    trunk = bpy.context.active_object
    trunk.name = "Trunk"
    assign(trunk, bark)
    # cut top slightly irregular via scale
    trunk.scale = (1.0, 1.05, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    # root flare
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.65, depth=0.25, location=(0, 0, 0.12))
    flare = bpy.context.active_object
    assign(flare, bark)
    # branch stubs
    for i, (ang, z, sc) in enumerate([(0.4, 0.9, 0.35), (2.2, 0.75, 0.28), (4.0, 1.0, 0.22)]):
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.12 * sc / 0.3, depth=0.55, location=(math.cos(ang)*0.35, math.sin(ang)*0.35, z))
        br = bpy.context.active_object
        br.rotation_euler = (1.1, 0, ang)
        assign(br, bark)
    bpy.ops.object.select_all(action='SELECT')
    obj = join_selected("SM_WoodStump")
    shade_smooth(obj)
    export_fbx(OUT / "SM_WoodStump.fbx")
    print("exported SM_WoodStump")

# --- Stone ---
def make_stone():
    reset()
    rock = mat("M_Stone", (0.45, 0.45, 0.48))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.7, location=(0, 0, 0.35))
    a = bpy.context.active_object
    a.scale = (1.3, 1.0, 0.55)
    bpy.ops.object.transform_apply(scale=True)
    assign(a, rock)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.4, location=(0.55, 0.2, 0.25))
    b = bpy.context.active_object
    b.scale = (1.1, 0.9, 0.7)
    bpy.ops.object.transform_apply(scale=True)
    assign(b, rock)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.35, location=(-0.45, -0.15, 0.2))
    c = bpy.context.active_object
    assign(c, rock)
    bpy.ops.object.select_all(action='SELECT')
    obj = join_selected("SM_StoneCluster")
    shade_smooth(obj)
    export_fbx(OUT / "SM_StoneCluster.fbx")
    print("exported SM_StoneCluster")

# --- Burr-hound (low wide quadruped + burr spikes) ---
def make_burr_hound():
    reset()
    hide = mat("M_BurrHide", (0.45, 0.18, 0.12))
    spike = mat("M_BurrSpike", (0.55, 0.35, 0.25))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.45))
    body = bpy.context.active_object
    body.scale = (1.4, 0.7, 0.45)
    bpy.ops.object.transform_apply(scale=True)
    assign(body, hide)
    # head
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.95, 0, 0.55))
    head = bpy.context.active_object
    head.scale = (0.45, 0.4, 0.35)
    bpy.ops.object.transform_apply(scale=True)
    assign(head, hide)
    # snout
    bpy.ops.mesh.primitive_cube_add(size=1, location=(1.3, 0, 0.45))
    sn = bpy.context.active_object
    sn.scale = (0.3, 0.25, 0.2)
    bpy.ops.object.transform_apply(scale=True)
    assign(sn, hide)
    # legs
    for x, y in [(-0.55, 0.35), (-0.55, -0.35), (0.55, 0.35), (0.55, -0.35)]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.12, depth=0.5, location=(x, y, 0.2))
        leg = bpy.context.active_object
        assign(leg, hide)
    # burr spikes on back
    for i, x in enumerate([-0.3, 0.0, 0.35, 0.7]):
        bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.12, depth=0.35, location=(x, 0, 0.75))
        sp = bpy.context.active_object
        assign(sp, spike)
    bpy.ops.object.select_all(action='SELECT')
    obj = join_selected("SM_BurrHound")
    # ground pivot
    obj.location.z = 0
    export_fbx(OUT / "SM_BurrHound.fbx")
    print("exported SM_BurrHound")

# --- Kelp-back (taller, fronds) ---
def make_kelp_back():
    reset()
    body_m = mat("M_KelpBody", (0.12, 0.35, 0.4))
    frond_m = mat("M_KelpFrond", (0.15, 0.55, 0.35))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55, location=(0, 0, 0.7))
    body = bpy.context.active_object
    body.scale = (0.9, 1.2, 1.4)
    bpy.ops.object.transform_apply(scale=True)
    assign(body, body_m)
    # neck/head
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, location=(0, 0.7, 1.35))
    head = bpy.context.active_object
    assign(head, body_m)
    # legs (stumpy)
    for x, y in [(-0.35, 0.35), (0.35, 0.35), (-0.35, -0.35), (0.35, -0.35)]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.14, depth=0.55, location=(x, y, 0.25))
        assign(bpy.context.active_object, body_m)
    # kelp fronds on back
    for i, (x, y, z) in enumerate([(-0.15, -0.1, 1.3), (0.15, 0.0, 1.45), (0.0, 0.2, 1.55), (-0.05, -0.25, 1.35)]):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
        f = bpy.context.active_object
        f.scale = (0.08, 0.25, 0.7)
        f.rotation_euler = (0.3 * i, 0.2, 0.4 * i)
        bpy.ops.object.transform_apply(scale=True, rotation=True)
        assign(f, frond_m)
    bpy.ops.object.select_all(action='SELECT')
    join_selected("SM_KelpBack")
    export_fbx(OUT / "SM_KelpBack.fbx")
    print("exported SM_KelpBack")

# --- Foundation plank ---
def make_foundation():
    reset()
    wood = mat("M_Plank", (0.4, 0.28, 0.12))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.08))
    plank = bpy.context.active_object
    plank.scale = (2.0, 2.0, 0.16)
    bpy.ops.object.transform_apply(scale=True)
    assign(plank, wood)
    # board seams as slight ridges
    for y in [-0.65, 0, 0.65]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, y, 0.14))
        r = bpy.context.active_object
        r.scale = (1.95, 0.08, 0.04)
        bpy.ops.object.transform_apply(scale=True)
        assign(r, wood)
    bpy.ops.object.select_all(action='SELECT')
    join_selected("SM_Foundation")
    export_fbx(OUT / "SM_Foundation.fbx")
    print("exported SM_Foundation")

# --- Shore gate arch ---
def make_shore_gate():
    reset()
    stone = mat("M_GateStone", (0.35, 0.38, 0.45))
    wood = mat("M_GateWood", (0.25, 0.15, 0.08))
    # pillars
    for x in [-1.6, 1.6]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, 1.5))
        p = bpy.context.active_object
        p.scale = (0.45, 0.55, 3.0)
        bpy.ops.object.transform_apply(scale=True)
        assign(p, stone)
    # lintel
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 3.1))
    lintel = bpy.context.active_object
    lintel.scale = (3.8, 0.6, 0.4)
    bpy.ops.object.transform_apply(scale=True)
    assign(lintel, stone)
    # wooden door slab (slightly open visual - solid blocking piece)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.4))
    door = bpy.context.active_object
    door.scale = (2.6, 0.2, 2.6)
    bpy.ops.object.transform_apply(scale=True)
    assign(door, wood)
    bpy.ops.object.select_all(action='SELECT')
    join_selected("SM_ShoreGate")
    export_fbx(OUT / "SM_ShoreGate.fbx")
    print("exported SM_ShoreGate")

# --- Path post ---
def make_path_post():
    reset()
    wood = mat("M_Post", (0.3, 0.18, 0.07))
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.12, depth=2.2, location=(0, 0, 1.1))
    post = bpy.context.active_object
    assign(post, wood)
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.25, depth=0.35, location=(0, 0, 2.3))
    cap = bpy.context.active_object
    assign(cap, wood)
    bpy.ops.object.select_all(action='SELECT')
    join_selected("SM_PathPost")
    export_fbx(OUT / "SM_PathPost.fbx")
    print("exported SM_PathPost")

if __name__ == "__main__":
    make_wood_stump()
    make_stone()
    make_burr_hound()
    make_kelp_back()
    make_foundation()
    make_shore_gate()
    make_path_post()
    print("ALL_DONE")
