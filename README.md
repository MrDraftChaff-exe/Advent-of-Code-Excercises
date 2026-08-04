# Advent-of-Code-Excercises

## Card frames

Premium illustrated TCG-style frames live in [`frames/`](frames/README.md).

Locked content regions (fixed location, restyleable design):

1. Top title box  
2. Central art window  
3. Bottom left + right footer boxes  

Provide design params, then generate HQ art from the built prompt:

```bash
python3 frames/build_hq_frame.py --params frames/params/<theme>.json --print-prompt
python3 frames/build_hq_frame.py --params frames/params/<theme>.json --punch raw.png --preview
```

Samples: `frames/samples/sakura-shrine-v1.png`, `frames/samples/fire-lava-v1.png`.
