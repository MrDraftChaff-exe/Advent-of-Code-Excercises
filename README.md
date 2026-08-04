# Advent-of-Code-Excercises

## Card frames

Transparent, layered TCG frame cutouts live in [`frames/`](frames/README.md).

Locked slots: title box, art window, bottom left/right plaques.

```bash
python3 frames/export_layers.py --params frames/params/fire-lava-v1.json --punch raw.png
```

Each sample pack includes `frame.png` plus editable `layers/*.png`.
