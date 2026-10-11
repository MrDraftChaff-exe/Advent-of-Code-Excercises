// Parametric marble-run kit
// Nominal ball: 16 mm glass marble or 5/8 in (15.875 mm) steel bearing.
// Open this file in OpenSCAD and set `part`, or pass -D from scripts/build_kit.py.
//
// Print orientation is the model's orientation: channel opens upward, bed is z = 0.
// No supports. 0.4 mm nozzle, 0.2 mm layers, 3 perimeters, 15% infill.

/* [Marble] */
marble_d = 16.0; // [12:0.5:20]

/* [Fit] */
// Extra diameter clearance on snap pockets. Raise by 0.1 if a test joint is tight.
fit_extra = 0.0; // [-0.2:0.05:0.6]

/* [Export] */
part = "T1";
mark_qty = 4;
mode = "part"; // [part, fit, mate, section]
mate_angle = 0; // degrees, positive lowers the downstream piece

/* [Hidden] */
$fn = 48;

ch_w = marble_d + 3.6;          // 19.6 at 16 mm
wall = 2.8;
floor_t = 2.6;
wall_h = 12.6;                  // above the floor; marble crown peeks ~3.5 mm
outer_w = ch_w + 2 * wall;
floor_top = floor_t;

axle_d = 8.0;
axle_z = 8.2;
pocket_d = axle_d + 0.50 + fit_extra;
neck_w = axle_d - 0.85;
neck_clear = 0.40;              // neck starts this far above a seated axle crown
stub_len = 7.6;
stub_gap = 0.45;                // lateral air gap so male wall and female cradle don't fuse
cradle_x = 7.2;                 // cradle block half-length along the track
end_inset = 1.15;               // floor stops this far short of the hinge plane

joint_gap = 1.15;               // floor-to-floor gap when level
// Downstream floor is slightly lower so a mismatch is always a step down.
step_down = 0.25;

module __end_params() {}

// ---------- small utilities ----------

module rz(a) { rotate([0, 0, a]) children(); }

module text_line(s, size=5.5) {
    text(s, size=size, font="Liberation Sans:style=Bold",
         halign="center", valign="center", $fn=16);
}

// Recessed label on the +Y outer wall. x is along-track position.
module side_label(x, lines, size=5.2) {
    n = len(lines);
    for (i = [0:n - 1]) {
        zi = floor_top + wall_h * 0.62 - (i - (n - 1) / 2) * (size + 0.7);
        translate([x, outer_w / 2 + 0.15, zi])
            rotate([90, 0, 0])
                linear_extrude(height=1.05, convexity=4)
                    text_line(lines[i], size);
    }
}

// Flow arrow on the +Y wall, pointing +X (toward the outlet).
module side_arrow(x) {
    translate([x, outer_w / 2 + 0.15, floor_top + 2.2])
        rotate([90, 0, 0])
            linear_extrude(height=1.05, convexity=3)
                polygon(points=[[-3.2, 0], [1.6, 0], [1.6, -1.15], [4.4, 1.15],
                                [1.6, 3.45], [1.6, 2.3], [-3.2, 2.3]]);
}

function qty_lines(id, qty, with_qty=true) =
    with_qty ? [id, str("x", qty)] : [id];

// ---------- hinge ----------
// Hinge axis is parallel to Y.
// Male axle stubs live on the upstream OUT end.
// Female keyhole cradles live on the downstream IN end.
// Seated axle does not rub: the neck is above the crown and only interferes while snapping in.

function side_y(s, extra=0) = s * (outer_w / 2 + stub_gap + extra);

module axle_stubs() {
    // Embedded in our own side wall. The downstream walls start past the
    // axle radius, so the two parts do not intersect.
    y_root = outer_w / 2 - wall + 0.6;
    y_tip = outer_w / 2 + stub_gap + stub_len;
    for (s = [-1, 1]) {
        ymin = s > 0 ? y_root : -y_tip;
        translate([0, ymin, axle_z])
            rotate([-90, 0, 0])
                cylinder(d=axle_d, h=y_tip - y_root, $fn=32);
    }
}

