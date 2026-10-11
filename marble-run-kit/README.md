# Marble run kit

Twenty printable parts that snap together into a marble run. A starter set, with more long tubes than anything else, packs onto **7 plates** of 220 × 220 mm.

## Which ball to use

Use a **16 mm ball**.

| Ball | Use it? |
| --- | --- |
| 16 mm glass marble | Yes. This is the default. Buy a bag labeled 16 mm and check every ball with the gauge. |
| 5/8 in (15.875 mm) steel ball bearing | Yes. Same channels. Better for the loop, the jump, and the elevator, because a steel ball is heavier and rounder and keeps its speed. |
| Anything else | No. 1/2 in (12.7 mm) bearings rattle and jam. 25 mm toy marbles do not fit. |

You do not need special marble-run balls, screws, or glue. Glass and steel can share one run. Do not mix other diameters.

The legend card has two holes:

- **GO, 16.7 mm.** The ball must fall through.
- **NO-GO, 15.5 mm.** The ball must sit on top and not fall through.

A good 16 mm marble and a 5/8 in bearing both pass. A 14 mm marble falls through the NO-GO hole. Reject that one.

The channel is 19.6 mm wide, so a ball from about **15.6 mm to 16.6 mm** rolls without jamming. Cheap glass marbles are often out of round. Roll a few down a long tube before you print a whole plate.

## The 20 parts

Each part is marked on the side. `T3` over `x6` means “long tube, print six for the starter set.”

| Mark | Starter count | What it is |
| --- | --- | --- |
| `FN` | 1 | Funnel. Start of a run, or a target for the jump. Outlet only. |
| `T1` | 4 | Short tube, 52 mm, drops 12 mm. |
| `T2` | 4 | Medium tube, 100 mm, drops 24 mm. |
| `T3` | 6 | Long tube, 150 mm, drops 36 mm. Print the most of these. |
| `CL` | 2 | 90° curve, left. |
| `CR` | 2 | 90° curve, right. |
| `CU` | 1 | 180° U-turn. |
| `SP` | 1 | Spiral. Drops about 28 mm in a compact column. |
| `WF` | 1 | Waterfall, plus cover `WF-C`. Prints flat. Stand it up after the cover is on. |
| `YS` | 1 | Splitter, one in, two out. |
| `MG` | 1 | Merger, two in, one out. |
| `SW` | 1 | Seesaw. Pieces `SW-B` base, `SW-A` beam, `SW-P` pin. |
| `LP` | 1 | Loop. Pieces `LP-A` track, `LP-B` cover, `LP-C` entry, `LP-D` exit. |
| `EL` | 1 | Hand-crank elevator. Pieces `EL-B` base, `EL-W` wheel, `EL-C` crank. One direction. |
| `ZZ` | 1 | Zigzag brake. Slows a fast marble. |
| `JP` | 1 | Jump ramp. Open lip, no front connector. |
| `LD` | 1 | Wide landing for the jump. |
| `SN` | 1 | Spinner. Pieces `SN-B` base, `SN-W` wheel, `SN-C` cap. |
| `RS` | 12 | Locking riser, 12 mm. Slides under any channel and stacks into a frame. |
| `BX` | 1 | Finish box. Inlet only. |

`FIT` is a small lock coupon, not one of the twenty. `LG` is the legend card and the ball gauge.

![All parts](images/parts.png)

## Gravity is built in

Tubes, curves, and the U-turn are sloped about **12–13°**. The slope is in the part. The joint is a square lock, so a run cannot sag back to flat.

| Piece | Drop |
| --- | --- |
| `T1`, `CL`, `CR`, `FIT` | 12 mm, one riser |
| `T2`, `CU` | 24 mm, two risers |
| `T3` | 36 mm, three risers |

The outlet of one piece locks to the inlet of the next at the same height. The next piece’s outlet is another step lower. A marble is always going downhill on those parts.

## Risers lock into a frame

Every channel has a T-shaped rail in the bottom. `RS` is a 12 mm block:

- The head slides into that rail from the end of the piece and clicks into a pocket.
- The same head slides into the slot in the bottom of another riser.

So a riser locks under any channel, and risers lock to each other. Twelve risers is 144 mm of frame. Put three fewer risers under the outlet of a `T3` than under its inlet. The bottoms stay level. The channel carries the slope.

Slide the head in until it clicks. Push harder to move it to the next pocket, one pocket every 12 mm.

## Printing

Files:

- `stl/*.stl` — one of each piece, already oriented for the bed.
- `plates/starter-220-*.stl` — the starter quantities on 220 × 220 mm plates.
- `images/plates.png` — what is on each plate.

![Plate layouts](images/plates.png)

Suggested slicer settings:

