# R6 Boxing Combat — 20-Second Cinematic

A 20-second (600 frames @ 30fps) boxing-style combat scene built from the R6
character rig in `BlenderRig.zip` (`R6IK_1.blend`), animated entirely with
headless Blender 5.0.1 (`bpy` from PyPI) and rendered with Cycles CPU.

## Contents

| Path | What it is |
|---|---|
| `video/combat_boxing.mp4` | **Final video** — 720p H.264, 20s, with mixed SFX track |
| `Blender/CombatScene.blend` | Fully keyed scene (open in any Blender 5.x): fighters, arena, cameras, VFX, compositor |
| `sfx/combat_sfx.wav` | Generated sound track (48kHz mono): whiffs, hits, uppercut, KO, crowd, victory sting |
| `previews/hero_*.png` | Hero stills of the key beats |
| `Blender/*.py` | The whole procedural pipeline (rebuild the scene from scratch) |
| `Blender/setup_env.sh` | One-shot toolchain rebuild for this sandbox |

## The fight (beat map)

| Time | Beat |
|---|---|
| 0.0–1.5s | Walk-in from outside the ring, guards up |
| 1.5–3.0s | P1 feint + jabs |
| 3.0–4.5s | P1 jab-cross-hook — hook connects (f102), close-up on P2's reaction (f127) |
| 4.5–6.0s | P2 slips and counters low — body shot (f150) |
| 6.0–7.6s | P1 ducks a hook, answers with an uppercut (f207) + shockwave |
| 7.6–9.3s | P2 pushed to the ropes, big jab (f246), low-angle capture |
| 9.3–11.1s | Trade — P2's hook whiffs, P1 weaves |
| 11.1–13.1s | P1 works the body (f360/f375), P2 slows down |
| 13.1–15.0s | P2's last cross connects (f395) — then his legs give out |
| 15.0–15.9s | Reset, breathe, step in |
| 16.0–17.6s | Finisher: walk-in, feint (ghost trail f497), P1's left hook (f524) — KO, double flash + shockwave |
| 17.6–19.0s | P2 folds to the canvas, P1 turns |
| 19.0–20.0s | Victory — fist raised, wide final shot |

17 camera cuts across 7 rigs (wide, three-quarter, 60mm close-ups, top-down,
low angle, cross, final) with 11 camera shakes synced to impacts.

## VFX

All VFX is procedural (no textures): impact flashes, expanding shockwave
rings, radial sparks, punch speed-lines, a translucent dodge afterimage
(ghost), and foot-step dust.

Hard-won Blender 5 transparency notes baked into `vfx.py`:

1. Unkeyframed Principled sockets extrapolate **negative** to their default
   before the first keyframe, which renders as opaque black. Every animated
   Alpha/Emission socket gets a zero key at frame 1.
2. The alpha'd Principled BSDF is explicitly linked to the Material Output.
3. Every VFX object also scales to 0 outside its event window, so a broken
   alpha can never leave a black blob.

## SFX

`sfx.py` synthesizes the whole track with numpy (48kHz): filtered-noise
whooshes, low-sine body thumps, an uppercut riser into a heavy hit, a deep
KO boom, crowd swells, and a four-note victory sting, over a quiet crowd
ambience bed.

## Rebuilding from scratch (this sandbox)

```sh
# 1. toolchain (PyPI only; apt mirrors are blocked here)
sh combat_boxing/Blender/setup_env.sh

# 2. scene + choreography (≈20s)
LD_LIBRARY_PATH=$PWD/.stubs .blenderenv/bin/python combat_boxing/Blender/build.py

# 3. full render + encode (≈4h on 2 CPU cores, resume-safe)
LD_LIBRARY_PATH=$PWD/.stubs .blenderenv/bin/python combat_boxing/Blender/render_and_encode.py
```

## Engineering notes (bpy 5.0.1 from PyPI, headless)

- Missing X11/GL system libs are satisfied by no-op stub shared libraries in
  `.stubs/` (Cycles-CPU never calls into X/GL). The xkbcommon stub must carry
  the `V_0.5.0` symbol version, or glibc 2.36's dynamic linker asserts during
  symbol lookup.
- In this build `pose_bone.matrix` omits the armature object transform, and
  `bone.matrix_local` is stored **armature-absolute** (not parent-relative).
  The fighter API therefore evaluates its own FK chain, and the bone
  direction is the **Y column** of the rest matrix. Placement is done via the
  armature object transform so the whole character yaws rigidly.
- Compositor Glare is socket-parameterized in 5.0 (Type/Quality/Threshold/
  Size/Strength are inputs), and the group's output node is
  `NodeGroupOutput` ("Group Output"); the `Render Layers` node must be
  linked into the Glare input.
