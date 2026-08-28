#!/usr/bin/env python3
"""Write an original ambient pad (not a licensed track).

Each seed (episode stem) gets its own warm sine choir so catalog videos
do not share one grating drone.
"""

from __future__ import annotations

import argparse
import math
import struct
import wave
from pathlib import Path

RATE = 44100
DURATION = 30.0
FADE = 1.4
MASTER = 0.11

# Low warm roots, C2 through A2.
ROOTS = (
    65.41,
    69.30,
    73.42,
    77.78,
    82.41,
    87.31,
    92.50,
    98.00,
    103.83,
    110.00,
)

# Soft consonant voicings only. No tritones, no bright triangles.
CHORDS = (
    (1.0, 5 / 4, 3 / 2, 15 / 8),  # maj7
    (1.0, 9 / 8, 5 / 4, 3 / 2),  # add9
    (1.0, 9 / 8, 4 / 3, 3 / 2),  # sus
    (1.0, 6 / 5, 3 / 2, 5 / 3),  # min6
    (1.0, 5 / 4, 3 / 2, 5 / 3),  # maj6
    (1.0, 6 / 5, 3 / 2, 9 / 5),  # min7
    (1.0, 9 / 8, 3 / 2, 2.0),  # sus2 octave
    (1.0, 5 / 4, 3 / 2, 9 / 4),  # maj add9
)

PARTIAL_GAIN = (0.24, 0.16, 0.12, 0.08)


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
        "lfo_hz": 0.035 + ((h >> 8) % 80) / 1000.0,
        "cutoff": 360.0 + ((h >> 12) % 220),
        "detune": 3.0 + ((h >> 16) % 6),
        "lfo_depth": 0.10 + ((h >> 20) % 8) / 100.0,
    }


def cents_ratio(cents: float) -> float:
    return 2.0 ** (cents / 1200.0)


def render(seconds: float = DURATION, seed: str = "preview") -> bytes:
    params = pad_params(seed)
    root = float(params["root"])
    chord = tuple(float(x) for x in params["chord"])  # type: ignore[arg-type]
    lfo_hz = float(params["lfo_hz"])
    cutoff = float(params["cutoff"])
    detune = float(params["detune"])
    lfo_depth = float(params["lfo_depth"])
    n = int(RATE * seconds)
    fade_n = int(RATE * FADE)
    lp_coef = math.exp(-2.0 * math.pi * cutoff / RATE)
    left_state = 0.0
    right_state = 0.0
    frames = bytearray()
    pack = struct.pack
    two_pi = 2.0 * math.pi
    left_ratio = cents_ratio(-detune)
    right_ratio = cents_ratio(detune)

    for i in range(n):
        t = i / RATE
        left = 0.0
        right = 0.0
        for freq_mul, gain in zip(chord, PARTIAL_GAIN):
            freq = root * freq_mul
            left += gain * math.sin(two_pi * freq * left_ratio * t)
            right += gain * math.sin(two_pi * freq * right_ratio * t)
        lfo = 1.0 + lfo_depth * math.sin(two_pi * lfo_hz * t)
        env = 1.0
        if i < fade_n:
            env = 0.5 - 0.5 * math.cos(math.pi * i / fade_n)
        elif i > n - fade_n:
            env = 0.5 - 0.5 * math.cos(math.pi * (n - i) / fade_n)
        amp = MASTER * lfo * env
        left *= amp
        right *= amp
        left_state = (1.0 - lp_coef) * left + lp_coef * left_state
        right_state = (1.0 - lp_coef) * right + lp_coef * right_state
        ls = max(-1.0, min(1.0, left_state))
        rs = max(-1.0, min(1.0, right_state))
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
