"""SFX: numpy, 48kHz, 20s. Event times t = frame / 30 (choreo.SFX_EVENTS)."""
import math
import os
import wave

import numpy as np

SR = 48000
DUR = 20.0
OUT = "/home/user/r6roblox-animation/combat_boxing/sfx/combat_sfx.wav"


def _env(n, tau):
    return np.exp(-np.arange(n, dtype=np.float64) / max(1e-6, tau * SR))


def _sine(freq, n, f_end=None):
    t = np.arange(n) / SR
    if f_end:
        phase = 2 * np.pi * (freq * t + (f_end - freq) * t * t / (2 * t[-1]))
    else:
        phase = 2 * np.pi * freq * t
    return np.sin(phase)


def _noise(n, rng):
    return rng.standard_normal(n)


def make(buf, t0, kind, rng):
    g = 1.0
    if kind == "footstep":
        n = int(0.07 * SR)
        sig = _sine(55, n) * _env(n, 0.025) * 0.5
        sig += _noise(n, rng) * _env(n, 0.012) * 0.12
        g = 0.35
    elif kind == "whiff":
        n = int(0.2 * SR)
        t = np.arange(n) / SR
        f = 900 * (1 - t / t[-1]) + 200
        ph = 2 * np.pi * np.cumsum(f) / SR
        sig = np.sin(ph) * _env(n, 0.05) * 0.25
        sig += _noise(n, rng) * _env(n, 0.06) * 0.3
        g = 0.8
    elif kind == "hit_light":
        n = int(0.16 * SR)
        sig = _sine(95, n) * _env(n, 0.05) * 0.9
        sig += _noise(n, rng) * _env(n, 0.02) * 0.5
        g = 0.9
    elif kind == "hit_heavy":
        n = int(0.28 * SR)
        sig = _sine(55, n, 38) * _env(n, 0.09) * 1.0
        sig += _noise(n, rng) * _env(n, 0.035) * 0.8
        g = 1.0
    elif kind == "hit_body":
        n = int(0.2 * SR)
        sig = _sine(110, n, 70) * _env(n, 0.06) * 0.9
        sig += _sine(65, n) * _env(n, 0.05) * 0.6
        sig += _noise(n, rng) * _env(n, 0.025) * 0.4
        g = 0.95
    elif kind == "uppercut":
        n1 = int(0.22 * SR)
        t = np.arange(n1) / SR
        f = 400 + 1400 * (t / t[-1])
        sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n1, 0.07) * 0.4
        n2 = int(0.3 * SR)
        sig = np.concatenate([sig, np.zeros(int(0.14 * SR))])
        heavy = _sine(50, n2, 35) * _env(n2, 0.1) + _noise(n2, rng) * _env(n2, 0.04) * 0.9
        sig = np.concatenate([sig, heavy])
        g = 1.0
    elif kind == "ko":
        n = int(1.1 * SR)
        sig = _sine(42, n, 30) * _env(n, 0.42) * 1.2
        sig[: int(0.02 * SR)] += _noise(int(0.02 * SR), rng) * 1.4
        sig += _noise(n, rng) * _env(n, 0.16) * 0.5
        g = 1.0
    elif kind == "thud":
        n = int(0.32 * SR)
        sig = _sine(48, n, 30) * _env(n, 0.11) * 1.1
        sig += _noise(n, rng) * _env(n, 0.05) * 0.5
        g = 0.9
    elif kind == "crowd":
        n = int(2.6 * SR)
        brown = np.cumsum(_noise(n, rng)) / 40.0
        a = np.minimum(1.0, np.arange(n) / (0.5 * SR))
        b = np.minimum(1.0, (n - np.arange(n)) / (0.9 * SR))
        sig = brown * a * b * 0.8
        g = 0.85
    elif kind == "victory":
        parts = []
        for fq in (261.6, 329.6, 392.0, 523.3):
            n = int(0.34 * SR)
            p = _sine(fq, n) * _env(n, 0.18) + _sine(fq * 2, n) * _env(n, 0.1) * 0.3
            parts.append(p)
        sig = np.concatenate(parts)
        g = 0.6
    else:
        return
    i0 = int(max(0.0, t0) * SR)
    i1 = min(len(buf), i0 + len(sig))
    if i1 > i0:
        buf[i0:i1] += g * sig[: i1 - i0]


def build(events, out_path=OUT):
    buf = np.zeros(int(SR * DUR))
    rng = np.random.default_rng(42)
    # ambient crowd bed
    n = int(SR * DUR)
    brown = np.cumsum(rng.standard_normal(n)) / 60.0
    buf += brown * 0.05
    for frame, kind in events:
        make(buf, frame / 30.0, kind, rng)
    # soft clip + normalize
    buf = np.tanh(buf * 1.4) * 0.9
    pk = np.max(np.abs(buf))
    if pk > 1e-6:
        buf = buf / pk * 0.89
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    pcm = (buf * 32767).astype("<i2")
    with wave.open(out_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out_path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/user/r6roblox-animation/combat_boxing/Blender")
    import choreo
    p = build(choreo.SFX_EVENTS)
    print("SFX written:", p)
