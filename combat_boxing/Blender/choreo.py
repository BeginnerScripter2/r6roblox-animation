"""The 20-second boxing choreography (600 frames @ 30fps).

Timeline engine: a list of beats (frame + full fighter states), smoothstep
interpolated. One-shot VFX / SFX / camera-shake events on explicit frames.

Anchors carried from the pre-reset build: f102 hit, f127/f331/f524 CC 60mm,
f207 speedline, f246 shockwave at (1.57,1.5,2.85), f265 CE, f395 hit,
f478 dust, f497-507 ghost, f588 brighten, f600 CG end.
"""
import math

FPS = 30
DUR = 600

P1_HOME = (-1.1, -1.5)
P2_HOME = (1.1, 1.5)
P1_ROPE = (2.2, 2.9)    # P2 corner (P2 leans here late)
P2_ROPE = (-2.2, -2.9)


def face_yaw(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    return math.degrees(math.atan2(dx, -dy))


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_v(a, b, t):
    return tuple(lerp(a[i], b[i], t) for i in range(len(a)))


def slerp_dir(a, b, t):
    a = [x / max(1e-6, math.sqrt(sum(v * v for v in a))) for x in a]
    b = [x / max(1e-6, math.sqrt(sum(v * v for v in b))) for x in b]
    d = sum(x * y for x, y in zip(a, b))
    d = max(-1.0, min(1.0, d))
    th = math.acos(d)
    if th < 1e-4:
        return a
    sa = math.sin(th)
    w1 = math.sin((1 - t) * th) / sa
    w2 = math.sin(t * th) / sa
    return tuple(w1 * x + w2 * y for x, y in zip(a, b))


# guard fist directions (character frame, from shoulder)
GRD_R = (0.701, 0, -0.708)      # rest
GRD_GUARD_R = (-0.80, -0.28, 0.52)
GRD_GUARD_L = (-0.70, -0.20, 0.55)
JAB_R = (-0.55, -0.80, 0.20)    # right fist straight to opponent face
CROSS_L = (0.55, -0.80, 0.20)
HOOK_R = (-0.92, -0.40, 0.35)
HOOK_L = (0.92, -0.40, 0.35)
UPPER_R = (-0.55, -0.25, 0.80)
UPPER_L = (0.55, -0.25, 0.80)
BODY_R = (-0.75, -0.55, -0.35)
BODY_L = (0.75, -0.55, -0.35)
RAISED_R = (-0.15, -0.25, 0.96)  # victory fist
DOWN_R = (0.75, 0.1, -0.66)


def S(pos, yaw, guard=1.0, pitch=10, hpitch=-6, hyaw=0,
      rdir=GRD_GUARD_R, ldir=GRD_GUARD_L,
      rfwd=0, lfwd=0, legR=(0, 10), legL=(0, 8)):
    return dict(pos=pos, yaw=yaw, guard=guard, pitch=pitch, hpitch=hpitch,
                hyaw=hyaw, rdir=rdir, ldir=ldir, rfwd=rfwd, lfwd=lfwd,
                legR=legR, legL=legL)


def interp_state(a, b, t):
    t = smoothstep(t)
    out = {}
    out["pos"] = lerp_v(a["pos"], b["pos"], t)
    out["yaw"] = lerp(a["yaw"], b["yaw"], t)
    out["guard"] = lerp(a["guard"], b["guard"], t)
    out["pitch"] = lerp(a["pitch"], b["pitch"], t)
    out["hpitch"] = lerp(a["hpitch"], b["hpitch"], t)
    out["hyaw"] = lerp(a["hyaw"], b["hyaw"], t)
    out["rfwd"] = lerp(a["rfwd"], b["rfwd"], t)
    out["lfwd"] = lerp(a["lfwd"], b["lfwd"], t)
    out["rdir"] = slerp_dir(a["rdir"], b["rdir"], t)
    out["ldir"] = slerp_dir(a["ldir"], b["ldir"], t)
    out["legR"] = lerp_v(a["legR"], b["legR"], t)
    out["legL"] = lerp_v(a["legL"], b["legL"], t)
    return out


# (frame, p1_state, p2_state)
BEATS = [
    # ---------------- intro: walk in from outside the ring ----------------
    (1,   S((-4.6, -4.2), face_yaw((-4.6, -4.2), P1_HOME), guard=0, pitch=4, hpitch=0, hyaw=0,
            rdir=GRD_R, ldir=(-0.701, 0, -0.708), legR=(12, 25), legL=(-12, 20)),
           S((4.6, 4.2), face_yaw((4.6, 4.2), P2_HOME), guard=0, pitch=4, hpitch=0, hyaw=0,
            rdir=(0.701, 0, -0.708), ldir=(-0.701, 0, -0.708), legR=(12, 25), legL=(-12, 20))),
    (25,  S((-2.9, -3.0), face_yaw((-2.9, -3.0), P1_HOME), guard=0.1, pitch=5, hpitch=0, hyaw=0,
            rdir=GRD_R, ldir=(-0.701, 0, -0.708), legR=(-12, 22), legL=(12, 18)),
           S((2.9, 3.0), face_yaw((2.9, 3.0), P2_HOME), guard=0.1, pitch=5, hpitch=0, hyaw=0,
            rdir=(0.701, 0, -0.708), ldir=(-0.701, 0, -0.708), legR=(-12, 22), legL=(12, 18))),
    (45,  S(P1_HOME, face_yaw(P1_HOME, P2_HOME), guard=0.55, pitch=8, hpitch=-4, hyaw=0,
            rdir=GRD_R, ldir=(-0.701, 0, -0.708), legR=(-6, 14), legL=(6, 12)),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME), guard=0.55, pitch=8, hpitch=-4, hyaw=0,
            rdir=(0.701, 0, -0.708), ldir=(-0.701, 0, -0.708), legR=(-6, 14), legL=(6, 12))),
    # ---------------- raise guards, square up ----------------
    (60,  S(P1_HOME, face_yaw(P1_HOME, P2_HOME)),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME))),
    # ---------------- P1 feint + jab ----------------
    (70,  S((-1.15, -1.62), face_yaw(P1_HOME, P2_HOME), pitch=16, hpitch=-4, hyaw=-4,
            rdir=(-0.35, -0.72, 0.35), rfwd=14),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME))),
    (78,  S((-1.1, -1.5), face_yaw(P1_HOME, P2_HOME), pitch=20, hpitch=-2, hyaw=-6,
            rdir=JAB_R, rfwd=30, legR=(-4, 12), legL=(8, 8)),
           S((1.16, 1.56), face_yaw(P2_HOME, P1_HOME) + 4, pitch=6, hpitch=2, hyaw=6,
            guard=1.0)),
    (88,  S(P1_HOME, face_yaw(P1_HOME, P2_HOME)),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME))),
    # ---------------- P1 combo: jab-cross-hook, hook connects f102 ----------------
    (96,  S((-1.05, -1.6), face_yaw(P1_HOME, P2_HOME), pitch=18, hyaw=-4, rdir=JAB_R, rfwd=24),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME))),
    (102, S((-0.95, -1.72), face_yaw(P1_HOME, P2_HOME) - 6, pitch=24, hyaw=-8,
            rdir=JAB_R, rfwd=40, legR=(-8, 14), legL=(12, 8)),
           S((1.2, 1.6), face_yaw(P2_HOME, P1_HOME) + 10, pitch=-6, hpitch=14, hyaw=-10,
            rdir=(0.5, 0.1, 0.75), ldir=GRD_GUARD_L)),
    (112, S((-1.0, -1.66), face_yaw(P1_HOME, P2_HOME) - 8, pitch=26, hyaw=-10,
            rdir=JAB_R, rfwd=36),
           S((1.26, 1.66), face_yaw(P2_HOME, P1_HOME) + 16, pitch=-10, hpitch=18, hyaw=-14,
            rdir=(0.55, 0.15, 0.7), ldir=GRD_GUARD_L)),
    (118, S((-0.9, -1.75), face_yaw(P1_HOME, P2_HOME) - 14, pitch=28, hyaw=-14,
            rdir=HOOK_R, rfwd=30, legR=(-10, 16), legL=(14, 10)),
           S((1.3, 1.7), face_yaw(P2_HOME, P1_HOME) + 22, pitch=-12, hpitch=22, hyaw=-20,
            rdir=(0.6, 0.2, 0.65), ldir=GRD_GUARD_L)),
    (130, S((-0.98, -1.68), face_yaw(P1_HOME, P2_HOME) - 8, pitch=20, hyaw=-8, rdir=HOOK_R, rfwd=20),
           S((1.24, 1.62), face_yaw(P2_HOME, P1_HOME) + 12, pitch=-8, hpitch=12, hyaw=-10,
            rdir=(0.5, 0.1, 0.75), ldir=GRD_GUARD_L)),
    (142, S(P1_HOME, face_yaw(P1_HOME, P2_HOME)),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME))),
    # ---------------- P2 counter: slip + body jab (hits f150) ----------------
    (152, S((-1.02, -1.52), face_yaw(P1_HOME, P2_HOME) - 8, pitch=4, hpitch=8, hyaw=10,
            guard=0.9, rdir=(0.6, 0.2, 0.6), ldir=GRD_GUARD_L),
           S((0.98, 1.42), face_yaw(P2_HOME, P1_HOME) - 12, pitch=22, hyaw=8,
            rdir=CROSS_L, lfwd=34, legR=(-6, 12), legL=(10, 8))),
    (160, S((-1.04, -1.54), face_yaw(P1_HOME, P2_HOME) - 10, pitch=0, hpitch=10, hyaw=12,
            guard=0.85, rdir=(0.65, 0.25, 0.55), ldir=GRD_GUARD_L),
           S((0.92, 1.36), face_yaw(P2_HOME, P1_HOME) - 16, pitch=26, hyaw=10,
            rdir=CROSS_L, lfwd=40, legR=(-8, 14), legL=(12, 8))),
    (172, S((-1.0, -1.5), face_yaw(P1_HOME, P2_HOME) - 4, pitch=8, hpitch=2, hyaw=4),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME))),
    # ---------------- P1 duck-dodge + uppercut (connects f207) ----------------
    (185, S(P1_HOME, face_yaw(P1_HOME, P2_HOME)),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME), pitch=14, hyaw=-4, rdir=(0.85, -0.35, 0.4), rfwd=16)),
    (196, S((-1.28, -1.78), face_yaw(P1_HOME, P2_HOME) - 6, pitch=34, hpitch=-16, hyaw=6,
            guard=1.0, rdir=GRD_GUARD_R, ldir=GRD_GUARD_L, legR=(-14, 26), legL=(10, 24)),
           S((1.2, 1.6), face_yaw(P2_HOME, P1_HOME) - 10, pitch=30, hyaw=-12,
            rdir=HOOK_L, lfwd=44, legR=(-10, 18), legL=(14, 12))),
    (203, S((-1.1, -1.55), face_yaw(P1_HOME, P2_HOME) - 4, pitch=18, hpitch=4, hyaw=4,
            rdir=UPPER_R, rfwd=30, legR=(-6, 18), legL=(10, 14)),
           S((1.28, 1.68), face_yaw(P2_HOME, P1_HOME) - 14, pitch=34, hyaw=-14,
            rdir=HOOK_L, lfwd=46, legR=(-12, 20), legL=(16, 14))),
    (209, S((-1.0, -1.45), face_yaw(P1_HOME, P2_HOME), pitch=10, hpitch=8, hyaw=2,
            rdir=UPPER_R, rfwd=24, legR=(-4, 14), legL=(8, 12)),
           S((1.42, 1.78), face_yaw(P2_HOME, P1_HOME) - 18, pitch=-18, hpitch=26, hyaw=-22,
            rdir=(0.7, 0.3, 0.55), ldir=(0.2, 0.3, 0.9), legR=(-14, 22), legL=(14, 20))),
    (222, S((-1.04, -1.52), face_yaw(P1_HOME, P2_HOME), pitch=8, hpitch=4,
            rdir=GRD_GUARD_R, ldir=GRD_GUARD_L),
           S((1.4, 1.74), face_yaw(P2_HOME, P1_HOME) - 12, pitch=-10, hpitch=14, hyaw=-12,
            rdir=(0.6, 0.2, 0.7), ldir=(0.1, 0.2, 0.95))),
    # ---------------- P1 pressure: P2 to ropes, big jab f246 ----------------
    (238, S((-0.85, -1.3), face_yaw((-0.85, -1.3), P1_ROPE) + 8, pitch=12, hyaw=-4,
            rdir=(-0.4, -0.75, 0.35), rfwd=10),
           S((1.5, 1.9), face_yaw((1.5, 1.9), P1_ROPE) - 14, pitch=-6, hpitch=10, hyaw=-8,
            guard=1.0, rdir=(0.6, 0.25, 0.65), ldir=GRD_GUARD_L)),
    (246, S((-0.72, -1.12), face_yaw((-0.72, -1.12), (1.57, 1.5)), pitch=24, hyaw=-6,
            rdir=(-0.3, -0.85, 0.3), rfwd=38, legR=(-8, 14), legL=(12, 10)),
           S((1.62, 1.98), face_yaw((1.62, 1.98), P1_ROPE) - 20, pitch=-12, hpitch=16, hyaw=-16,
            rdir=(0.65, 0.3, 0.6), ldir=GRD_GUARD_L, legR=(-12, 20), legL=(12, 18))),
    (258, S((-0.8, -1.22), face_yaw((-0.8, -1.22), P1_ROPE) + 4, pitch=12, hyaw=-4),
           S((1.58, 1.94), face_yaw((1.58, 1.94), P1_ROPE) - 16, pitch=-8, hpitch=10, hyaw=-12,
            rdir=(0.6, 0.25, 0.65), ldir=GRD_GUARD_L)),
    (274, S(P1_HOME, face_yaw(P1_HOME, P2_HOME)),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME))),
    # ---------------- trade: P2 hook whiffs, P1 weaves ----------------
    (290, S((-1.1, -1.5), face_yaw(P1_HOME, P2_HOME)),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME), pitch=16, hyaw=-4, rdir=(0.85, -0.35, 0.4), rfwd=14)),
    (302, S((-1.24, -1.62), face_yaw(P1_HOME, P2_HOME) + 10, pitch=30, hpitch=-14, hyaw=-14,
            guard=1.0, legR=(-12, 26), legL=(8, 24)),
           S((1.16, 1.42), face_yaw(P2_HOME, P1_HOME) - 12, pitch=32, hyaw=-14,
            rdir=HOOK_L, lfwd=46, legR=(-10, 18), legL=(14, 14))),
    (312, S((-1.05, -1.42), face_yaw(P1_HOME, P2_HOME) + 6, pitch=14, hpitch=-4, hyaw=-8,
            rdir=GRD_GUARD_R, ldir=GRD_GUARD_L),
           S((1.2, 1.5), face_yaw(P2_HOME, P1_HOME) - 10, pitch=26, hyaw=-10,
            rdir=HOOK_L, lfwd=30, legR=(-10, 16), legL=(14, 14))),
    (326, S(P1_HOME, face_yaw(P1_HOME, P2_HOME)),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME), pitch=6, hpitch=4, hyaw=-4, guard=0.95)),
    # ---------------- P1 works the body ----------------
    (338, S((-1.0, -1.4), face_yaw((-1.0, -1.4), P2_HOME) + 6, pitch=18, hyaw=-4,
            rdir=GRD_GUARD_R, rfwd=8),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME), pitch=4, hpitch=6, guard=0.95, hyaw=4)),
    (348, S((-0.88, -1.28), face_yaw((-0.88, -1.28), P2_HOME) + 8, pitch=34, hpitch=-8, hyaw=-8,
            rdir=BODY_R, rfwd=28, legR=(-8, 16), legL=(10, 12)),
           S((1.16, 1.44), face_yaw(P2_HOME, P1_HOME) + 6, pitch=8, hpitch=14, hyaw=-6,
            guard=0.8, rdir=(0.55, 0.15, 0.7), ldir=GRD_GUARD_L)),
    (360, S((-0.8, -1.16), face_yaw((-0.8, -1.16), P2_HOME) + 12, pitch=38, hpitch=-10, hyaw=-10,
            rdir=BODY_R, rfwd=36, legR=(-10, 18), legL=(12, 12)),
           S((1.24, 1.5), face_yaw(P2_HOME, P1_HOME) + 8, pitch=12, hpitch=18, hyaw=-8,
            guard=0.75, rdir=(0.6, 0.2, 0.65), ldir=GRD_GUARD_L)),
    (372, S((-0.86, -1.24), face_yaw((-0.86, -1.24), P2_HOME) + 10, pitch=36, hpitch=-8, hyaw=-8,
            rdir=BODY_L, lfwd=30, legR=(-8, 16), legL=(12, 14)),
           S((1.28, 1.54), face_yaw(P2_HOME, P1_HOME) + 6, pitch=10, hpitch=14, hyaw=-4,
            guard=0.75, rdir=(0.55, 0.15, 0.7), ldir=(0.2, 0.2, 0.9))),
    (384, S((-0.92, -1.32), face_yaw((-0.92, -1.32), P2_HOME) + 6, pitch=20, hpitch=0, hyaw=-4),
           S((1.2, 1.46), face_yaw(P2_HOME, P1_HOME), pitch=2, hpitch=8, hyaw=0,
            guard=0.7, rdir=(0.5, 0.1, 0.8), ldir=(0.1, 0.1, 0.95))),
    (394, S(P1_HOME, face_yaw(P1_HOME, P2_HOME), pitch=8, hpitch=2, guard=0.9),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME), pitch=0, hpitch=4, guard=0.75)),
    # ---------------- P2's last cross hits f395, then his legs give ----------------
    (400, S((-1.16, -1.6), face_yaw(P1_HOME, P2_HOME) - 10, pitch=-6, hpitch=12, hyaw=12,
            rdir=(0.6, 0.25, 0.6), ldir=GRD_GUARD_L, guard=0.85),
           S((0.98, 1.4), face_yaw(P2_HOME, P1_HOME) - 12, pitch=26, hyaw=8,
            rdir=CROSS_L, lfwd=38, legR=(-8, 14), legL=(12, 10))),
    (408, S((-1.24, -1.68), face_yaw(P1_HOME, P2_HOME) - 14, pitch=-12, hpitch=16, hyaw=14,
            rdir=(0.65, 0.3, 0.55), ldir=GRD_GUARD_L, guard=0.8, legR=(-8, 20), legL=(6, 18)),
           S((0.9, 1.3), face_yaw(P2_HOME, P1_HOME) - 14, pitch=30, hyaw=10,
            rdir=CROSS_L, lfwd=42, legR=(-10, 16), legL=(14, 12))),
    (420, S((-1.2, -1.62), face_yaw(P1_HOME, P2_HOME) - 8, pitch=-4, hpitch=8, hyaw=6,
            rdir=(0.6, 0.2, 0.65), ldir=GRD_GUARD_L, guard=0.85, legR=(-6, 18), legL=(8, 16)),
           S((1.0, 1.42), face_yaw(P2_HOME, P1_HOME) - 18, pitch=-8, hpitch=14, hyaw=-16,
            rdir=(0.6, 0.2, 0.7), ldir=(0.15, 0.25, 0.9), guard=0.7, legR=(-12, 24), legL=(10, 22))),
    (434, S((-1.3, -1.72), face_yaw(P1_HOME, P2_HOME) - 4, pitch=-2, hpitch=6, hyaw=4,
            rdir=(0.55, 0.15, 0.7), ldir=GRD_GUARD_L, guard=0.8, legR=(-4, 18), legL=(6, 16)),
           S((1.06, 1.5), face_yaw(P2_HOME, P1_HOME) - 20, pitch=-10, hpitch=16, hyaw=-18,
            rdir=(0.6, 0.2, 0.7), ldir=(0.1, 0.2, 0.95), guard=0.65,
            legR=(-14, 28), legL=(8, 26))),
    # ---------------- reset: breathe, step back to center ----------------
    (452, S(P1_HOME, face_yaw(P1_HOME, P2_HOME), pitch=12, hpitch=-2, guard=0.9),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME), pitch=4, hpitch=10, guard=0.7)),
    (470, S(P1_HOME, face_yaw(P1_HOME, P2_HOME), pitch=8, hpitch=-4, guard=1.0),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME), pitch=0, hpitch=8, guard=0.7,
            rdir=(0.5, 0.1, 0.8), ldir=(0.1, 0.1, 0.95))),
    (480, S(P1_HOME, face_yaw(P1_HOME, P2_HOME)),
           S(P2_HOME, face_yaw(P2_HOME, P1_HOME), pitch=2, hpitch=8, guard=0.72)),
    # ---------------- finisher: walk-in, feint (ghost), LEFT HOOK f524 ----------------
    (492, S((-0.7, -1.05), face_yaw((-0.7, -1.05), P1_ROPE) + 10, pitch=14, hyaw=-4,
            rdir=GRD_GUARD_R, ldir=GRD_GUARD_L, rfwd=6),
           S((1.7, 2.05), face_yaw((1.7, 2.05), P1_ROPE) - 18, pitch=-6, hpitch=12, hyaw=-14,
            guard=0.7, rdir=(0.6, 0.25, 0.6), ldir=GRD_GUARD_L)),
    (505, S((-0.55, -0.85), face_yaw((-0.55, -0.85), P1_ROPE) + 14, pitch=24, hpitch=-6, hyaw=-8,
            rdir=GRD_GUARD_R, ldir=GRD_GUARD_L, rfwd=16, lfwd=10),
           S((1.82, 2.15), face_yaw((1.82, 2.15), P1_ROPE) - 22, pitch=-8, hpitch=14, hyaw=-18,
            guard=0.65, rdir=(0.6, 0.25, 0.6), ldir=GRD_GUARD_L, legR=(-10, 22), legL=(8, 20))),
    (516, S((-0.5, -0.78), face_yaw((-0.5, -0.78), P1_ROPE) + 10, pitch=30, hpitch=-8, hyaw=-10,
            rdir=GRD_GUARD_R, ldir=GRD_GUARD_L, rfwd=20),
           S((1.9, 2.22), face_yaw((1.9, 2.22), P1_ROPE) - 24, pitch=-10, hpitch=14, hyaw=-20,
            guard=0.6, rdir=(0.62, 0.28, 0.58), ldir=GRD_GUARD_L, legR=(-12, 24), legL=(10, 22))),
    (524, S((-0.42, -0.68), face_yaw((-0.42, -0.68), P1_ROPE) - 18, pitch=38, hpitch=-12, hyaw=-24,
            rdir=GRD_GUARD_R, ldir=HOOK_L, lfwd=52, legR=(-14, 20), legL=(16, 14)),
           S((2.05, 2.35), face_yaw((2.05, 2.35), P1_ROPE) + 14, pitch=-20, hpitch=28, hyaw=24,
            rdir=(0.7, 0.35, 0.5), ldir=(0.3, 0.4, 0.85), guard=0.5,
            legR=(-16, 26), legL=(14, 24))),
    # ---------------- KO: P2 folds ----------------
    (536, S((-0.46, -0.74), face_yaw((-0.46, -0.74), P1_ROPE) - 14, pitch=20, hpitch=-6, hyaw=-12,
            rdir=GRD_GUARD_R, ldir=GRD_GUARD_L),
           S((2.2, 2.5), face_yaw((2.2, 2.5), P1_ROPE) + 40, pitch=-40, hpitch=48, hyaw=48,
            rdir=(0.75, 0.5, 0.3), ldir=(0.4, 0.55, 0.7), guard=0.4,
            legR=(-18, 40), legL=(16, 38))),
    (550, S((-0.5, -0.8), face_yaw((-0.5, -0.8), P1_ROPE) - 8, pitch=10, hpitch=-4,
            rdir=GRD_GUARD_R, ldir=GRD_GUARD_L),
           S((2.4, 2.62), face_yaw((2.4, 2.62), P1_ROPE) + 70, pitch=-64, hpitch=70, hyaw=60,
            rdir=(0.8, 0.6, 0.15), ldir=(0.5, 0.7, 0.45), guard=0.3,
            legR=(-16, 52), legL=(14, 50))),
    (566, S((-0.52, -0.84), face_yaw((-0.52, -0.84), P1_ROPE) - 4, pitch=8, hpitch=-2,
            rdir=GRD_GUARD_R, ldir=GRD_GUARD_L),
           S((2.52, 2.7), face_yaw((2.52, 2.7), P1_ROPE) + 95, pitch=-82, hpitch=84, hyaw=70,
            rdir=(0.85, 0.7, 0.1), ldir=(0.6, 0.75, 0.35), guard=0.2,
            legR=(-12, 60), legL=(10, 58))),
    # ---------------- victory: P1 raises fist ----------------
    (580, S((-0.4, -0.66), face_yaw((-0.4, -0.66), (2.4, 2.6)), pitch=2, hpitch=6,
            rdir=RAISED_R, rfwd=8, ldir=GRD_GUARD_L, guard=0.6, legR=(-4, 10), legL=(4, 8)),
           S((2.52, 2.7), face_yaw((2.52, 2.7), P1_ROPE) + 95, pitch=-84, hpitch=84, hyaw=70,
            rdir=(0.85, 0.7, 0.1), ldir=(0.6, 0.75, 0.35), guard=0.2,
            legR=(-12, 60), legL=(10, 58))),
    (592, S((-0.38, -0.62), face_yaw((-0.38, -0.62), (2.4, 2.6)), pitch=0, hpitch=10,
            rdir=RAISED_R, rfwd=6, ldir=GRD_GUARD_L, guard=0.5, legR=(-2, 6), legL=(2, 5)),
           S((2.52, 2.7), face_yaw((2.52, 2.7), P1_ROPE) + 95, pitch=-84, hpitch=84, hyaw=70,
            rdir=(0.85, 0.7, 0.1), ldir=(0.6, 0.75, 0.35), guard=0.2,
            legR=(-12, 60), legL=(10, 58))),
    (600, S((-0.36, -0.6), face_yaw((-0.36, -0.6), (2.4, 2.6)), pitch=0, hpitch=12,
            rdir=RAISED_R, rfwd=4, ldir=GRD_GUARD_L, guard=0.5, legR=(-2, 4), legL=(2, 4)),
           S((2.52, 2.7), face_yaw((2.52, 2.7), P1_ROPE) + 95, pitch=-84, hpitch=84, hyaw=70,
            rdir=(0.85, 0.7, 0.1), ldir=(0.6, 0.75, 0.35), guard=0.2,
            legR=(-12, 60), legL=(10, 58))),
]

