"""Scene construction: two R6 fighters + arena + lights + cameras + compositor.

Recipes carried over from the (verified) pre-reset build:
- lights: key 5200W / fill 1800W / rim 8000W spot
- bokeh emissive 1.8
- compositor Glare Bloom: threshold 2.0, size 7, strength 0.35
- camera rigs CA..CG with the post height-patch values
"""
import bpy
from mathutils import Vector

import blender_api as api

BODY = ("Head", "Torso", "Left Arm", "Right Arm", "Left Leg", "Right Leg")

# camera rigs: name -> (loc, lens, target)
CAMERAS = {
    "CA": ((8.0, -10.0, 4.0), 38, (0.0, 0.0, 3.1)),    # wide establishing
    "CB": ((3.2, -7.5, 2.9), 45, (0.55, -0.4, 3.3)),   # three-quarter action
    "CC": ((2.9, -1.9, 4.2), 40, (0.3, -1.9, 4.2)),    # close-up (lens 60 in cuts)
    "CD": ((0.3, -1.6, 11.5), 35, (0.3, -1.5, 2.6)),   # top-down
    "CE": ((3.6, -3.2, 1.6), 45, (0.6, 0.0, 3.0)),     # low angle
    "CF": ((3.6, 2.6, 3.6), 45, (0.5, -0.8, 3.3)),     # cross
    "CG": ((4.8, -4.6, 3.4), 38, (0.8, 0.8, 3.0)),     # final (frames both corners)
}


def build_fighters():
    """Open the rig, create P1 (original, cyan) and P2 (copy, dark).
    Returns (P1 Fighter, P2 Fighter, scene)."""
    bpy.ops.wm.open_mainfile(filepath="/home/user/r6roblox-animation/extracted/BlenderRig/R6IK_1.blend")
    scn = bpy.context.scene
    orig = {o.name: o for o in scn.objects}

    # P1 = originals renamed
    p1 = {"Armature": "P1_Armature"}
    for n in list(orig.keys()):
        if n in BODY:
            p1[n] = "P1_" + n.replace(" ", "_")
    for n, new in p1.items():
        orig[n].name = new

    # P2 = full copies with separate mesh data
    for n, new in p1.items():
        src = bpy.data.objects[new]
        cp = src.copy()
        if cp.data is not None:
            cp.data = cp.data.copy()
        cp.name = new.replace("P1_", "P2_")
        scn.collection.objects.link(cp)
        if cp.type == 'MESH':
            cp.parent = bpy.data.objects["P2_Armature"]
            for m in cp.modifiers:
                if m.type == 'ARMATURE':
                    m.object = bpy.data.objects["P2_Armature"]

    # dark body material for P2
    opp = bpy.data.materials.new("OppBody")
    opp.use_nodes = True
    bb = opp.node_tree.nodes["Principled BSDF"]
    bb.inputs["Base Color"].default_value = (0.16, 0.16, 0.18, 1.0)
    bb.inputs["Roughness"].default_value = 0.45
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith("P2_"):
            for i, m in enumerate(o.data.materials):
                if m and m.name == "R64Mtl":
                    o.data.materials[i] = opp

    # hide helper meshes on both fighters
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        short = o.name.split("_", 1)[-1] if "_" in o.name else o.name
        if short in api.HIDDEN_MESH_PARTS:
            o.hide_render = True
    # the driver-only armature
    for o in bpy.data.objects:
        if o.type == 'ARMATURE' and o.name not in ("P1_Armature", "P2_Armature"):
            o.hide_render = True

    f1 = api.Fighter(bpy.data.objects["P1_Armature"], "P1")
    f2 = api.Fighter(bpy.data.objects["P2_Armature"], "P2")
    return f1, f2, scn