module keyhole_cut(length) {
    rotate([-90, 0, 0])
        cylinder(d=pocket_d, h=length, center=true, $fn=32);
    nb = axle_d / 2 + neck_clear;
    translate([-neck_w / 2, -length / 2 - 0.2, nb])
        cube([neck_w, length + 0.4, 16]);
    // Lead-in funnel so the axle cams the lips open.
    hull() {
        translate([-neck_w / 2, -length / 2 - 0.2, nb + 1.2])
            cube([neck_w, length + 0.4, 0.2]);
        translate([-(pocket_d + 3) / 2, -length / 2 - 0.2, nb + 6.5])
            cube([pocket_d + 3, length + 0.4, 0.2]);
    }
}

module cradle_block(side) {
    y0 = side_y(side, -0.15);
    y1 = side_y(side, stub_len + 0.55);
    ymin = min(y0, y1);
    ymax = max(y0, y1);
    y_mid = (ymin + ymax) / 2;
    difference() {
        translate([-cradle_x, ymin, 0])
            cube([cradle_x * 2, ymax - ymin, axle_z + axle_d / 2 + neck_clear + 5.4]);
        translate([0, y_mid, axle_z])
            keyhole_cut(ymax - ymin + 0.8);
    }
}

// Low rib under the axle, so it can cross the hinge plane without hitting a stub.
module cradle_tie(side) {
    y_inner = side * (outer_w / 2 - wall - 0.5);
    y_outer = side_y(side, 2.2);
    ymin = min(y_inner, y_outer);
    ymax = max(y_inner, y_outer);
    translate([4.0, ymin, 0])
        cube([7.2, ymax - ymin, 3.3]);
}

// Cut the side walls back so an upstream axle can sit in the cradles.
module axle_clearance() {
    intersection() {
        translate([0, 0, axle_z])
            rotate([-90, 0, 0])
                cylinder(d=axle_d + 2.6, h=outer_w + 30, center=true, $fn=28);
        for (s = [-1, 1]) {
            ypos = s * (outer_w / 2) - (s > 0 ? wall + 1.2 : -1.2);
            translate([-8, min(ypos, ypos + wall + 2.4), 2.2])
                cube([16, wall + 2.4, 20]);
        }
    }
}

module cradles() {
    cradle_block(-1);
    cradle_block(1);
    cradle_tie(-1);
    cradle_tie(1);
}

// Low shelf past the male hinge. The female underside is chamfered to land on it near 16°.
module male_shelf() {
    // Anvil just upstream of the hinge. The female chamfer lands on it near 16°.
    translate([-5.2, -6.2, 0])
        cube([5.2, 12.4, 1.25]);
}

// Remove only the underside corner of the inlet floor so the part can pitch down.
module inlet_chamfer_cut() {
    hull() {
        translate([0.4, -6.4, -0.2])
            cube([0.2, 12.8, 2.05]);
        translate([12.0, -6.4, -0.2])
            cube([0.2, 12.8, 0.22]);
    }
}

// ---------- straight channel ----------

module channel_straight(len, fz0, fz1, open_inlet=true) {
    // Floor runs close to the hinge. Inlet walls start past the axle radius
    // so a seated stub does not intersect them. The marble bridges that gap.
    x0 = end_inset;
    x1 = len - end_inset;
    wx0 = open_inlet ? (axle_d / 2 + 1.35) : end_inset;
    hull() {
        translate([x0, -outer_w / 2, 0]) cube([0.2, outer_w, fz0]);
        translate([x1 - 0.2, -outer_w / 2, 0]) cube([0.2, outer_w, fz1]);
    }
    for (s = [-1, 1]) {
        hull() {
            translate([wx0, s * (outer_w / 2) - (s > 0 ? wall : 0), fz0 - 0.05])
                cube([0.2, wall, wall_h + 0.05]);
            translate([x1 - 0.2, s * (outer_w / 2) - (s > 0 ? wall : 0), fz1 - 0.05])
                cube([0.2, wall, wall_h + 0.05]);
        }
    }
}

