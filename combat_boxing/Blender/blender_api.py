"""R6 fighter API for Blender 5 (headless bpy).

Rebuilt after the sandbox reset. The core pose formula below was calibrated
against this exact rig (calib5, error 0.00000 rad):

    For a fixed parent pose:   W(Q) = W0 . Q
    =>  Q = (W0^-1 @ R_target @ rest).to_quaternion()

    W0     = pb.matrix.to_3x3() measured with Q=identity (parent as-posed)
    rest   = pb.bone.matrix_local.to_3x3()   (rest local rotation)
    R_target = desired character-frame (armature-space) rotation of the bone

MC (MasterControl) location lives in the bone-local frame with mapping
    world_delta = Rx90 . loc   =>   loc = (pos.x, pos.z, -pos.y)
and the MC must land at pos + rest_root (armature origin = foot level).
A MC rotation about local Y == world-Z yaw.

Per-fighter build order MUST be root -> torso -> head -> arms -> legs
(parent posed before child).
"""
import math
import bpy
from mathutils import Vector, Matrix, Euler

DEG = math.pi / 180.0

# original rig bone names -> canonical names used by the choreography
BONE_MAP = {
    "MasterControl":  "MC",
    "Torso":          "Torso",
    "Head":           "Head",
    "LeftUpperArm":   "L_UpperArm",
    "LeftArm.002":    "L_Arm002",
    "RightUpperArm":  "R_UpperArm",
    "RightArm.002":   "R_Arm002",
    "LeftUpperLeg":   "L_UpperLeg",
    "LeftLowerLeg":   "L_LowerLeg",
    "RightUpperLeg":  "R_UpperLeg",
    "RightLowerLeg":  "R_LowerLeg",
}

# helper / IK bones that must be hidden from render (per fighter prefix)
HIDDEN_MESH_PARTS = (
    "Sphere", "Sphere.001", "Sphere.002", "Sphere.003",
    "_Shape_Bounds_Grab.001", "_Shape_Bounds_Track", "_Shape_Bounds_Track.002",
    "_Shape_Point", "Circle.001", "Circle.005",
    "Cube.005", "Cube.006", "Cube.007", "Cube.008", "Cube.009",
    "Cube.018", "Cube.019", "Cube.020", "Cube.022",
)


def _rx(a):
    return Matrix.Rotation(a, 3, 'X')


def _ry(a):
    return Matrix.Rotation(a, 3, 'Y')


def _rz(a):
    return Matrix.Rotation(a, 3, 'Z')


