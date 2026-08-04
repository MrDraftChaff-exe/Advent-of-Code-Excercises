# Advent-of-Code-Excercises

## Card frames

Parameterized TCG-style card frames live in [`frames/`](frames/README.md).

Preserved content regions (fixed location, restyleable design):

1. Top title box  
2. Central art window  
3. Bottom left + right footer boxes  

Provide design params via `frames/params/*.json` or the request template, then run:

```bash
python3 frames/generate_frame.py --params frames/params.example.json
```