// Inlet floor is 0.3 mm low, then ramps back up so every joint steps downhill.
module inlet_step_cut() {
    hull() {
        translate([0.4, -ch_w / 2 + 0.7, floor_top - 0.32])
            cube([0.2, ch_w - 1.4, 0.34]);
        translate([11.5, -ch_w / 2 + 0.7, floor_top - 0.02])
            cube([0.2, ch_w - 1.4, 0.04]);
    }
}

module tube(len, id, qty) {
    difference() {
        channel_straight(len, floor_top, floor_top);
        inlet_chamfer_cut();
        inlet_step_cut();
        side_label(len * 0.48, qty_lines(id, qty), 5.0);
        side_arrow(len - 16);
    }
    cradles();
    translate([len, 0, 0]) {
        axle_stubs();
        male_shelf();
        for (s = [-1, 1])
            translate([-6.2, s * (outer_w / 2) - (s > 0 ? wall : 0), floor_top - 0.05])
                cube([6.2, wall, wall_h + 0.05]);
    }
}

// ---------- swept channel (curves, zigzag, junctions) ----------
// pts are [x,y], angs are heading degrees (0 = +X). Profiles are thin slabs
// hull'ed together. The void slab is slightly longer so it clears the solid hull.

module profile_solid(fz) {
    translate([-0.6, -outer_w / 2, 0])
        cube([1.2, outer_w, fz]);
    for (s = [-1, 1])
        translate([-0.6, s * outer_w / 2 - (s > 0 ? wall : 0), fz - 0.05])
            cube([1.2, wall, wall_h + 0.05]);
}

module profile_void(fz) {
    translate([-1.15, -ch_w / 2, fz - 0.02])
        cube([2.3, ch_w, wall_h + 8]);
}

module sweep(pts, angs, fz) {
    n = len(pts);
    difference() {
        for (i = [0:n - 2])
            hull() {
                translate([pts[i][0], pts[i][1], 0]) rz(angs[i]) profile_solid(fz);
                translate([pts[i + 1][0], pts[i + 1][1], 0]) rz(angs[i + 1]) profile_solid(fz);
            }
        for (i = [0:n - 2])
            hull() {
                translate([pts[i][0], pts[i][1], 0]) rz(angs[i]) profile_void(fz);
                translate([pts[i + 1][0], pts[i + 1][1], 0]) rz(angs[i + 1]) profile_void(fz);
            }
    }
}

function arc_pts(cx, cy, r, a0, a1, n=18) =
    [for (i = [0:n]) let(a = a0 + (a1 - a0) * i / n)
        [cx + r * cos(a), cy + r * sin(a)]];

// Heading of travel. Increasing angle (CCW) heads at a+90; clockwise travel heads at a-90.
function arc_angs(a0, a1, n=18) =
    [for (i = [0:n]) let(a = a0 + (a1 - a0) * i / n)
        (a1 >= a0 ? a + 90 : a - 90)];

module hinge_male_at(x, y, ang) {
    translate([x, y, 0]) rz(ang) {
        axle_stubs();
        male_shelf();
        for (s = [-1, 1])
            translate([-6.2, s * (outer_w / 2) - (s > 0 ? wall : 0), floor_top - 0.05])
                cube([6.2, wall, wall_h + 0.05]);
    }
}

module hinge_female_at(x, y, ang) {
    translate([x, y, 0]) rz(ang)
        cradles();
}

// ---------- curved parts ----------

