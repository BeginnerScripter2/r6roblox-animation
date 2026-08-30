"""Procedural VFX for the boxing scene.

Black-art lessons from the pre-reset build (all baked in here):
1. In this Blender 5 build, an unkeyframed Principled socket extrapolates
   NEGATIVE to its default value before the first key, which renders as
   OPAQUE BLACK.  Every animated Alpha/Emission socket therefore gets a
   ZERO key at frame 1 (_zero_preframe).
2. The alpha'd Principled BSDF must be explicitly linked to the Material
   Output node (a default new material has the link, but we rebuild the
   graph by hand so we make it explicit and verify it).
3. Extra safety: every VFX object also scales to 0 outside its event
   window, so even a broken alpha can never leave a black blob.
"""
import bpy
import math
from mathutils import Vector

DEG = math.pi / 180.0


def _key(sock, frame, value):
    sock.default_value = value
    sock.keyframe_insert("default_value", frame=frame)


def _zero_preframe(sock):
    """Frame-1 zero key so pre-first-key extrapolation is 0, not opaque."""
    cur = sock.default_value
    _key(sock, 1, 0.0)
    sock.default_value = cur


def _make_vfx_mat(name, base=(0.0, 0.0, 0.0, 1.0)):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.location = (0, 0)
    p.inputs["Base Color"].default_value = base
    p.inputs["Roughness"].default_value = 0.5
    p.inputs["Alpha"].default_value = 0.0
    p.inputs["Emission Color"].default_value = base if base[0] + base[1] + base[2] > 0.05 else (1.0, 1.0, 1.0)
    p.inputs["Emission Strength"].default_value = 0.0
    nt.links.new(p.outputs["BSDF"], out.inputs["Surface"])   # explicit link
    return m, p


def _scale_window(ob, f0, f1, s0=0.0, s1=1.0, grow_to=None):
    """Scale 0 -> s1 over f0..f1 (optionally growing), back to 0."""
    for f, s in ((1, s0), (max(1, f0), s0)):
        ob.scale = (s, s, s)
        ob.keyframe_insert("scale", frame=f)
    if grow_to:
        ob.scale = (s1, s1, s1)
        ob.keyframe_insert("scale", frame=f0)
        ob.scale = (grow_to, grow_to, grow_to)
        ob.keyframe_insert("scale", frame=f1)
    else:
        ob.scale = (s1, s1, s1)
        ob.keyframe_insert("scale", frame=f0 + 1)
    ob.scale = (0.0, 0.0, 0.0)
    ob.keyframe_insert("scale", frame=f1)


def flash(pos, frame, strength=6.0, dur=5, size=0.34, color=(1.0, 0.92, 0.7)):
    """Impact flash sphere."""
    m, p = _make_vfx_mat("FlashMat", (*color, 1.0))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=size, location=pos, segments=12, ring_count=8)
    ob = bpy.context.object
    ob.name = "VFX_flash_%d" % frame
    ob.data.materials.append(m)
    _zero_preframe(p.inputs["Alpha"])
    _zero_preframe(p.inputs["Emission Strength"])
    _key(p.inputs["Alpha"], frame, 1.0)
    _key(p.inputs["Emission Strength"], frame, strength)
    _key(p.inputs["Alpha"], frame + 2, 0.55)
    _key(p.inputs["Emission Strength"], frame + 2, strength * 0.5)
    _key(p.inputs["Alpha"], frame + dur, 0.0)
    _key(p.inputs["Emission Strength"], frame + dur, 0.0)
    _scale_window(ob, frame, frame + dur, 0.0, 1.0, grow_to=2.2)
    return ob


