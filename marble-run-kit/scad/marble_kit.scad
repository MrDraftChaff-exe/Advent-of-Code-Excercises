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
keel_h = 0;
wall_h = 12.6;                  // above the marble floor
outer_w = ch_w + 2 * wall;
floor_top = keel_h + floor_t;

// Square lock. A square bar cannot rotate, so a run cannot sag flat.
bar = 7.6;
bar_pocket = bar + 0.65 + fit_extra;
neck_w = bar - 0.7;
neck_clear = 0.40;
stub_len = 7.6;
stub_gap = 0.45;
cradle_x = 7.2;
end_inset = 1.15;
axle_d = bar;                   // legacy name used by a few clearances
axle_z = floor_top + 5.6;

// Gravity is built into each track: about 12 degrees, in 12 mm steps.
slope_deg = 12;
drop_step = 12;

// Riser rail under every channel. Head slides in from the end and clicks.
slot_mouth_w = 6.6;
slot_mouth_h = 2.6;
slot_cav_w = 10.8;
slot_cav_z = 2.3;
slot_cav_h = 3.0;
head_w = 10.0;
head_h = 2.6;
head_len = 8.0;
neck_bar_w = 5.6;
riser_pitch = 12;

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

function track_drop(len) =
    drop_step * max(1, round(len * tan(slope_deg) / drop_step));

function pz(p) = len(p) > 2 ? p[2] : 0;

// ---------- hinge ----------
// Hinge axis is parallel to Y.
// Male axle stubs live on the upstream OUT end.
// Female keyhole cradles live on the downstream IN end.
// Seated axle does not rub: the neck is above the crown and only interferes while snapping in.

function side_y(s, extra=0) = s * (outer_w / 2 + stub_gap + extra);

module axle_stubs() {
    // Square bar embedded in the side wall. Downstream walls start past it.
    y_root = outer_w / 2 - wall + 0.6;
    y_tip = outer_w / 2 + stub_gap + stub_len;
    for (s = [-1, 1]) {
        ymin = s > 0 ? y_root : -y_tip;
        translate([-bar / 2, ymin, axle_z - bar / 2])
            cube([bar, y_tip - y_root, bar]);
    }
}