class Fighter:
    """One R6 fighter: armature + its mesh parts, controlled via FK."""

    def __init__(self, arm_ob, prefix="P1"):
        self.arm_ob = arm_ob
        self.prefix = prefix
        self.bones = {}
        self.mesh_objs = []

        # disable ALL constraints (IK targets, track-to, copy-location...)
        for pb in arm_ob.pose.bones:
            for c in pb.constraints:
                c.enabled = False
        # the file's loaded pose is a mid-animation frame -> unusable base.
        # clear armature animation and reset every pose bone to identity rest.
        if arm_ob.animation_data:
            arm_ob.animation_data_clear()
        for pb in arm_ob.pose.bones:
            pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
            pb.location = (0.0, 0.0, 0.0)
            pb.scale = (1.0, 1.0, 1.0)
        bpy.context.view_layer.update()
        self.rest_root = arm_ob.matrix_world.translation.copy()

        self._orig_names = {pb.bone.name for pb in arm_ob.pose.bones}
        for pb in arm_ob.pose.bones:
            if pb.bone.name in BONE_MAP:
                self.bones[BONE_MAP[pb.bone.name]] = pb

    # ------------------------------------------------------------------ pose
    def _pose_by_bone(self, bone_name):
        for pb in self.arm_ob.pose.bones:
            if pb.bone.name == bone_name:
                return pb
        return None

    def _rel_rest(self, name):
        """Parent-relative rest matrix (this build stores bone.matrix_local
        in armature-ABSOLUTE space, so convert: L_abs @ L_parent_abs^-1)."""
        b = self.bones[name].bone
        L = b.matrix_local
        if b.parent is None:
            return L
        return b.parent.matrix_local.inverted() @ L

    def _chain(self, name):
        """Armature-space (character-frame) matrix of a canonical bone,
        computed from rest + basis (does not rely on pb.matrix, which in
        this build omits the armature object transform)."""
        pb = self.bones[name]
        b = pb.bone
        if b.parent is None:
            return b.matrix_local @ pb.matrix_basis
        M_parent = self._chain(b.parent.name if b.parent.name in self._orig_names
                               else b.parent.name) if False else self._parent_chain(b)
        return M_parent @ self._rel_rest(name) @ pb.matrix_basis

    def _parent_chain(self, b):
        """Armature-space matrix of the parent bone (any rig bone)."""
        pb = self._pose_by_bone(b.parent.name)
        par = b.parent
        if par.parent is None:
            return par.matrix_local @ pb.matrix_basis
        M_grand = self._parent_chain(par)
        rel = par.parent.matrix_local.inverted() @ par.matrix_local
        return M_grand @ rel @ pb.matrix_basis

    def _set_final(self, name, R_final):
        """Set pose bone `name` so its final armature-space (character-frame)
        orientation is exactly R_final (R_final = desired char-frame rotation
        of the bone, i.e. char_pose_rot @ absolute_rest_rot). Parent poses
        are respected (W0 measured with parent as-posed). Returns Q."""
        pb = self.bones[name]
        pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        bpy.context.view_layer.update()
        W0 = self._chain(name).to_3x3()
        Q = (W0.inverted() @ R_final).to_quaternion()
        pb.rotation_quaternion = Q
        return Q

    def _rest_rot(self, name):
        return self.bones[name].bone.matrix_local.to_3x3()

    # ------------------------------------------------------------- placements
    def root(self, pos, yaw_deg=0.0):
        """Move + yaw the whole fighter rigidly, via the armature object.
        pos = world floor position (armature origin = foot level).
        Character frame == armature local space, so every bone R_target
        (character frame) rigidly follows this yaw."""
        self.arm_ob.location = (pos[0], pos[1], pos[2])
        self.arm_ob.rotation_euler = (0.0, 0.0, yaw_deg * DEG)
        mc = self.bones.get("MC")
        if mc is not None:
            mc.rotation_mode = 'QUATERNION'
            mc.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
            mc.location = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()

    @staticmethod
    def face_yaw(from_pos, to_pos):
        """Yaw (deg) that turns the rest-facing (-Y) of `from_pos` toward `to_pos`."""
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        return math.degrees(math.atan2(dx, -dy))

    def torso(self, pitch_deg=0.0, lean_deg=0.0, twist_deg=0.0):
        """pitch = forward lean (X), lean = side tilt (Z), twist = rotate (Y)."""
        R = _rx(pitch_deg * DEG) @ _rz(lean_deg * DEG) @ _ry(twist_deg * DEG)
        self._set_final("Torso", R @ self._rest_rot("Torso"))

    def head(self, pitch_deg=0.0, yaw_deg=0.0):
        R = _rx(pitch_deg * DEG) @ _ry(yaw_deg * DEG)
        self._set_final("Head", R @ self._rest_rot("Head"))

    def arm(self, side, up_deg=0.0, fwd_deg=0.0):
        """side 'L'/'R'. up = raise in the character XZ plane (about Y),
        fwd = punch forward (about X). Only the shoulder Arm002 bone moves
        (elbow stays at the side -> boxing guard look)."""
        sign = 1.0 if side == 'R' else -1.0
        R = _rx(fwd_deg * DEG) @ _ry(sign * up_deg * DEG)
        self._set_final("%s_Arm002" % side, R @ self._rest_rot("%s_Arm002" % side))

    def arm_dir(self, side, direction):
        """Point the shoulder Arm002 bone at a target direction (character
        frame, from the shoulder). Uses the minimal rotation rest_dir ->
        target, so the fist lands exactly where aimed regardless of the
        rig's baked frame twist."""
        d = Vector(direction).normalized()
        Rc = self.bones[side + "_Arm002"].bone.matrix_local.to_3x3()
        rest_dir = Vector((Rc[0][1], Rc[1][1], Rc[2][1])).normalized()
        axis = rest_dir.cross(d)
        alen = axis.length
        if alen < 1e-6:
            R = Matrix.Identity(3)
        else:
            ang = math.acos(max(-1.0, min(1.0, rest_dir.dot(d))))
            R = Matrix.Rotation(ang, 3, axis.normalized())
        self._set_final(side + "_Arm002", R @ self._rest_rot(side + "_Arm002"))

    def arm_upper(self, side, fwd_deg=0.0, up_deg=0.0):
        sign = 1.0 if side == 'R' else -1.0
        R = _rx(fwd_deg * DEG) @ _ry(sign * up_deg * DEG)
        self._set_final("%s_UpperArm" % side, R @ self._rest_rot("%s_UpperArm" % side))

    def leg(self, side, fwd_deg=0.0, out_deg=0.0, knee_deg=0.0):
        """Upper leg: fwd = stride forward (X), out = step wide (Z).
        Lower leg: knee = bend (X, negative = knee forward)."""
        sign = 1.0 if side == 'R' else -1.0
        R = _rx(fwd_deg * DEG) @ _rz(sign * out_deg * DEG)
        self._set_final("%s_UpperLeg" % side, R @ self._rest_rot("%s_UpperLeg" % side))
        self._set_final("%s_LowerLeg" % side, _rx(-knee_deg * DEG) @ self._rest_rot("%s_LowerLeg" % side))

    # ------------------------------------------------------------- shortcuts
    def guard(self, deep=1.0):
        """Boxing stance: crouch, hands up. deep 0..1 blends from rest."""
        self.torso(pitch_deg=10 * deep)
        self.head(pitch_deg=-6 * deep)
        # fists: blend rest dir -> guard dir by `deep`
        self._blend_arm_dir('R', (0.701, 0, -0.708), (-0.80, -0.28, 0.52), deep)
        self._blend_arm_dir('L', (-0.701, 0, -0.708), (-0.70, -0.20, 0.55), deep)
        self.leg('R', fwd_deg=-8 * deep, out_deg=6 * deep, knee_deg=14 * deep)
        self.leg('L', fwd_deg=8 * deep, out_deg=6 * deep, knee_deg=10 * deep)

    def _blend_arm_dir(self, side, rest, target, t):
        r = Vector(rest); tg = Vector(target).normalized()
        # slerp the direction, then point the arm at it
        ang = math.acos(max(-1.0, min(1.0, r.normalized().dot(tg))))
        if ang < 1e-6 or t <= 0.0:
            d = r.normalized()
        else:
            s = t * ang
            axis = r.normalized().cross(tg)
            R = Matrix.Rotation(s, 3, axis.normalized())
            d = (R @ r.normalized()).normalized()
        self.arm_dir(side, d)

    def reset_pose(self):
        for pb in self.arm_ob.pose.bones:
            pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
            pb.location = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()

    # ------------------------------------------------------------- querying
    def bone_point(self, name, t=0.5):
        """Point along a canonical bone (t=0 head, 1 tail) in world space.
        NOTE: in this build the bone direction is the Y column of the
        rest/pose matrices (verified against skel.txt head/tail data)."""
        M = self._chain(name)
        h = M.translation.copy()
        tl = M @ Vector((0.0, self.bones[name].bone.length * t, 0.0))
        return self.arm_ob.matrix_world @ tl

    def bone_point_local(self, name, t=0.5):
        """Point along a bone in armature (character) space (t=0 head, 1 tail)."""
        M = self._chain(name)
        return M @ Vector((0.0, self.bones[name].bone.length * t, 0.0))

    def head_world(self):
        return self.bone_point("Head", 0.35)

    def fist_world(self, side):
        return self.bone_point("%s_Arm002" % side, 1.0)
