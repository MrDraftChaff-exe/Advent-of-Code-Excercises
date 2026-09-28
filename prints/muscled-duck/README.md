# Muscled duck (AD5X, 4 colors)

A standing duck with a lifter's build: yellow body, orange bill and legs, black belt, gloves, and eyes, red trunks and sweatband. It is modeled to print without support on a Flashforge AD5X.

| | |
| --- | --- |
| Size | 68.0 × 68.4 × 112.2 mm |
| Bed | Feet flat on z = 0, centered |
| Nozzle | 0.4 mm |
| Material | PLA in all 4 IFS slots |
| File | `output/muscled-duck-ad5x.3mf` |

Separate shells are in `output/stl/` if you need to inspect one color. Import the 3MF for a real print. The four shells are one assembly, so they stay aligned.

## Colors

| Slot | Name in the 3MF | PLA | Parts |
| --- | --- | --- | --- |
| 1 | Body | `#F5C518` duck yellow | Head, torso, arms, tail |
| 2 | Bill, legs and feet | `#FF6A00` orange | Bill, thighs, calves, webbed feet |
| 3 | Belt, gloves and eyes | `#1A1A1A` black | Power belt and buckle, gloves, eyes |
| 4 | Trunks and sweatband | `#E10600` red | Posing trunks, forehead sweatband |

Loaded spool colors can differ. In Flash Studio, map each sliced filament to the channel that actually holds that color. Keep the material type PLA on every channel. Mixing PLA with ABS or PETG will fail slicing, and an empty channel cannot be selected.

## Slice and send

1. Open `output/muscled-duck-ad5x.3mf` in Flash Studio (Orca-Flashforge) or Orca Slicer.
2. Re-select the printer **Flashforge AD5X**, nozzle **0.4 mm**, and a **0.20 mm PLA** process. The 3MF only carries filament colors and the printer name. The slicer profile is the one that sets temperatures and line width.
3. Confirm the four parts still wear slots 1–4 as in the table above. Do not Arrange in a way that splits the assembly, and do not center the STL files one by one.
4. Suggested process: 0.20 mm layers, 3 walls, 12% gyroid infill, supports off, 5 mm brim, prime tower on, flush into infill.
5. Enable IFS when you send the job. Assign each filament to a loaded PLA channel.

`output/print.json` estimates about 52 g of filament before purge, at 3 walls and 12% infill. The slicer total, including the prime tower, is the number to trust.

The pose is support-free on purpose. The arms end on the trunks, the bill sits on the chest, and the overhangs stay near 45 degrees or shallower. Leave supports off unless the sliced preview shows a floating island.

## Rebuild

From the repo root, with the packages in `requirements.txt`:

```bash
python3 prints/muscled-duck/generate.py --quality final
```

`--quality preview` uses a coarser curve and is only for looking at the sculpt. Ship the `final` meshes. The script refuses to write a shell that is not watertight after a slicer-style vertex weld, and it refuses a standing pose that needs support or falls outside the bed.