module keyhole_cut(length) {
    // Square pocket. The neck is above a seated bar, so it snaps in and then sits free.
    translate([-bar_pocket / 2, -length / 2 - 0.1, -bar_pocket / 2])
        cube([bar_pocket, length + 0.2, bar_pocket]);
    nb = bar / 2 + neck_clear;
    translate([-neck_w / 2, -length / 2 - 0.2, nb])
        cube([neck_w, length + 0.4, 16]);
    hull() {
        translate([-neck_w / 2, -length / 2 - 0.2, nb + 1.2])
            cube([neck_w, length + 0.4, 0.2]);
        translate([-(bar_pocket + 3) / 2, -length / 2 - 0.2, nb + 6.5])
            cube([bar_pocket + 3, length + 0.4, 0.2]);
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

// Downward-opening T-slot. A riser head slides in from the end.
module t_slot_plain(x0, x1) {
    translate([x0, -slot_mouth_w / 2, -0.3])
        cube([max(x1 - x0, 0.2), slot_mouth_w, slot_mouth_h + 0.3]);
    translate([x0, -slot_cav_w / 2, slot_cav_z])
        cube([max(x1 - x0, 0.2), slot_cav_w, slot_cav_h]);
}

module t_slot(x0, x1) {
    t_slot_plain(x0, x1);
    // Wider pockets the riser nub clicks into, one per riser_pitch.
    for (x = [x0 + 8:riser_pitch:x1 - 4])
        translate([x - 1.6, -(slot_mouth_w / 2 + 1.3), 0.3])
            cube([3.2, slot_mouth_w + 2.6, slot_mouth_h]);
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
    // Floor runs close to the hinge. Inlet walls start past the lock bar
    // so a seated stub does not intersect them. The marble bridges that gap.
    x0 = end_inset;
    x1 = len - end_inset;
    wx0 = open_inlet ? (bar / 2 + 1.5) : end_inset;
    difference() {
        union() {
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
    }
}

// Inlet floor is 0.3 mm low, then ramps back up so every joint steps downhill.
module inlet_step_cut(zfloor=floor_top) {
    hull() {
        translate([0.4, -ch_w / 2 + 0.7, zfloor - 0.32])
            cube([0.2, ch_w - 1.4, 0.34]);
        translate([11.5, -ch_w / 2 + 0.7, zfloor - 0.02])
            cube([0.2, ch_w - 1.4, 0.04]);
    }
}

// ---------- tower system (Fat Brain style) ----------
// Posts stack into towers. Each track clips onto two posts.
// Slope is the height difference between those posts.

post_d = 18;
post_pitch = 20;
flange_d = 28;
flange_h = 3.2;
clip_h = 8.4;
groove_z = flange_h;
groove_h = 13.6;
peg_d = 12;
peg_h = 7.2;
socket_d = peg_d + 0.45 + fit_extra;
socket_h = 7.6;
pin_d = 6;
pin_hole = pin_d + 0.7 + fit_extra;
pin_z = 6.2;
clip_reach = 16; // post center to hinge pin

module post() {
    difference() {
        union() {
            cylinder(d=flange_d, h=flange_h, $fn=48);
            translate([0, 0, flange_h])
                cylinder(d=post_d, h=groove_h, $fn=48);
            translate([0, 0, flange_h + groove_h])
                cylinder(d=flange_d, h=flange_h, $fn=48);
            translate([0, 0, flange_h + groove_h + flange_h])
                cylinder(d=peg_d, h=peg_h, $fn=32);
            // Snap rib. A groove in the next socket clears it once seated.
            translate([0, 0, flange_h + groove_h + flange_h + 2.9])
                cylinder(d=peg_d + 0.5, h=1.2, $fn=32);
        }
        translate([0, 0, -0.2])
            cylinder(d=socket_d, h=socket_h, $fn=32);
        translate([0, 0, 2.4])
            cylinder(d=socket_d + 1.3, h=1.8, $fn=32);
        translate([0, -flange_d / 2 - 0.1, 8])
            rotate([90, 0, 0])
                linear_extrude(1)
                    text_line("PS", 4.2);
    }
}

module base_foot() {
    difference() {
        union() {
            cylinder(d=46, h=4, $fn=64);
            translate([0, 0, 4])
                cylinder(d=peg_d, h=peg_h, $fn=32);
            translate([0, 0, 4 + 2.9])
                cylinder(d=peg_d + 0.5, h=1.2, $fn=32);
        }
        translate([-10, -22, 1])
            linear_extrude(1)
                text_line("BF", 5);
    }
}

hinge_y = outer_w / 2 + 9;

module end_clip() {
    // C-clip for the post, plus a hinge knuckle beside the track.
    // This body is not joined to the channel; the pin passes through the knuckle.
    difference() {
        union() {
            cylinder(d=post_d + 8, h=clip_h, $fn=48);
            translate([3, outer_w / 2 - 0.4, 0])
                cube([clip_reach + 2, hinge_y - 1 - (outer_w / 2 - 0.4), clip_h]);
            translate([clip_reach, hinge_y, pin_z])
                rotate([-90, 0, 0])
                    cylinder(d=pin_hole + 4.8, h=7, center=true, $fn=28);
        }
        translate([0, 0, -0.4])
            cylinder(d=post_d + 0.55 + fit_extra, h=clip_h + 0.8, $fn=48);
        translate([-8.2, 1.2, -0.6])
            cube([16.4, post_d + 2, clip_h + 1.2]);
        translate([clip_reach, hinge_y, pin_z])
            rotate([-90, 0, 0])
                cylinder(d=pin_hole, h=16, center=true, $fn=28);
    }
}

module end_pin() {
    // Pin captured in the clip knuckle, cheek joined only to the channel wall.
    translate([clip_reach, hinge_y, pin_z])
        rotate([-90, 0, 0])
            cylinder(d=pin_d, h=14, center=true, $fn=24);
    translate([clip_reach - 7, outer_w / 2 - wall, 0])
        cube([14, hinge_y - 4.4 - (outer_w / 2 - wall), pin_z + pin_d / 2 + 1.2]);
}

module span_track(span, id, qty) {
    difference() {
        translate([14, 0, 0])
            channel_straight(span - 28, floor_top, floor_top, false);
        translate([14, 0, 0])
            side_label((span - 28) * 0.45, qty_lines(id, qty), 4.6);
        translate([span - 30, 0, 0])
            side_arrow(0);
    }
    end_pin();
    translate([span, 0, 0]) rz(180) end_pin();
    end_clip();
    translate([span, 0, 0]) rz(180) end_clip();
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
        union() {
            for (i = [0:n - 2])
                hull() {
                    translate([pts[i][0], pts[i][1], pz(pts[i])]) rz(angs[i]) profile_solid(fz);
                    translate([pts[i + 1][0], pts[i + 1][1], pz(pts[i + 1])]) rz(angs[i + 1]) profile_solid(fz);
                }
            // Keel down to the bed so the riser rail stays on the bottom.
            for (i = [0:n - 2])
                hull() {
                    translate([pts[i][0], pts[i][1], 0]) rz(angs[i])
                        translate([-0.7, -8, 0]) cube([1.4, 16, keel_h]);
                    translate([pts[i + 1][0], pts[i + 1][1], 0]) rz(angs[i + 1])
                        translate([-0.7, -8, 0]) cube([1.4, 16, keel_h]);
                }
        }
        for (i = [0:n - 2])
            hull() {
                translate([pts[i][0], pts[i][1], pz(pts[i])]) rz(angs[i]) profile_void(fz);
                translate([pts[i + 1][0], pts[i + 1][1], pz(pts[i + 1])]) rz(angs[i + 1]) profile_void(fz);
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
            translate([pE[0], pE[1], 0]) rz(hE)
                translate([-3, 0, 0])
                    channel_straight(lead + 3, floor_top, floor_top, false);
            translate([-clip_reach, 0, 0]) end_pin();
            translate([pE[0], pE[1], 0]) rz(hE)
                translate([lead, 0, 0]) rz(180)
                    end_pin();
        }
        translate([mid[0], mid[1], 0]) rz(hang)
            side_label(0, qty_lines(id, qty), 4.6);
    }
    translate([-clip_reach, 0, 0]) end_clip();
    translate([pE[0], pE[1], 0]) rz(hE)
        translate([lead, 0, 0]) rz(180)
            end_clip();
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
            translate([-clip_reach, 0, 0]) end_pin();
            translate([pE[0], pE[1], 0]) rz(hE)
                translate([lead, 0, 0]) rz(180)
                    end_pin();
        }
        translate([mid[0], mid[1], 0]) rz(hang)
            side_label(0, qty_lines(id, qty), 4.6);
    }
    translate([-clip_reach, 0, 0]) end_clip();
    translate([pE[0], pE[1], 0]) rz(hE)
        translate([lead, 0, 0]) rz(180)
            end_clip();
}