# camera cuts: (frame, cam_name, lens_override)
CUTS = [
    (1, "CA", None),
    (46, "CB", None),
    (90, "CB", None),
    (104, "CA", None),
    (127, "CC", 60),
    (140, "CC", None),
    (180, "CE", None),
    (209, "CA", None),
    (231, "CB", None),
    (265, "CE", None),
    (281, "CF", None),
    (331, "CC", 60),
    (352, "CB", None),
    (396, "CA", None),
    (411, "CD", None),
    (451, "CF", None),
    (481, "CB", None),
    (505, "CC", 60),
    (525, "CG", None),
    (561, "CG", None),
]

# camera shake: (frame, amplitude) — damped ~14 frames
SHAKES = [
    (78, 0.5), (102, 1.6), (150, 1.3), (207, 2.2), (246, 1.9),
    (302, 0.9), (360, 1.1), (375, 1.1), (395, 1.8), (524, 3.4),
    (540, 2.4),
]

# VFX one-shots: (frame, kind, args)
VFX_EVENTS = [
    (58, "speedline", dict(start=(-0.4, -0.9, 3.3), end=(0.9, 0.5, 3.4), dur=6, strength=2.5)),
    (66, "speedline", dict(start=(-0.4, -0.9, 3.3), end=(0.9, 0.5, 3.4), dur=6, strength=2.5)),
    (102, "flash", dict(pos=(1.32, 1.62, 4.0), strength=8, dur=5)),
    (102, "sparks", dict(pos=(1.32, 1.62, 4.0), count=10, dist=0.9, dur=9)),
    (150, "flash", dict(pos=(-0.98, -1.44, 2.9), strength=5, dur=5)),
    (150, "sparks", dict(pos=(-0.98, -1.44, 2.9), count=10, dist=0.8, dur=9)),
    (203, "speedline", dict(start=(-1.0, -1.5, 2.6), end=(0.4, -0.2, 4.3), dur=6, strength=2.5)),
    (207, "flash", dict(pos=(1.2, 1.5, 4.2), strength=7, dur=6)),
    (207, "shockwave", dict(pos=(1.2, 1.5, 3.0), r0=1.6, r1=3.5, dur=9, strength=2.0)),
    (246, "flash", dict(pos=(1.57, 1.5, 4.0), strength=8, dur=5)),
    (246, "shockwave", dict(pos=(1.57, 1.5, 2.85), r0=1.6, r1=3.5, dur=9, strength=2.0)),
    (246, "sparks", dict(pos=(1.57, 1.5, 4.0), count=12, dist=1.0, dur=9)),
    (302, "speedline", dict(start=(1.0, 1.3, 3.4), end=(-0.8, -0.6, 3.6), dur=6, strength=2.5)),
    (360, "flash", dict(pos=(1.14, 1.36, 2.7), strength=5, dur=5)),
    (375, "flash", dict(pos=(1.18, 1.4, 2.7), strength=5, dur=5)),
    (395, "flash", dict(pos=(-1.1, -1.5, 4.0), strength=6, dur=5)),
    (395, "sparks", dict(pos=(-1.1, -1.5, 4.0), count=10, dist=0.9, dur=9)),
    (425, "dust", dict(pos=(1.05, 1.46, 0.2), dur=14)),
    (478, "dust", dict(pos=(0.2, 0.2, 0.2), dur=14)),
    (497, "ghost", dict(body_pos=P1_HOME, yaw=0, dur=12)),
    (524, "flash", dict(pos=(1.95, 2.25, 4.1), strength=10, dur=8)),
    (524, "flash", dict(pos=(1.95, 2.25, 2.9), strength=7, dur=8)),
    (524, "shockwave", dict(pos=(1.95, 2.25, 2.85), r0=1.6, r1=3.5, dur=10, strength=2.5)),
    (524, "sparks", dict(pos=(1.95, 2.25, 4.1), count=14, dist=1.3, dur=11)),
    (540, "dust", dict(pos=(2.3, 2.5, 0.2), dur=16)),
]

# SFX one-shots: (frame, kind)
SFX_EVENTS = [
    (8, "footstep"), (16, "footstep"), (24, "footstep"), (32, "footstep"), (40, "footstep"),
    (58, "whiff"), (66, "whiff"),
    (78, "whiff"), (86, "whiff"),
    (96, "whiff"), (102, "hit_heavy"),
    (110, "whiff"), (118, "hit_light"),
    (150, "hit_body"),
    (196, "whiff"), (207, "uppercut"),
    (246, "hit_heavy"),
    (290, "whiff"), (302, "whiff"),
    (348, "hit_body"), (360, "hit_body"), (375, "hit_body"),
    (400, "whiff"), (395, "hit_heavy"),
    (428, "crowd"),
    (478, "footstep"),
    (524, "ko"),
    (540, "thud"),
    (556, "crowd"),
    (580, "victory"),
]
