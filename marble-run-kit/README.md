# Marble run kit

A tower-and-track marble run in the style of the Fat Brain 200-piece set. Short posts stack into towers. Tracks clip onto the posts. One end higher than the other is what makes the marble run.

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
| `PS` | 16 | Tower post. These are the connectors. Stack them. |
| `BF` | 4 | Wide foot. Start each tower on one. |
| `BX` | 1 | Finish box. Inlet only. |

`FIT` is a small lock coupon, not one of the twenty. `LG` is the legend card and the ball gauge.

![All parts](images/parts.png)

## How a run gets its slope

This is the same idea as that clear tower set: most of the parts are posts, and the tracks hang between them.

1. Snap `PS` posts onto a `BF` foot. Each post adds 20 mm.
2. Snap a track’s C-clip into the groove between the two discs on a post.
3. Snap the other clip onto a second tower, one post lower.

The clips stay level. The track hinges on them, so it tilts to the tower heights. One post of difference is about 13° on a short tube, 9° on a medium tube, and 7° on a long tube. Two posts on a short tube is a fast drop. The clip locks in the groove, so the height does not slip.

Tracks do not plug into each other. The end of an upper track is aimed at the start of the next track, one level down, often on the same tower or the next one. That is how the big sets are built.

## Printing

Files:

- `stl/*.stl` — one of each piece, already oriented for the bed.
- `plates/starter-220-*.stl` — the starter set on 9 plates of 220 × 220 mm. Most of the pieces on those plates are tower posts.
- `images/plates.png` — what is on each plate.

![Plate layouts](images/plates.png)

Suggested slicer settings:

- 0.4 mm nozzle, 0.2 mm layers
- 3 perimeters
- 15% infill
- PLA or PETG
- No supports
- A brim on `PS`, `BF`, `EL-W`, and `SP` if the corners lift

Print one `PS`, one `BF`, and `FIT` first. Stack the post on the foot, then snap both clips of `FIT` onto posts. The clip should click into the groove and the track should tilt if one post is higher. If a clip will not go on, open `scad/marble_kit.scad`, raise `fit_extra` by 0.1, and rerun `python3 scripts/build_kit.py`.

Every individual piece fits on a 180 × 180 mm bed. The combined plates are laid out for 220 × 220 mm, which is the common Ender-size bed. A 256 mm bed can use the same plates.

## Building a tower run

Four feet, with towers of different heights, are enough for a first layout. Clip a long tube from a high groove to a groove one post lower. Put a curve on the lower tower and run it across to a third tower, again one post lower. Keep doing that until the marble reaches the finish box. A two-post drop on a short tube is the fast section.

## A run that uses the set

1. `BF` feet in a loose grid, about 90–160 mm apart, with `PS` towers on them.
2. `FN` clipped at the top of the tallest tower, then a `T3` down one post to the next tower.
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