def shockwave(pos, frame, r0=1.6, r1=3.5, dur=9, strength=2.0,
              color=(0.7, 0.85, 1.0)):
    """Expanding ground ring (squashed torus)."""
    m, p = _make_vfx_mat("ShockMat", (*color, 1.0))
    z = max(0.12, pos[2] * 0.06)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.5, minor_radius=0.045,
                                     location=(pos[0], pos[1], z),
                                     major_segments=40, minor_segments=8)
    ob = bpy.context.object
    ob.name = "VFX_shock_%d" % frame
    ob.scale = (r0, r0, 1.0)
    ob.data.materials.append(m)
    _zero_preframe(p.inputs["Alpha"])
    _zero_preframe(p.inputs["Emission Strength"])
    _key(p.inputs["Alpha"], frame, 0.9)
    _key(p.inputs["Emission Strength"], frame, strength)
    _key(p.inputs["Alpha"], frame + dur, 0.0)
    _key(p.inputs["Emission Strength"], frame + dur, 0.0)
    ob.scale = (r0, r0, 1.0)
    ob.keyframe_insert("scale", frame=frame)
    ob.scale = (r1, r1, 1.0)
    ob.keyframe_insert("scale", frame=frame + dur)
    ob.scale = (0.0, 0.0, 0.0)
    ob.keyframe_insert("scale", frame=frame + dur + 1)
    return ob


def sparks(pos, frame, count=12, dist=1.1, dur=10, strength=4.0,
           color=(1.0, 0.75, 0.3)):
    """Radial spark streaks."""
    objs = []
    for i in range(count):
        m, p = _make_vfx_mat("SparkMat_%d" % i, (*color, 1.0))
        ang = (2 * math.pi * i / count) + 0.35
        dy = 0.25 * math.sin(ang * 2.7)
        d = Vector((math.cos(ang), dy, 0.35 * math.sin(ang * 1.9))).normalized()
        bpy.ops.mesh.primitive_cone_add(radius1=0.035, radius2=0.005, depth=0.45,
                                        location=pos, end_fill_type='NOTHING')
        ob = bpy.context.object
        ob.name = "VFX_spark_%d_%d" % (frame, i)
        ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        ob.data.materials.append(m)
        _zero_preframe(p.inputs["Alpha"])
        _zero_preframe(p.inputs["Emission Strength"])
        _key(p.inputs["Alpha"], frame, 1.0)
        _key(p.inputs["Emission Strength"], frame, strength)
        _key(p.inputs["Alpha"], frame + dur, 0.0)
        _key(p.inputs["Emission Strength"], frame + dur, 0.0)
        ob.location = pos
        ob.keyframe_insert("location", frame=frame)
        ob.location = [pos[k] + d[k] * dist for k in range(3)]
        ob.keyframe_insert("location", frame=frame + dur)
        ob.scale = (0.0, 0.0, 0.0)
        ob.keyframe_insert("scale", frame=1)
        ob.scale = (1.0, 1.0, 1.0)
        ob.keyframe_insert("scale", frame=frame)
        ob.scale = (0.0, 0.0, 0.0)
        ob.keyframe_insert("scale", frame=frame + dur)
        objs.append(ob)
    return objs


def speedline(start, end, frame, dur=7, strength=2.5, width=0.05,
              color=(0.8, 0.9, 1.0)):
    """Motion streak along a punch path."""
    m, p = _make_vfx_mat("SpeedMat", (*color, 1.0))
    a = Vector(start); b = Vector(end)
    mid = (a + b) / 2
    L = (b - a).length
    bpy.ops.mesh.primitive_cube_add(size=1, location=mid)
    ob = bpy.context.object
    ob.name = "VFX_speed_%d" % frame
    ob.scale = (L, width, width)
    ob.rotation_euler = (b - a).to_track_quat('X', 'Z').to_euler()
    ob.data.materials.append(m)
    _zero_preframe(p.inputs["Alpha"])
    _zero_preframe(p.inputs["Emission Strength"])
    _key(p.inputs["Alpha"], frame, 0.0)
    _key(p.inputs["Emission Strength"], frame, 0.0)
    _key(p.inputs["Alpha"], frame + 2, 0.8)
    _key(p.inputs["Emission Strength"], frame + 2, strength)
    _key(p.inputs["Alpha"], frame + dur, 0.0)
    _key(p.inputs["Emission Strength"], frame + dur, 0.0)
    ob.scale = (0.0, width, width)
    ob.keyframe_insert("scale", frame=frame)
    ob.scale = (L, width, width)
    ob.keyframe_insert("scale", frame=frame + 2)
    ob.scale = (L * 1.4, 0.001, 0.001)
    ob.keyframe_insert("scale", frame=frame + dur)
    return ob