module curve(hand, id, qty) {
    // Straight leads keep the hinges identical to a tube. hand +1 turns left.
    lead = 16;
    r = 36;
    n = 14;
    a0 = hand > 0 ? -90 : 90;
    a1 = 0;
    cx = lead;
    cy = hand > 0 ? r : -r;
    pts = arc_pts(cx, cy, r, a0, a1, n);
    angs = arc_angs(a0, a1, n);
    pE = pts[len(pts) - 1];
    hE = angs[len(angs) - 1];
    mid = pts[floor(n / 2)];
    hang = angs[floor(n / 2)];
    difference() {
        union() {
            channel_straight(lead + 1.2, floor_top, floor_top);
            sweep(pts, angs, floor_top);
            // Outlet lead, in the end-tangent frame, overlapping the arc.
            translate([pE[0], pE[1], 0]) rz(hE)
                translate([-3, 0, 0])
                    channel_straight(lead + 3, floor_top, floor_top, false);
        }
        inlet_chamfer_cut();
        inlet_step_cut();
        translate([mid[0], mid[1], 0]) rz(hang)
            side_label(0, qty_lines(id, qty), 4.6);
    }
    hinge_female_at(0, 0, 0);
    translate([pE[0], pE[1], 0]) rz(hE)
        translate([lead, 0, 0])
            hinge_male_at(0, 0, 0);
}

module uturn(id, qty) {
    lead = 14;
    r = 32;
    n = 20;
    a0 = -90; a1 = 90;
    pts = arc_pts(lead, r, r, a0, a1, n);
    angs = arc_angs(a0, a1, n);
    pE = pts[len(pts) - 1];
    hE = angs[len(angs) - 1];
    mid = pts[floor(n / 2)];
    hang = angs[floor(n / 2)];
    difference() {
        union() {
            channel_straight(lead + 1.2, floor_top, floor_top);
            sweep(pts, angs, floor_top);
            translate([pE[0], pE[1], 0]) rz(hE)
                translate([-3, 0, 0])
                    channel_straight(lead + 3, floor_top, floor_top, false);
        }
        inlet_chamfer_cut();
        inlet_step_cut();
        translate([mid[0], mid[1], 0]) rz(hang)
            side_label(0, qty_lines(id, qty), 4.6);
    }
    hinge_female_at(0, 0, 0);
    translate([pE[0], pE[1], 0]) rz(hE)
        translate([lead, 0, 0])
            hinge_male_at(0, 0, 0);
}

include <parts_extra.scad>

// ---------- dispatcher ----------

module build_part() {
    if (part == "T1") tube(52, "T1", mark_qty);
    else if (part == "T2") tube(100, "T2", mark_qty);
    else if (part == "T3") tube(150, "T3", mark_qty);
    else if (part == "FIT") tube(42, "FIT", 1);
    else if (part == "CL") curve(+1, "CL", mark_qty);
    else if (part == "CR") curve(-1, "CR", mark_qty);
    else if (part == "CU") uturn("CU", mark_qty);
    else extra_part();
}

module mated() {
    len = 52;
    tube(len, "T1", 4);
    translate([len, 0, axle_z])
        rotate([0, mate_angle, 0])
            translate([0, 0, -axle_z])
                tube(len, "T1", 4);
}

module mate_hit() {
    len = 52;
    intersection() {
        tube(len, "T1", 4);
        translate([len, 0, axle_z])
            rotate([0, mate_angle, 0])
                translate([0, 0, -axle_z])
                    tube(len, "T1", 4);
    }
}

if (mode == "part") build_part();
else if (mode == "mate") mated();
else if (mode == "hit") mate_hit();
else if (mode == "section")
    intersection() {
        mated();
        translate([-5, -0.4, -2]) cube([120, 0.8, 30]);
    }
else if (mode == "fit") {
    // Spheres that must miss the solid. An empty STL means the channel clears the ball.
    intersection() {
        tube(52, "T1", 4);
        for (x = [10:6:42])
            translate([x, 0, floor_top + marble_d / 2 + 0.3])
                sphere(d=marble_d, $fn=24);
    }
}
