# Tairn, Sgaeyl, and Andarna (AD5X, 4 colors)

The three central dragons from the Fourth Wing series, modeled as an original figurine for a Flashforge AD5X. Tairn is the large black dragon with a morningstar tail, Sgaeyl is the blue dragon with a dagger tail, and Andarna is the small gold dragon with a feather tail. They crouch on one sandstone perch, which is the fourth filament.

| | |
| --- | --- |
| Size | 172.0 × 144.5 × 38.9 mm |
| Bed | Flat perch bottom on z = 0, centered |
| Nozzle | 0.4 mm |
| Material | PLA in all 4 IFS slots |
| File | `output/fourth-wing-dragons-ad5x.3mf` |

Separate shells are in `output/stl/` if you need to inspect one color. Import the 3MF for a real print. The four shells are one assembly, so they stay aligned.

## Colors

| Slot | Name in the 3MF | PLA | Parts |
| --- | --- | --- | --- |
| 1 | Tairn | `#161616` black | Body, folded wings, morningstar tail |
| 2 | Sgaeyl | `#1A4FD0` blue | Body, folded wings, dagger tail |
| 3 | Andarna | `#E2B007` gold | Body, folded wings, feather tail |
| 4 | Stone perch | `#8D7963` sandstone | Shared base |

Loaded spool colors can differ. In Flash Studio, map each sliced filament to the channel that actually holds that color. Keep the material type PLA on every channel. Mixing PLA with ABS or PETG will fail slicing, and an empty channel cannot be selected.

## Slice and send

1. Open `output/fourth-wing-dragons-ad5x.3mf` in Flash Studio (Orca-Flashforge) or Orca Slicer.
2. Re-select the printer **Flashforge AD5X**, nozzle **0.4 mm**, and a **0.20 mm PLA** process. The 3MF carries filament colors and the printer name. The slicer profile sets temperatures and line width.
3. Confirm the four parts still wear slots 1–4 as in the table above. Do not Arrange in a way that splits the assembly, and do not center the STL files one by one.
4. Suggested process: 0.20 mm layers, 3 walls, 12% gyroid infill, supports off, 5 mm brim, prime tower on, flush into infill.
5. Enable IFS when you send the job. Assign each filament to a loaded PLA channel.

`output/print.json` estimates about 118 g of filament before purge, at 3 walls and 12% infill. Most of that is the perch. The slicer total, including the prime tower, is the one to trust.

Wings are folded, and the feet, bellies, and tails sit in the stone so the group prints without support. Leave supports off unless the sliced preview shows a floating island.

## Rebuild

From the repo root, with the packages in `requirements.txt`:

```bash
python3 prints/fourth-wing-dragons/generate.py --quality final
```

`--quality preview` uses a coarser curve and is only for looking at the sculpt. Ship the `final` meshes. The script refuses to write a shell that is not watertight after a slicer-style vertex weld, and it refuses a pose that needs support or falls outside the bed.