def ghost(body_pos, yaw, frame, dur=12, color=(0.6, 0.8, 1.0)):
    """Translucent afterimage silhouette (5 boxes), for dodges."""
    m, p = _make_vfx_mat("GhostMat", (*color, 1.0))
    parts = [((0, 0, 1.25), (0.55, 0.35, 1.1)),    # torso
             ((0, 0, 2.05), (0.3, 0.3, 0.35)),     # head
             ((0.45, 0, 1.6), (0.22, 0.3, 0.7)),   # arm R
             ((-0.45, 0, 1.6), (0.22, 0.3, 0.7)),  # arm L
             ((0.25, 0, 0.6), (0.2, 0.3, 1.15)),   # leg R
             ((-0.25, 0, 0.6), (0.2, 0.3, 1.15))]  # leg L
    objs = []
    for i, (off, sc) in enumerate(parts):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
        ob = bpy.context.object
        ob.name = "VFX_ghost_%d_%d" % (frame, i)
        ob.scale = sc
        ob.location = off
        ob.data.materials.append(m)
        objs.append(ob)
    # animate the whole set: rise + fade
    _zero_preframe(p.inputs["Alpha"])
    _zero_preframe(p.inputs["Emission Strength"])
    _key(p.inputs["Alpha"], frame, 0.0)
    _key(p.inputs["Emission Strength"], frame, 0.0)
    _key(p.inputs["Alpha"], frame + 2, 0.35)
    _key(p.inputs["Emission Strength"], frame + 2, 0.5)
    _key(p.inputs["Alpha"], frame + dur, 0.0)
    _key(p.inputs["Emission Strength"], frame + dur, 0.0)
    for ob in objs:
        for k in (1, frame):
            ob.location = ob.location
            ob.keyframe_insert("location", frame=k)
        ob.location = (ob.location[0], ob.location[1], ob.location[2] + 0.5)
        ob.keyframe_insert("location", frame=frame + dur)
    return objs


def dust(pos, frame, dur=14, n=4):
    """Foot-step dust puffs."""
    objs = []
    for i in range(n):
        m, p = _make_vfx_mat("DustMat_%d" % i, (0.35, 0.3, 0.28, 1.0))
        dx = (i - n / 2) * 0.18
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14,
                                             location=(pos[0] + dx, pos[1], 0.1),
                                             segments=10, ring_count=6)
        ob = bpy.context.object
        ob.name = "VFX_dust_%d_%d" % (frame, i)
        ob.data.materials.append(m)
        _zero_preframe(p.inputs["Alpha"])
        _zero_preframe(p.inputs["Emission Strength"])
        _key(p.inputs["Alpha"], frame, 0.0)
        _key(p.inputs["Alpha"], frame + 3, 0.5)
        _key(p.inputs["Alpha"], frame + dur, 0.0)
        _key(p.inputs["Emission Strength"], 1, 0.0)
        ob.location = (pos[0] + dx, pos[1], 0.1)
        ob.keyframe_insert("location", frame=frame)
        ob.location = (pos[0] + dx + 0.25, pos[1] + 0.2, 0.55)
        ob.keyframe_insert("location", frame=frame + dur)
        ob.scale = (0.0, 0.0, 0.0)
        ob.keyframe_insert("scale", frame=1)
        ob.scale = (1.0, 1.0, 1.0)
        ob.keyframe_insert("scale", frame=frame + 2)
        ob.scale = (1.8, 1.8, 1.2)
        ob.keyframe_insert("scale", frame=frame + dur)
        objs.append(ob)
    return objs


def hide_vfx_before(ob, frame):
    """Make sure an object renders as scale-0 at frame 1 (belt & braces)."""
    ob.scale = (0.0, 0.0, 0.0)
    ob.keyframe_insert("scale", frame=1)


def all_vfx_objects(scn):
    return [o for o in scn.objects if o.name.startswith("VFX_")]
