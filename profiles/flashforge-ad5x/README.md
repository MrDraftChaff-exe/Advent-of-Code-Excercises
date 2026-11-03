# AD5X 0.20 mm standard, low waste

Daily profile for a Flashforge AD5X with a 0.4 mm nozzle and PLA. It keeps the stock 0.20 mm surfaces (2 walls, 5 top layers, 3 bottom layers, 0.20 mm layers, 0.25 mm first layer) and spends less filament on infill, supports, and color changes.

The process preset stands on its own. It shows up for the stock **Flashforge AD5X 0.4 nozzle** printer, which is the one already in the printer list. The optional printer preset only turns on **Purge in prime tower**.

## Import

1. In the slicer, the printer **Flashforge AD5X 0.4 nozzle** has to already be in the printer dropdown. Add that system printer from the configuration wizard first if it is missing. An import with no matching printer is dropped, and the dialog then says no config was imported.
2. Use **File → Import → Import Configs**. Select `0.20mm Standard Low Waste @FF AD5X.json`. You can select the zip instead; it contains the same process file plus the optional printer preset.
3. The dialog should report that a config was imported. Restart the slicer if the new name is not in the list yet.
4. Leave the printer on **Flashforge AD5X 0.4 nozzle**. Open the process dropdown and choose **0.20mm Standard Low Waste @FF AD5X**. It is a user preset, so it sits apart from the system 0.20 mm profiles.
5. Open the printer settings, Multimaterial tab, and turn on **Purge in prime tower**. That switch is what makes the flush multiplier, flush-into-infill, and flush-into-support apply. Selecting the optional printer **Flashforge AD5X 0.4 nozzle Low Waste** turns the same switch on for you.

| | |
| --- | --- |
| Printer | Flashforge AD5X 0.4 nozzle |
| Process | 0.20mm Standard Low Waste @FF AD5X |
| Nozzle | 0.4 mm |
| Material | PLA in every IFS slot used by the print |

## What changed from stock 0.20 mm Standard @FF AD5X

| Setting | Stock | This profile |
| --- | --- | --- |
| Layer height | 0.20 mm | 0.20 mm |
| Walls / top / bottom | 2 / 5 / 3 | 2 / 5 / 3 |
| Sparse infill | 15% crosshatch | 12% gyroid |
| Supports | off, tree when enabled, 30° | off, tree when enabled, 40° |
| Support interface spacing | 0.2 mm | 0.3 mm |
| Support base spacing | 2.5 mm | 3.0 mm |
| Prime tower | on | on, and skipped on layers with no color change |
| Prime tower brim | 5 mm | 3 mm |
| Flush into infill | off | on |
| Flush into support | on | on |
| Flush into other objects | off | off |
| Flush multiplier | 0.3 | 0.2 |
| Purge in prime tower | printer switch off | turn on under the printer's Multimaterial tab |
| Seam | aligned, no scarf | aligned, scarf on smooth outer walls |

Supports stay off. Turn them on for a print that needs them. Tree supports at 40° catch the overhangs that PLA will not hold, and those supports are allowed to be printed from the purge. Support filament and support-interface filament stay on the default slot, which is what allows the purge to flow into them.

Outer walls are never used as purge, so the shell color stays the filament assigned to that part.

## Seams

The stock profile lines every outer-wall start and stop up in one place and leaves a small gap there. On a rounded corner that becomes the groove in the photo: a notch that runs layer after layer, easy to see in white.

This profile still uses an aligned seam, so a sharp corner keeps the join tucked into that corner. On a smooth loop, where there is no sharp corner to hide it, the outer wall uses a scarf joint: the end of the loop ramps down over 15 mm and the next start ramps up over the same path, so the gap is closed instead of stacked. The scarf prints at 60 mm/s. The outer wall itself stays at the stock 200 mm/s, and only that 15 mm ramp slows down. The ramp starts at 10% of the layer height so the first bit of the join still has plastic in it.

Inner seams are staggered so they do not sit in one line behind the outer wall. Before the outer wall starts, the nozzle unretracts on the inside of the wall. At the end of a closed loop it wipes inward.

A sharp 90° corner still gets a normal aligned seam. That mark is shorter than a scarf laid across a crisp edge. If a corner like the one in the photo is still open after a reslice, turn off **Conditional scarf joint** for that project so every outer wall gets the ramp.

## Purge amount

Orca builds a flush table from the two filament colors, then multiplies it by 0.2. The first 15 mm³ of each change still goes on the prime tower so pressure is stable. Whatever is left is printed as infill, then as support, and only the leftover stays on the tower. The tower is also skipped on layers that do not change color, so a tall single-color section does not keep feeding the tower.

PLA at 1.24 g/cm³. "Into the part" is purge that becomes infill or support when that layer has enough of either.

| Change | Table | At 0.3 | At 0.2 | Left on the tower | Can go into the part |
| --- | ---: | ---: | ---: | ---: | ---: |
| Black → white | 559 mm³ | 168 mm³ | 112 mm³ | 15 mm³ | 97 mm³ |
| Black → yellow | 585 mm³ | 176 mm³ | 117 mm³ | 15 mm³ | 102 mm³ |
| Red → yellow | 431 mm³ | 129 mm³ | 86 mm³ | 15 mm³ | 71 mm³ |
| Yellow → red | 177 mm³ | 53 mm³ | 35 mm³ | 15 mm³ | 20 mm³ |
| White → yellow | 209 mm³ | 63 mm³ | 42 mm³ | 15 mm³ | 27 mm³ |
| Yellow → black | 115 mm³ | 35 mm³ | 23 mm³ | 15 mm³ | 8 mm³ |
| White → black | 79 mm³ | 24 mm³ | 16 mm³ | 15 mm³ | 1 mm³ |

A dark filament into a light one is the case to watch. If the first light wall shows the previous color, open the flush dialog and raise the multiplier from 0.2 toward 0.3 for that project. Similar colors and light-into-dark are already near the 15 mm³ tower minimum.

Place the prime tower in open bed space. With sparse tower layers off, a color change high in the print makes the nozzle travel down to the tower. Smooth timelapse prints the tower on every layer anyway.

The AD5X can also drop a purge puck into the chute from its own tool-change routine. This profile sets the slicer purge. If a full puck still falls in the chute on every change, that length is the printer's purge and stays in addition to the tower.