def _add_mat(name, color, rough=0.6, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    if emit > 0:
        b.inputs["Emission Color"].default_value = (*color, 1.0)
        b.inputs["Emission Strength"].default_value = emit
    return m


def build_arena(scn):
    # floor (large, dark, slightly glossy)
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "Floor"
    floor.data.materials.append(_add_mat("ArenaFloor", (0.045, 0.04, 0.05), rough=0.35))

    # ring platform
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.09))
    plat = bpy.context.object
    plat.name = "RingPlatform"
    plat.scale = (3.6, 3.6, 0.09)
    plat.data.materials.append(_add_mat("RingMat", (0.13, 0.05, 0.05), rough=0.8))

    # corner posts + 3 ropes per side
    post_mat = _add_mat("PostMat", (0.35, 0.35, 0.38), rough=0.4)
    rope_mat = _add_mat("RopeMat", (0.75, 0.08, 0.08), rough=0.5)
    corners = [(-3.3, -3.3), (3.3, -3.3), (3.3, 3.3), (-3.3, 3.3)]
    post_h = 2.6
    for i, (x, y) in enumerate(corners):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=post_h,
                                            location=(x, y, post_h / 2))
        p = bpy.context.object
        p.name = "Post_%d" % i
        p.data.materials.append(post_mat)
    for i in range(4):
        x1, y1 = corners[i]
        x2, y2 = corners[(i + 1) % 4]
        for k, h in enumerate((0.9, 1.6, 2.3)):
            mid = ((x1 + x2) / 2, (y1 + y2) / 2, h)
            dx, dy = x2 - x1, y2 - y1
            import math
            L = (dx * dx + dy * dy) ** 0.5
            bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=L,
                                                location=mid,
                                                rotation=(0, 1.5708, math.atan2(dy, dx)))
            r = bpy.context.object
            r.name = "Rope_%d_%d" % (i, k)
            r.data.materials.append(rope_mat)

    # dark backdrop
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 26, 18),
                                     rotation=(1.5708, 0, 0))
    bd = bpy.context.object
    bd.name = "Backdrop"
    bd.data.materials.append(_add_mat("BackMat", (0.02, 0.02, 0.028), rough=1.0))

    # bokeh dust (emissive specks, emit 1.8)
    bokeh_mat = _add_mat("Bokeh", (1.0, 0.85, 0.55), emit=1.8)
    import random
    random.seed(7)
    for i in range(42):
        x = random.uniform(-14, 14)
        y = random.uniform(2, 16)
        z = random.uniform(0.5, 6.5)
        r = random.uniform(0.02, 0.07)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(x, y, z), segments=8, ring_count=6)
        b = bpy.context.object
        b.name = "Bokeh_%d" % i
        b.data.materials.append(bokeh_mat)
        b.hide_select = False


def build_lights(scn):
    def spot(name, loc, tgt, energy, size=0.5, color=(1, 1, 1)):
        d = bpy.data.lights.new(name, 'SPOT')
        d.energy = energy
        d.spot_size = 1.15
        d.spot_blend = size
        d.color = color
        o = bpy.data.objects.new(name, d)
        scn.collection.objects.link(o)
        o.location = loc
        dd = Vector(tgt) - Vector(loc)
        o.rotation_euler = dd.to_track_quat('-Z', 'Y').to_euler()
        return o

    spot("Key", (6.5, -8.0, 9.0), (0, 0, 3.0), 5200, 0.35, (1.0, 0.97, 0.92))
    fill_d = bpy.data.lights.new("Fill", 'AREA')
    fill_d.energy = 1800
    fill_d.size = 6
    fill_d.color = (0.75, 0.82, 1.0)
    fill = bpy.data.objects.new("Fill", fill_d)
    scn.collection.objects.link(fill)
    fill.location = (-7.0, -6.0, 5.5)
    dd = Vector((0, 0, 2.5)) - fill.location
    fill.rotation_euler = dd.to_track_quat('-Z', 'Y').to_euler()
    spot("Rim", (-2.0, 12.0, 7.0), (0, 0, 3.2), 8000, 0.25, (0.85, 0.9, 1.0))

    w = bpy.context.scene.world
    if w is None:
        w = bpy.data.worlds.new("World")
        scn.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Strength"].default_value = 0.02
        bg.inputs["Color"].default_value = (0.05, 0.06, 0.09, 1.0)


def build_cameras(scn):
    for name, (loc, lens, tgt) in CAMERAS.items():
        cd = bpy.data.cameras.new(name)
        cd.lens = lens
        o = bpy.data.objects.new(name, cd)
        scn.collection.objects.link(o)
        o.location = loc
        d = Vector(tgt) - Vector(loc)
        o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scn.camera = bpy.data.objects["CA"]


def build_compositor(scn):
    """Verified Blender 5 recipe: compositing node group, feed GROUP_OUTPUT,
    Glare 'Bloom' thr 2.0 str 0.35 size 7."""
    scn.use_nodes = True
    before = {g.name for g in bpy.data.node_groups}
    bpy.ops.node.new_compositing_node_group()
    g = next(g for g in bpy.data.node_groups if g.name not in before)
    g.name = "FXGroup"
    scn.compositing_node_group = g
    scn.render.use_compositing = True
    gl = g.nodes.new("CompositorNodeGlare")
    def setin(name, val):
        try:
            gl.inputs[name].default_value = val
        except Exception:
            pass
    setin("Type", "Bloom")
    setin("Quality", "High")
    setin("Threshold", 2.0)
    setin("Size", 7)
    setin("Strength", 0.35)
    rl = next(n for n in g.nodes if n.bl_idname == "CompositorNodeRLayers")
    g.links.new(rl.outputs["Image"], gl.inputs["Image"])
    go = next(n for n in g.nodes if n.bl_idname == "NodeGroupOutput")
    g.links.new(gl.outputs["Image"], go.inputs["Image"])


def render_settings(scn, res=(1280, 720), samples=32):
    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'CPU'
    scn.cycles.samples = samples
    scn.cycles.use_denoising = True
    scn.render.resolution_x = res[0]
    scn.render.resolution_y = res[1]
    scn.render.resolution_percentage = 100
    scn.render.image_settings.file_format = 'PNG'
    scn.frame_start = 1
    scn.frame_end = 600
