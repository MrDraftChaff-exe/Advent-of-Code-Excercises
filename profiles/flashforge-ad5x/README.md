# AD5X 0.20 mm standard, low waste

Daily profile for a Flashforge AD5X with a 0.4 mm nozzle and PLA. It keeps the stock 0.20 mm surfaces (2 walls, 5 top layers, 3 bottom layers, 0.20 mm layers, 0.25 mm first layer) and spends less filament on infill, supports, and color changes.

Import `AD5X-0.20mm-Standard-Low-Waste.zip` in Orca-Flashforge or Orca Slicer with **File → Import → Import Configs**. Then select:

| | |
| --- | --- |
| Printer | Flashforge AD5X 0.4 nozzle Low Waste |
| Process | 0.20mm Standard Low Waste @FF AD5X |
| Nozzle | 0.4 mm |
| Material | PLA in every IFS slot used by the print |

The process preset is hidden until that printer preset is selected. The printer preset turns on **Purge in prime tower**. On this printer that switch is what makes the flush multiplier, flush-into-infill, and flush-into-support apply. With it off, Orca replaces the flush table with a flat prime volume and ignores those three settings.

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
| Purge in prime tower | off | on |

Supports stay off. Turn them on for a print that needs them. Tree supports at 40° catch the overhangs that PLA will not hold, and those supports are allowed to be printed from the purge. Support filament and support-interface filament stay on the default slot, which is what allows the purge to flow into them.

Outer walls are never used as purge, so the shell color stays the filament assigned to that part.

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
