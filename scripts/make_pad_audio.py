#!/usr/bin/env python3
"""Write an original ambient pad (not a licensed track).

Each seed (episode stem) gets its own quiet low fifth/triad so videos
do not share a harsh drone.
"""

from __future__ import annotations

import argparse
import math
import struct
import wave
from pathlib import Path

RATE = 44100
DURATION = 30.0
FADE = 2.8
MASTER = 0.22

# Low roots, A1 through E2.
ROOTS = (
    55.00,
    58.27,
    61.74,
    65.41,
    69.30,
    73.42,
    77.78,
    82.41,
)

# Open fifths and soft triads. No 7ths, no bright 9ths, no octave scream.
CHORDS = (
    (1.0, 3 / 2),
    (1.0, 6 / 5, 3 / 2),
    (1.0, 5 / 4, 3 / 2),
    (1.0, 4 / 3),
    (1.0, 5 / 3),
    (1.0, 6 / 5, 8 / 5),
)

PARTIAL_GAIN = (0.22, 0.09, 0.05)


def hash_seed(seed: str) -> int:
    h = 2166136261
    for byte in (seed or "facts-or-whacks").encode("utf-8"):
        h ^= byte
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def pad_params(seed: str) -> dict[str, float | tuple[float, ...]]:
    h = hash_seed(seed)
    return {
        "root": ROOTS[h % len(ROOTS)],
        "chord": CHORDS[(h >> 4) % len(CHORDS)],
        "lfo_hz": 0.02 + ((h >> 8) % 40) / 1000.0,
        "cutoff": 150.0 + ((h >> 12) % 70),
        "lfo_depth": 0.03 + ((h >> 20) % 4) / 100.0,
    }


def render(seconds: float = DURATION, seed: str = "preview") -> bytes:
    params = pad_params(seed)
    root = float(params["root"])
    chord = tuple(float(x) for x in params["chord"])  # type: ignore[arg-type]
    lfo_hz = float(params["lfo_hz"])
    cutoff = float(params["cutoff"])
    lfo_depth = float(params["lfo_depth"])
    n = int(RATE * seconds)
    fade_n = int(RATE * FADE)
    lp_coef = math.exp(-2.0 * math.pi * cutoff / RATE)
    left_a = left_b = 0.0
    right_a = right_b = 0.0
    frames = bytearray()
    pack = struct.pack
    two_pi = 2.0 * math.pi
    pans = (0.0, -0.25, 0.25)

    for i in range(n):
        t = i / RATE
        left = 0.0
        right = 0.0
        for idx, freq_mul in enumerate(chord):
            gain = PARTIAL_GAIN[idx] if idx < len(PARTIAL_GAIN) else 0.05
            sample = gain * math.sin(two_pi * root * freq_mul * t)
            pan = pans[idx] if idx < len(pans) else 0.0
            left += sample * (1.0 - max(0.0, pan))
            right += sample * (1.0 + min(0.0, pan))
        lfo = 1.0 + lfo_depth * math.sin(two_pi * lfo_hz * t)
        env = 1.0
        if i < fade_n:
            env = 0.5 - 0.5 * math.cos(math.pi * i / fade_n)
        elif i > n - fade_n:
            env = 0.5 - 0.5 * math.cos(math.pi * (n - i) / fade_n)
        amp = MASTER * lfo * env
        left *= amp
        right *= amp
        left_a = (1.0 - lp_coef) * left + lp_coef * left_a
        left_b = (1.0 - lp_coef) * left_a + lp_coef * left_b
        right_a = (1.0 - lp_coef) * right + lp_coef * right_a
        right_b = (1.0 - lp_coef) * right_a + lp_coef * right_b
        ls = max(-1.0, min(1.0, left_b))
        rs = max(-1.0, min(1.0, right_b))
        frames += pack("<hh", int(ls * 32767), int(rs * 32767))
    return bytes(frames)


def write_wav(path: Path, seconds: float = DURATION, seed: str = "preview") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = render(seconds, seed)
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(pcm)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("public/audio/facts-or-whacks-pad-30s.wav"),
    )
    parser.add_argument("--seconds", type=float, default=DURATION)
    parser.add_argument("--seed", default="preview")
    args = parser.parse_args()
    write_wav(args.out, args.seconds, args.seed)
    print(args.out, args.out.stat().st_size, "seed", args.seed)


if __name__ == "__main__":
    main()
