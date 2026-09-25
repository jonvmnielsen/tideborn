import bpy, math
from mathutils import Vector, noise

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# v9: ~50m wide x 12m deep, 240uu drop toward water (-Y).
# MUST be placed with min world Y >= ~530 so it never covers mid-ocean.
sx, sy = 5000.0, 1200.0
res_x, res_y = 48, 28
drop = 240.0

bpy.ops.mesh.primitive_grid_add(x_subdivisions=res_x, y_subdivisions=res_y, size=1)
slope = bpy.context.active_object
slope.name = "SM_TidebornBeachSlope"
slope.scale = (sx, sy, 1.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

for v in slope.data.vertices:
    x, y, z = v.co
    # t=0 at land (+Y), t=1 at water (-Y)
    t = 0.5 - (y / sy)
    t = max(0.0, min(1.0, t))
    wave = 0.14 * math.sin(x * 0.0035) + 0.09 * math.sin(x * 0.008 + 1.1)
    t2 = max(0.0, min(1.0, t + wave * t * 0.5))
    h = -drop * (t2 * t2 * (3.0 - 2.0 * t2))
    n1 = noise.noise(Vector((x * 0.0022, y * 0.0022, 0.7))) * 8.0
    v.co.z = h + n1 * t2
    edge = abs(x) / (sx * 0.5)
    if edge > 0.90:
        v.co.z *= max(0.0, 1.0 - (edge - 0.90) / 0.10)

# Keep origin at land-surface Z=0 (do NOT recenter) so UE place Z is predictable.
bpy.ops.object.origin_set(type="ORIGIN_CURSOR")  # cursor is 0,0,0
# Force origin to (0,0,0) geometric center XY but Z=0 land reference:
# Actually set origin to geometry center then shift mesh so max Z ~ 0
import bmesh
bm = bmesh.new()
bm.from_mesh(slope.data)
zs = [v.co.z for v in bm.verts]
zmax = max(zs)
for v in bm.verts:
    v.co.z -= zmax  # land ~0, water ~-drop
xs = [v.co.x for v in bm.verts]
ys = [v.co.y for v in bm.verts]
cx = 0.5 * (min(xs) + max(xs))
cy = 0.5 * (min(ys) + max(ys))
for v in bm.verts:
    v.co.x -= cx
    v.co.y -= cy
bm.to_mesh(slope.data)
bm.free()
slope.location = (0, 0, 0)

bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")

out = r"C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\export\SM_TidebornBeachSlope.fbx"
bpy.ops.object.select_all(action="DESELECT")
slope.select_set(True)
bpy.context.view_layer.objects.active = slope
bpy.ops.export_scene.fbx(
    filepath=out, use_selection=True, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
    mesh_smooth_type="FACE", global_scale=1.0,
)
zs = [v.co.z for v in slope.data.vertices]
print("exported", out, "xy", sx, sy, "drop", drop, "zrange", min(zs), max(zs))
print("DONE beach slope v9")
