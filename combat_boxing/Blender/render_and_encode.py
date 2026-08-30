"""Render all 600 frames at 720p, encode H.264 with SFX, copy hero previews.

Run headless:
  LD_LIBRARY_PATH=<repo>/.stubs <repo>/.blenderenv/bin/python render_and_encode.py
"""
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy

import choreo
import build

REPO = "/home/user/r6roblox-animation"
BLEND = os.path.join(REPO, "combat_boxing/Blender/CombatScene.blend")
FRAMES = os.path.join(REPO, "combat_boxing/.work/frames")
OUT_MP4 = os.path.join(REPO, "combat_boxing/video/combat_boxing.mp4")
PREVIEWS = os.path.join(REPO, "combat_boxing/previews")
SFX_WAV = os.path.join(REPO, "combat_boxing/sfx/combat_sfx.wav")
FFMPEG = "/home/user/r6roblox-animation/.blenderenv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
HERO_FRAMES = (30, 78, 102, 127, 150, 207, 246, 302, 360, 395, 420, 524, 550, 592)


def main():
    os.makedirs(FRAMES, exist_ok=True)
    os.makedirs(os.path.dirname(OUT_MP4), exist_ok=True)
    os.makedirs(PREVIEWS, exist_ok=True)

    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scn = bpy.context.scene
    scn.render.resolution_x = 1280
    scn.render.resolution_y = 720
    scn.render.resolution_percentage = 100
    scn.cycles.device = 'CPU'
    scn.cycles.samples = 16
    scn.cycles.use_adaptive_sampling = True
    scn.cycles.adaptive_threshold = 0.08
    scn.cycles.use_denoising = True
    scn.cycles.max_bounces = 4
    scn.cycles.diffuse_bounces = 2
    scn.cycles.glossy_bounces = 2
    scn.cycles.transmission_bounces = 2
    scn.cycles.transparent_max_bounces = 8
    scn.cycles.volume_bounces = 0
    scn.frame_set(1)

    t0 = time.time()
    for f in range(1, choreo.DUR + 1):
        cam, _lens = build.active_cut(f)
        scn.camera = bpy.data.objects[cam]
        scn.frame_set(f)
        out = os.path.join(FRAMES, "frame_%04d.png" % f)
        if os.path.exists(out) and os.path.getsize(out) > 10000:
            continue  # resume-safe
        scn.render.filepath = out
        bpy.ops.render.render(write_still=True)
        if f % 25 == 0:
            el = time.time() - t0
            avg = el / f
            print("RENDER %d/600 avg %.1fs eta %d min" % (f, avg, int(avg * (600 - f) / 60)), flush=True)

    # encode
    print("ENCODING...", flush=True)
    cmd = [FFMPEG, "-y", "-framerate", "30", "-i",
           os.path.join(FRAMES, "frame_%04d.png"),
           "-i", SFX_WAV,
           "-c:v", "libx264", "-preset", "slow", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-shortest", "-movflags", "+faststart", OUT_MP4]
    subprocess.run(cmd, check=True)
    print("ENCODED %s" % OUT_MP4, flush=True)

    # hero previews
    for f in HERO_FRAMES:
        src = os.path.join(FRAMES, "frame_%04d.png" % f)
        dst = os.path.join(PREVIEWS, "hero_%03d.png" % f)
        if os.path.exists(src):
            shutil.copyfile(src, dst)
    print("ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