include <parts_extra.scad>

// ---------- dispatcher ----------

module build_part() {
    if (part == "T1") span_track(90, "T1", mark_qty);
    else if (part == "T2") span_track(130, "T2", mark_qty);
    else if (part == "T3") span_track(170, "T3", mark_qty);
    else if (part == "FIT") span_track(70, "FIT", 1);
    else if (part == "PS") post();
    else if (part == "BF") base_foot();
    else if (part == "CL") curve(+1, "CL", mark_qty);
    else if (part == "CR") curve(-1, "CR", mark_qty);
    else if (part == "CU") uturn("CU", mark_qty);
    else if (part == "RS") part_rs();
    else extra_part();
}

module part_rs() {
    // 12 mm locking riser. The head slides into the rail under any channel,
    // and into the slot in the bottom of another riser.
    difference() {
        union() {
            translate([-8, -8, 0]) cube([16, 16, riser_pitch]);
            translate([-head_len / 2, -neck_bar_w / 2, riser_pitch])
                cube([head_len, neck_bar_w, slot_mouth_h]);
            translate([-head_len / 2, -head_w / 2, riser_pitch + slot_mouth_h - 0.05])
                cube([head_len, head_w, head_h]);
            // Nub that clicks into the rail pockets.
            translate([-1.2, -3.7, riser_pitch + 0.5])
                cube([2.4, 7.4, 1.5]);
        }
        t_slot(-9, 9);
        translate([-7, -7.9, 4])
            rotate([90, 0, 0])
                linear_extrude(1.0)
                    text_line("RS", 4.5);
        translate([-6, -7.9, 1.2])
            rotate([90, 0, 0])
                linear_extrude(1.0)
                    text_line(str("x", mark_qty), 3.4);
    }
}

module mated() {
    len = 52;
    d = track_drop(len);
    tube(len, "T1", 4);
    translate([len, 0, axle_z])
        rotate([0, mate_angle, 0])
            translate([0, 0, -(axle_z + d)])
                tube(len, "T1", 4);
}

module mate_hit() {
    len = 52;
    d = track_drop(len);
    intersection() {
        tube(len, "T1", 4);
        translate([len, 0, axle_z])
            rotate([0, mate_angle, 0])
                translate([0, 0, -(axle_z + d)])
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
    intersection() {
        span_track(90, "T1", 4);
        for (x = [24:8:66])
            translate([x, 0, floor_top + marble_d / 2 + 0.4])
                sphere(d=marble_d, $fn=24);
    }
}
else if (mode == "stack") {
    intersection() {
        post();
        translate([0, 0, post_pitch + 0.25]) post();
    }
}
else if (mode == "clipfit") {
    intersection() {
        post();
        translate([0, 0, groove_z + 1.2]) end_clip();
    }
}
