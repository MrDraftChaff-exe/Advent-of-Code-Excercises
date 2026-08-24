#!/usr/bin/env python3
"""Write an original 30s ambient pad (not a licensed track)."""

from __future__ import annotations

import argparse
import math
import struct
import wave
from pathlib import Path

RATE = 44100
DURATION = 30.0
# Same drone set as the in-browser pad: original sine bed, not a sample.
PARTIALS = (
    (110.00, 0.26, "sine"),
    (164.81, 0.14, "sine"),
    (246.94, 0.06, "triangle"),
    (329.63, 0.035, "sine"),
)
MASTER = 0.18
LFO_HZ = 0.09
LFO_DEPTH = 0.22
FADE = 0.8


def osc(kind: str, phase: float) -> float:
    if kind == "triangle":
        return 2.0 * abs(2.0 * (phase % 1.0) - 1.0) - 1.0
    return math.sin(2.0 * math.pi * phase)


def render(seconds: float = DURATION) -> bytes:
    n = int(RATE * seconds)
    fade_n = int(RATE * FADE)
    samples = []
    for i in range(n):
        t = i / RATE
        mix = 0.0
        for freq, gain, kind in PARTIALS:
            mix += gain * osc(kind, freq * t)
        lfo = 1.0 + LFO_DEPTH * math.sin(2.0 * math.pi * LFO_HZ * t)
        env = 1.0
        if i < fade_n:
            env = i / fade_n
        elif i > n - fade_n:
            env = (n - i) / fade_n
        samples.append(max(-1.0, min(1.0, mix * MASTER * lfo * env)))
    return b"".join(struct.pack("<h", int(s * 32767)) for s in samples)


def write_wav(path: Path, seconds: float = DURATION) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = render(seconds)
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
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
    args = parser.parse_args()
    write_wav(args.out, args.seconds)
    print(args.out, args.out.stat().st_size)


if __name__ == "__main__":
    main()
