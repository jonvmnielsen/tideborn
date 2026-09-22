import bpy
import math
from mathutils import Vector, noise

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Beach grid: X along shore, Y toward ocean (negative = water)
# Size in meters (UE will scale x100 for cm): 80m x 100m
sx, sy = 80, 100
res_x, res_y = 160, 200

bpy.ops.mesh.primitive_grid_add(x_subdivisions=res_x, y_subdivisions=res_y, size=1)
beach = bpy.context.active_object
beach.name = "SM_TidebornBeach"
beach.scale = (sx, sy, 1)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

mesh = beach.data
# Displace vertices: inland high, ocean low, side dunes
for v in mesh.vertices:
    x, y, z = v.co
    # normalize -0.5..0.5 from size
    nx = x / sx
    ny = y / sy  # -0.5 (ocean) .. +0.5 (inland)
    # base slope: inland (+Y) higher, ocean (-Y) lower
    h = (ny + 0.5) * 2.2  # 0 at ocean edge -> ~2.2m inland
    # cove bowl: center lower corridor
    cove = -1.1 * math.exp(-(nx * nx) * 8.0) * max(0.0, 0.55 - ny)
    # side dunes / berms
    dunes = 1.4 * math.exp(-((abs(nx) - 0.28) ** 2) * 55) * (0.4 + 0.6 * (ny + 0.5))
    # gentle noise
    nval = noise.noise(Vector((x * 0.08, y * 0.08, 0.0))) * 0.35
    nval2 = noise.noise(Vector((x * 0.25, y * 0.25, 1.7))) * 0.12
    v.co.z = h + cove + dunes + nval + nval2

# Recalc normals
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')

# UV unwrap smart
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')

# Water plane (flat, lower)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -35, -0.8))
water = bpy.context.active_object
water.name = "SM_TidebornWater"
water.scale = (90, 50, 1)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Export FBX — UE units cm, so scale_apply with 100
out_beach = r"C:\Users\User\Desktop\AI\Grok\Tideborn\RawArt\CC0\Models\SM_TidebornBeach.fbx"
out_water = r"C:\Users\User\Desktop\AI\Grok\Tideborn\RawArt\CC0\Models\SM_TidebornWater.fbx"

def export(obj, path):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Y',
        axis_up='Z',
        mesh_smooth_type='FACE',
        global_scale=100.0,  # m -> cm for UE
    )
    print("exported", path)

export(beach, out_beach)
export(water, out_water)
print("DONE beach+water")
