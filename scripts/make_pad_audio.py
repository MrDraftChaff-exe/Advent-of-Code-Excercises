#!/usr/bin/env python3
"""Write an original ambient pad (not a licensed track).

Each seed gets its own quiet sine bed that breathes, changes chords, and
pulses so a minute-long collage does not sit on a dead drone.
Sine only. No triangle, no chorus detune, no 7ths.
"""

from __future__ import annotations

import argparse
import math
import struct
import wave
from pathlib import Path

RATE = 44100
DURATION = 60.0
FADE = 2.4
MASTER = 0.28

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

# Open fifths and soft triads. No 7ths, no bright 9ths.
CHORDS = (
    (1.0, 3 / 2),
    (1.0, 6 / 5, 3 / 2),
    (1.0, 5 / 4, 3 / 2),
    (1.0, 4 / 3),
    (1.0, 5 / 3),
    (1.0, 6 / 5, 8 / 5),
)

PARTIAL_GAIN = (0.24, 0.11, 0.06)


def hash_seed(seed: str) -> int:
    h = 2166136261
    for byte in (seed or "facts-or-whacks").encode("utf-8"):
        h ^= byte
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def pad_params(seed: str) -> dict[str, float | tuple[float, ...] | tuple[int, ...]]:
    h = hash_seed(seed)
    order = [(h >> (i * 3)) % len(CHORDS) for i in range(4)]
    return {
        "root": ROOTS[h % len(ROOTS)],
        "chord": CHORDS[(h >> 4) % len(CHORDS)],
        "lfo_hz": 0.08 + ((h >> 8) % 50) / 1000.0,
        "cutoff": 190.0 + ((h >> 12) % 90),
        "lfo_depth": 0.12 + ((h >> 20) % 8) / 100.0,
        "breath_hz": 0.11 + ((h >> 16) % 6) / 100.0,
        "pulse_hz": 0.48 + ((h >> 18) % 8) / 100.0,
        "filter_lfo": 0.028 + ((h >> 10) % 12) / 1000.0,
        "prog": tuple(order),
    }


def chord_at(params: dict, index: int) -> tuple[float, ...]:
    prog = tuple(int(x) for x in params["prog"])  # type: ignore[arg-type]
    return tuple(float(x) for x in CHORDS[prog[index % len(prog)]])


def mix_chords(
    t: float,
    seconds: float,
    root: float,
    params: dict,
) -> tuple[float, float]:
    n_chords = 4
    seg = max(1e-6, seconds / n_chords)
    xfade = 2.2
    c0 = min(n_chords - 1, int(t / seg))
    local = t - c0 * seg
    chords = [chord_at(params, c0)]
    mixes = [1.0]
    if c0 < n_chords - 1 and local > seg - xfade:
        blend = (local - (seg - xfade)) / xfade
        chords.append(chord_at(params, c0 + 1))
        mixes = [1.0 - blend, blend]
    left = 0.0
    right = 0.0
    pans = (0.0, -0.32, 0.32)
    two_pi = 2.0 * math.pi
    for mix, chord in zip(mixes, chords):
        for idx, freq_mul in enumerate(chord):
            gain = PARTIAL_GAIN[idx] if idx < len(PARTIAL_GAIN) else 0.05
            sample = mix * gain * math.sin(two_pi * root * freq_mul * t)
            pan = pans[idx] if idx < len(pans) else 0.0
            left += sample * (1.0 - max(0.0, pan))
            right += sample * (1.0 + min(0.0, pan))
    return left, right


def render(seconds: float = DURATION, seed: str = "preview") -> bytes:
    params = pad_params(seed)
    root = float(params["root"])
    lfo_hz = float(params["lfo_hz"])
    cutoff = float(params["cutoff"])
    lfo_depth = float(params["lfo_depth"])
    breath_hz = float(params["breath_hz"])
    pulse_hz = float(params["pulse_hz"])
    filter_lfo = float(params["filter_lfo"])
    n = int(RATE * seconds)
    fade_n = int(RATE * min(FADE, seconds / 4))
    left_a = left_b = 0.0
    right_a = right_b = 0.0
    frames = bytearray()
    pack = struct.pack
    two_pi = 2.0 * math.pi
    pulse_period = 1.0 / pulse_hz

    for i in range(n):
        t = i / RATE
        left, right = mix_chords(t, seconds, root, params)
        breath = 0.78 + 0.22 * (0.5 + 0.5 * math.sin(two_pi * breath_hz * t))
        lfo = 1.0 + lfo_depth * math.sin(two_pi * lfo_hz * t)
        env = 1.0
        if i < fade_n:
            env = 0.5 - 0.5 * math.cos(math.pi * i / fade_n)
        elif i > n - fade_n:
            env = 0.5 - 0.5 * math.cos(math.pi * (n - i) / fade_n)

        phase = t % pulse_period
        if phase < 0.42:
            pulse_env = math.sin(math.pi * phase / 0.42) ** 2
            pulse = 0.09 * pulse_env * math.sin(two_pi * root * t)
            left += pulse
            right += pulse * 0.92

        shim_env = 0.5 + 0.5 * math.sin(two_pi * 0.19 * t)
        shimmer = 0.045 * shim_env * math.sin(two_pi * root * 3.0 * t)
        left += shimmer * 0.7
        right += shimmer * 1.0

        amp = MASTER * lfo * breath * env
        left *= amp
        right *= amp

        cut = cutoff * (1.18 + 0.32 * math.sin(two_pi * filter_lfo * t))
        lp_coef = math.exp(-2.0 * math.pi * max(90.0, cut) / RATE)
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
        default=Path("public/audio/facts-or-whacks-pad-60s.wav"),
    )
    parser.add_argument("--seconds", type=float, default=DURATION)
    parser.add_argument("--seed", default="preview")
    args = parser.parse_args()
    write_wav(args.out, args.seconds, args.seed)
    print(args.out, args.out.stat().st_size, "seed", args.seed)


if __name__ == "__main__":
    main()