- 0.4 mm nozzle, 0.2 mm layers
- 3 perimeters
- 15% infill
- PLA or PETG
- No supports
- A brim on `RS`, `EL-W`, and `SP` if the corners lift

Print `FIT` first and lock it to a `T1`. The square stub should click in and then stay put. If it will not seat, open `scad/marble_kit.scad` and raise `fit_extra` by 0.1, then rerun `python3 scripts/build_kit.py`. Slide one `RS` into the rail under `FIT` until it clicks.

Every individual piece fits on a 180 × 180 mm bed. The combined plates are laid out for 220 × 220 mm, which is the common Ender-size bed. A 256 mm bed can use the same plates.

## Building the frame

Start the funnel on a stack of risers. Each `T3` after that needs a stack three risers shorter, each `T2` or U-turn two shorter, each `T1` or 90° curve one shorter. The locked joint sets the height. The risers only hold the part up.

A brim on `RS`, `EL-W`, and `SP` helps if the corners lift.

## A run that uses the set

1. `FN` on a tall stack.
2. Two `T3`s at about 12°.
3. `CL`, a `T2`, `CR`.
4. `SP` to lose a chunk of height in one footprint.
5. `YS` to split.
6. One branch: `ZZ` into `SW`, then onward.
7. The other branch: `JP` aimed at `LD`, then `LP` if you want the loop. Use a steel ball for the loop and the jump.
8. `MG` to join the branches.
9. `WF` stood upright, cover on, inlet at the top.
10. `EL` to lift the ball back up. Crank the wheel so pockets rise on the shroud side.
11. `CU` and `BX` to finish.

`SN` can sit anywhere a ball should pause and spin.

## The pieces that are not plain tubes

**Waterfall.** Printed flat. Snap `WF-C` over the open side (rails pointing down onto the walls). Stand it so the `UP` mark points up and the inlet hinge is at the top. The outlet hinge stays horizontal.

**Loop.** `LP-A` is the open track, printed flat. `LP-B` is the cover; the pegs on `LP-A` go through the holes in `LP-B`. Stand the pair up. Slide `LP-C` onto the entry tenon and `LP-D` onto the exit tenon. Feed the loop from a `T3`, or from the jump. A steel 5/8 in bearing makes the loop much more reliable than glass.

**Jump and landing.** `JP` is a fixed ramp with an open lip. `LD` is the wide mouth that catches it. Start with the landing about 80–100 mm in front of the lip and a little lower, then move it after a few throws. Steel balls fly straighter.

**Seesaw.** Drop `SW-P` through `SW-A` into the saddles on `SW-B`. Empty, the tail sits down and the cup waits under the inlet. One glass marble in the cup should tip it and roll out the lower chute. The tail has a pocket: leave it empty at first. If the beam will not tip back, put one marble in that pocket.

**Elevator.** One-way lift. `EL-W` is the wheel and prints flat. `EL-C` is the crank with a long shaft; the shaft prints standing up and has a flat that matches the wheel bore. Slide the wheel onto the shaft, then drop the shaft into the two saddles on `EL-B` so the wheel hangs between the towers and the pockets face the shroud. The crank stays outside one tower. Turn it so a pocket picks up a ball at the bottom window and carries it to the top window. Turning the other way dumps the ball back at the inlet.

**Spinner.** Drop `SN-W` onto the pin and press `SN-C` on top. A ball from the inlet hits a paddle, spins the wheel, and eventually finds the exit.

**Spiral.** The ribs under the helix are part of the print. They are not supports you remove. The inlet is the high hinge, the outlet is the low one.

## Changing the ball size

Open `scad/marble_kit.scad`. `marble_d` is 16. Channel width, funnel, gauge text, and the seesaw pocket all follow from the parts that read `marble_d`. The legend holes are fixed at 16.7 and 15.5; change those in `scad/parts_extra.scad` if you change the ball. Then:

```bash
python3 scripts/build_kit.py
```

That re-exports `stl/`, repacks `plates/`, and writes `validation.txt`. You need OpenSCAD 2021 or newer and Python 3 with NumPy and Matplotlib.

## If something does not roll

- Joint will not snap: raise `fit_extra` by 0.1 and rebuild. Do not sand the inside of the keyhole first.
- Marble stalls on a tube: the tube is already about 13°. Check that the square joint is fully seated and the riser stacks differ by the drop in the table above.
- Marble hops out of a curve: lower the angle, or come into the curve from `ZZ`.
- Seesaw stays tipped: add one marble to the tail pocket.
- Seesaw never tips: the tail pocket should be empty. A steel ball in the cup tips more easily than glass.
- Loop or jump is inconsistent: use a 5/8 in steel bearing for those tricks. Glass is fine everywhere else.
