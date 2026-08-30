"""Build the full CombatScene: fighters + arena + choreography keyframes +
VFX + cameras/cuts/shakes. Saves combat_boxing/Blender/CombatScene.blend.

Run:  LD_LIBRARY_PATH=<repo>/.stubs <repo>/.blenderenv/bin/python build.py
"""
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy

import blender_api as api
import scene_build as sb
import choreo
import vfx

REPO = "/home/user/r6roblox-animation"
BLEND_OUT = os.path.join(REPO, "combat_boxing/Blender/CombatScene.blend")
CANON = ("MC", "Torso", "Head", "L_UpperArm", "R_UpperArm",
         "L_Arm002", "R_Arm002", "L_UpperLeg", "R_UpperLeg",
         "L_LowerLeg", "R_LowerLeg")


def pose_fighter(f, st):
    """Apply a beat state to a fighter (parents before children!)."""
    f.root((st["pos"][0], st["pos"][1], 0.0), st["yaw"])
    f.torso(pitch_deg=st["pitch"])
    f.head(pitch_deg=st["hpitch"], yaw_deg=st["hyaw"])
    if st["rfwd"]:
        f.arm_upper("R", fwd_deg=st["rfwd"])
    if st["lfwd"]:
        f.arm_upper("L", fwd_deg=st["lfwd"])
    f.arm_dir("R", st["rdir"])
    f.arm_dir("L", st["ldir"])
    f.leg("R", fwd_deg=st["legR"][0], knee_deg=st["legR"][1])
    f.leg("L", fwd_deg=st["legL"][0], knee_deg=st["legL"][1])


def keyframe_fighter(f, frame):
    f.arm_ob.keyframe_insert("location", frame=frame)
    f.arm_ob.keyframe_insert("rotation_euler", frame=frame)
    for bn in CANON:
        pb = f.bones[bn]
        pb.keyframe_insert("rotation_quaternion", frame=frame)


def state_at(beats, frame):
    if frame <= beats[0][0]:
        return beats[0][1], beats[0][2]
    for i in range(len(beats) - 1):
        f0, a1, a2 = beats[i]
        f1, b1, b2 = beats[i + 1]
        if frame <= f1:
            t = (frame - f0) / max(1, (f1 - f0))
            return choreo.interp_state(a1, b1, t), choreo.interp_state(a2, b2, t)
    return beats[-1][1], beats[-1][2]


def shake_offset(frame):
    """Sum of damped sine shakes active at `frame` -> (dx, dz)."""
    dx = dz = 0.0
    for sf, amp in choreo.SHAKES:
        d = frame - sf
        if 0 <= d < 16:
            k = amp * math.exp(-d / 4.0)
            t = d / 30.0
            dx += k * (math.sin(2 * math.pi * 11.3 * t) * 0.6 +
                       math.sin(2 * math.pi * 6.7 * t + 1.7) * 0.5) * 0.06
            dz += k * (math.sin(2 * math.pi * 13.1 * t + 0.8) * 0.5 +
                       math.cos(2 * math.pi * 8.9 * t) * 0.5) * 0.05
    return dx, dz


def active_cut(frame):
    cur = (choreo.CUTS[0][1], choreo.CUTS[0][2])
    for cf, name, lens in choreo.CUTS:
        if cf <= frame:
            cur = (name, lens)
        else:
            break
    return cur


def main():
    t0 = time.time()
    f1, f2, scn = sb.build_fighters()
    sb.build_arena(scn)
    sb.build_lights(scn)
    sb.build_cameras(scn)
    sb.build_compositor(scn)
    sb.render_settings(scn, res=(1280, 720), samples=32)
    print("scene built in %.1fs" % (time.time() - t0), flush=True)

    # --- keyframe camera cuts (lens) + shake (location), all frames ---
    for cam in sb.CAMERAS:
        co = bpy.data.objects[cam]
        co.data.keyframe_insert("lens", frame=1)
        base = co.location
        for frame in range(1, choreo.DUR + 1):
            _, lens = active_cut(frame)
            if lens:
                co.data.lens = lens
            else:
                co.data.lens = sb.CAMERAS[cam][1]
            co.data.keyframe_insert("lens", frame=frame)
            dx, dz = shake_offset(frame)
            co.location = (base[0] + dx, base[1], base[2] + dz)
            co.keyframe_insert("location", frame=frame)
    print("cameras keyed in %.1fs" % (time.time() - t0), flush=True)

    # --- keyframe fighters, all 600 frames ---
    t1 = time.time()
    for frame in range(1, choreo.DUR + 1):
        s1, s2 = state_at(choreo.BEATS, frame)
        pose_fighter(f1, s1)
        pose_fighter(f2, s2)
        keyframe_fighter(f1, frame)
        keyframe_fighter(f2, frame)
        if frame % 60 == 0:
            print("pose %d/600 (%.1fs)" % (frame, time.time() - t1), flush=True)
    print("fighters keyed in %.1fs" % (time.time() - t1), flush=True)

    # --- aim the CC close-up at the featured fighter's head ---
    from mathutils import Vector
    cc = bpy.data.objects["CC"]
    cc_windows = [(127, 139, f2), (331, 340, f1), (505, 516, f1), (524, 536, f2)]
    for ws, we, feat in cc_windows:
        for fr in range(ws, we + 1):
            scn.frame_set(fr)
            h = feat.head_world()
            behind = (h - Vector(cc.location)).normalized()
            tgt = h + behind * 0.38
            d = tgt - Vector(cc.location)
            cc.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
            cc.keyframe_insert("rotation_euler", frame=fr)
    print("cc close-ups aimed", flush=True)

    # --- VFX (impact flashes/sparks land on the receiver's actual head) ---
    t2 = time.time()
    impact_receiver = {102: f2, 150: f1, 207: f2, 246: f2, 395: f1, 524: f2}
    impact_attacker = {102: f1, 150: f2, 207: f1, 246: f1, 395: f2, 524: f1}
    for frame, kind, args in choreo.VFX_EVENTS:
        args = dict(args)
        if frame in impact_receiver and kind in ("flash", "sparks"):
            scn.frame_set(max(1, frame - 1))
            h = impact_receiver[frame].head_world()
            fist = impact_attacker[frame].fist_world("L") if frame in (150, 524) \
                else impact_attacker[frame].fist_world("R")
            off = (Vector(fist) - Vector(h))
            if off.length > 1e-4:
                h = h + off.normalized() * 0.33
            args["pos"] = (h.x, h.y, h.z)
        getattr(vfx, kind)(frame=frame, **args)
    nv = len(vfx.all_vfx_objects(scn))
    print("vfx: %d objects in %.1fs" % (nv, time.time() - t2), flush=True)

    # --- default camera + save ---
    scn.camera = bpy.data.objects["CA"]
    scn.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    print("saved %s (total %.1fs)" % (BLEND_OUT, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
