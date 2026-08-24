# Facts or Whacks — 30s video batch

Turn each topic still (or any folder of images/videos) into a **30-second 9:16 clip** with a trendy-style audio bed underneath.

Licensed TikTok/Reels sounds cannot be bundled here. The script generates an original dark-cinematic trap bed timed to 30s. For the algorithm boost, replace that bed in CapCut/TikTok with a currently trending sound.

## Batch the CSV (all 30 topics)

```bash
python3 scripts/overlay_trendy_audio.py --csv facts-or-whacks-30-videos.csv
```

Writes `output/videos/01-….mp4` through `30-….mp4`.

## Overlay the same 30s bed on your own files

```bash
python3 scripts/overlay_trendy_audio.py --input-dir /path/to/clips
python3 scripts/overlay_trendy_audio.py --input-dir /path/to/clips --audio /path/to/your-sound.mp3
```

Images become a Ken Burns 9:16 clip. Videos are fitted to 9:16, trimmed/padded to 30s, and the soundtrack is replaced.

Needs `ffmpeg`, `python3`, `numpy`, and `Pillow`.
