// Printable tower-and-track marble run.
// Same system as the clear 200-piece set: cylinders stack, a track ring
// slides down over a cylinder, and the next cylinder traps the ring.
// The ring is captive on the track and hinges so the chute can slope.
//
// Published counts: 80 connectors, 36 tracks, 60 marbles, and 24 other pieces.
// This file is original geometry. It does not copy a logo or a booklet.
//
// Marble: 16 mm. 0.4 mm nozzle, 0.2 mm layers, no supports.
// Raise fit_extra by 0.05 if a ring or a peg is tight on your printer.

/* [Fit] */
fit_extra = 0.0; // [0:0.05:0.4]

/* [Export] */
part = "CN";
mode = "part"; // [part, stack, ringfit, clear, fit]

/* [Hidden] */
$fn = 32;

marble_d = 16;
ch_w = marble_d + 3.6;
wall = 2.4;
floor_t = 2.2;
wall_h = 8;
outer_w = ch_w + 2 * wall;

// 1.5 in stack pitch, 1 in cylinder. Ring rides on the 1 in neck.
// Short column segments, about as tall as they are wide, like the colored bands.
seated = 28;
cyl_d = 24;
flange_d = 32;
air = 0.25;
trap_h = 5.4;
ring_h = 3.2;
shoulder_top = seated - trap_h;
neck_top = seated - air;
peg_d = 12.0;
peg_h = 6.6;
socket_d = peg_d + 0.40 + fit_extra;
rib_d = peg_d + 0.80;
groove_d = socket_d + 1.6;

ring_id = cyl_d + 0.85 + fit_extra;
ring_od = 34;

lip = 26; // chute mouth stops here, just outside the column
hinge_x = 18;
hinge_y = 16; // small ear on the side of the collar, not a long arm
pin_d = 4.2;
pin_hole = 5.4 + fit_extra;
pin_z = 5.4;
path_y = 0;
past = 0;

module rz(a) { rotate([0, 0, a]) children(); }

module text_line(s, size=5) {
    text(s, size=size, font="Liberation Sans:style=Bold",
         halign="center", valign="center", $fn=12);
}

// ---------- shared top joint (shoulder, neck, peg) ----------

module neck_and_peg(seat_z) {
    neck_h = trap_h - air;
    translate([0, 0, seat_z - trap_h - 0.2])
        cylinder(d=cyl_d, h=neck_h + 0.4, $fn=48);
    translate([0, 0, seat_z - air]) {
        cylinder(d=peg_d, h=peg_h - 1.1, $fn=40);
        translate([0, 0, peg_h - 1.2])
            cylinder(d1=peg_d, d2=peg_d - 2.2, h=1.2, $fn=40);
        translate([0, 0, 3.1])
            cylinder(d=rib_d, h=1.15, $fn=40);
    }
}

module socket_void() {
    translate([0, 0, -0.2])
        cylinder(d=socket_d, h=8.2, $fn=40);
    translate([0, 0, 2.55])
        cylinder(d=groove_d, h=2.15, $fn=40);
}

module peg_slot(seat_z) {
    // Slot lets the peg spring past the rib, then relax into the groove.
    translate([-0.6, -peg_d, seat_z - air + 0.8])
        cube([1.2, peg_d * 2, peg_h]);
}

// ---------- connector and foot ----------

module connector() {
    difference() {
        union() {
            cylinder(d=flange_d, h=3.2, $fn=48);
            translate([0, 0, 3.0])
                cylinder(d=cyl_d, h=shoulder_top - 3.0 - 2.8, $fn=48);
            translate([0, 0, shoulder_top - 3.0])
                cylinder(d=flange_d, h=3.0, $fn=48);
            neck_and_peg(seated);
        }
        socket_void();
        peg_slot(seated);
    }
}

foot_seat = 5.2 + trap_h;

module foot() {
    difference() {
        union() {
            translate([-34, -34, 0]) cube([68, 68, 5]);
            translate([0, 0, 4.2]) cylinder(d=cyl_d, h=1.4, $fn=48);
            neck_and_peg(foot_seat);
        }
        peg_slot(foot_seat);
    }
    translate([0, 22, 4.45])
        linear_extrude(0.9)
            text_line("BF", 6);
}

// ---------- captive ring and hinge ----------
// The ring and the track must not touch. The pin bridges the gap.

module ring_only() {
    difference() {
        union() {
            cylinder(d=ring_od, h=ring_h, $fn=48);
            // Short lug toward the ear. Stays off the chute.
            translate([10, 13.6, 0])
                cube([10, 6, ring_h]);
            translate([hinge_x, hinge_y, pin_z])
                rotate([-90, 0, 0])
                    cylinder(d=knuckle_d(), h=5.2, center=true, $fn=20);
        }
        translate([0, 0, -0.4])
            cylinder(d=ring_id, h=ring_h + 0.8, $fn=48);
        translate([hinge_x, hinge_y, pin_z])
            rotate([-90, 0, 0])
                cylinder(d=pin_hole, h=12, center=true, $fn=16);
    }
}

function knuckle_d() = pin_hole + 3.2;

module track_pin() {
    translate([hinge_x, hinge_y - 1, pin_z])
        rotate([-90, 0, 0])
            cylinder(d=pin_d, h=12, center=true, $fn=14);
    // Cheek from the chute wall up to the knuckle. Stops clear of the collar.
    translate([hinge_x - 4, outer_w / 2 - wall, 0])
        cube([14, (hinge_y - 4.0) - (outer_w / 2 - wall), pin_z + 1.4]);
}

module place_end(x, y, ang) {
    translate([x, y, 0]) rz(ang) children();
}

// ---------- channels ----------

module straight_channel(x0, x1, wh=wall_h, y0=0) {
    translate([x0, y0 - outer_w / 2, 0])
        cube([x1 - x0, outer_w, floor_t]);
    for (s = [-1, 1])
        translate([x0, y0 + s * outer_w / 2 - (s > 0 ? wall : 0), floor_t - 0.12])
            cube([x1 - x0, wall, wh]);
}

module inlet_cup() {
    // Tray behind the column. Kept off the collar so the hinge stays free.
    r = 34;
    difference() {
        union() {
            for (i = [0:4]) {
                a0 = 155 + i * 16;
                a1 = a0 + 16;
                hull() {
                    translate([r * cos(a0), r * sin(a0), 0])
                        cylinder(r=6, h=floor_t, $fn=8);
                    translate([r * cos(a1), r * sin(a1), 0])
                        cylinder(r=6, h=floor_t, $fn=8);
                }
            }
            hull() {
                translate([r * cos(215), r * sin(215), 0])
                    cylinder(r=4, h=floor_t, $fn=8);
                translate([-18, -26, 0])
                    cylinder(r=4, h=floor_t, $fn=8);
            }
            hull() {
                translate([-18, -26, 0])
                    cylinder(r=4, h=floor_t, $fn=8);
                translate([24, -20, 0])
                    cylinder(r=4, h=floor_t, $fn=8);
            }
            hull() {
                translate([24, -20, 0])
                    cylinder(r=4, h=floor_t, $fn=8);
                translate([lip, -outer_w / 2, 0])
                    cube([10, 8, floor_t]);
            }
        }
    }
}

module lane_body(span, wh) {
    straight_channel(lip, span - lip, wh, 0);
    inlet_cup();
}

module flare(x_post, dir) {
    // Wider, taller mouth. Each wall is its own hull so the chute stays open.
    x0 = x_post + dir * lip;
    x1 = x_post + dir * (lip + 14);
    lo = min(x0, x1);
    hi = max(x0, x1);
    hull() {
        translate([lo, -16, 0]) cube([0.4, 32, floor_t]);
        translate([hi, -outer_w / 2, 0]) cube([0.4, outer_w, floor_t]);
    }
    for (s = [-1, 1])
        hull() {
            translate([lo, s * 16 - (s > 0 ? wall : 0), 0])
                cube([0.4, wall, 17]);
            translate([hi, s * outer_w / 2 - (s > 0 ? wall : 0), floor_t - 0.2])
                cube([0.4, wall, wall_h + 0.4]);
        }
}

module mark_wall(x, s) {
    translate([x, -outer_w / 2 + 0.15, floor_t + wall_h / 2])
        rotate([90, 0, 0])
            linear_extrude(0.9)
                text_line(s, 4.6);
}

function kit_qty(id) =
    id == "CN" ? 80 :
    id == "L" || id == "M" || id == "BF" ? 8 :
    id == "S" ? 6 :
    id == "CL" || id == "CR" ? 3 :
    id == "CB" || id == "SF" ? 4 :
    2;

module span_track(span, label, wh=wall_h) {
    difference() {
        union() {
            lane_body(span, wh);
            place_end(0, 0, 0) track_pin();
            translate([span, 0, 0]) scale([-1, 1, 1]) track_pin();
        }
        translate([span / 2, path_y - outer_w / 2 + 0.15, floor_t + wall_h / 2])
            rotate([90, 0, 0])
                linear_extrude(0.9)
                    text_line(str(label, " x", kit_qty(label)), 4.6);
    }
    place_end(0, 0, 0) ring_only();
    translate([span, 0, 0]) scale([-1, 1, 1]) ring_only();
}

module profile_solid(wh=wall_h) {
    translate([-1.1, -outer_w / 2, 0])
        cube([2.2, outer_w, floor_t]);
    for (s = [-1, 1])
        translate([-1.1, s * outer_w / 2 - (s > 0 ? wall : 0), floor_t - 0.12])
            cube([2.2, wall, wh]);
}

module profile_void(wh=wall_h) {
    translate([-1.6, -ch_w / 2, floor_t - 0.01])
        cube([3.2, ch_w, wh + 6]);
}

module arc_track(cx, cy, r, a0, a1, n, wh=wall_h) {
    for (i = [0:n - 1]) {
        a = a0 + (a1 - a0) * i / n;
        b = a0 + (a1 - a0) * (i + 1) / n;
        hull() {
            translate([cx + r * cos(a), cy + r * sin(a), 0])
                rz(a + 90) profile_solid(wh);
            translate([cx + r * cos(b), cy + r * sin(b), 0])
                rz(b + 90) profile_solid(wh);
        }
    }
}

module arc_void(cx, cy, r, a0, a1, n, wh=wall_h) {
    for (i = [0:n - 1]) {
        a = a0 + (a1 - a0) * i / n;
        b = a0 + (a1 - a0) * (i + 1) / n;
        hull() {
            translate([cx + r * cos(a), cy + r * sin(a), 0])
                rz(a + 90) profile_void(wh);
            translate([cx + r * cos(b), cy + r * sin(b), 0])
                rz(b + 90) profile_void(wh);
        }
    }
}

module bend(sign) {
    r = 52;
    n = 10;
    a0 = sign > 0 ? -90 : 90;
    a1 = 0;
    cy = sign * r;
    end_a = a1;
    // CCW travel heads a+90. CW travel heads a-90.
    end_h = sign > 0 ? end_a + 90 : end_a - 90;
    end_pt = [lip + r * cos(end_a), cy + r * sin(end_a)];
    post = [end_pt[0] + lip * cos(end_h), end_pt[1] + lip * sin(end_h)];
    difference() {
        union() {
            arc_track(lip, cy, r, a0, a1, n);
            place_end(0, 0, 0) track_pin();
            place_end(post[0], post[1], end_h + 180) track_pin();
        }
        arc_void(lip, cy, r, a0, a1, n);
        translate([lip + 16, sign * 18, floor_t + 6])
            rotate([90, 0, sign > 0 ? 180 : 0])
                linear_extrude(0.9)
                    text_line(str(sign > 0 ? "CL" : "CR", " x3"), 4.2);
    }
    place_end(0, 0, 0) ring_only();
    place_end(post[0], post[1], end_h + 180) ring_only();
}

module uturn() {
    r = 36;
    n = 14;
    a0 = -90;
    a1 = 90;
    end_h = a1 + 90;
    end_pt = [lip + r * cos(a1), r + r * sin(a1)];
    post = [end_pt[0] + lip * cos(end_h), end_pt[1] + lip * sin(end_h)];
    difference() {
        union() {
            arc_track(lip, r, r, a0, a1, n, 14);
            place_end(0, 0, 0) track_pin();
            place_end(post[0], post[1], end_h + 180) track_pin();
        }
        arc_void(lip, r, r, a0, a1, n, 14);
    }
    place_end(0, 0, 0) ring_only();
    place_end(post[0], post[1], end_h + 180) ring_only();
}

module vortex() {
    r = 56;
    n = 18;
    a0 = -90;
    a1 = 180;
    // Keep the mouth closer than a straight chute so the 270° arc
    // does not run into its own ring.
    approach = 20;
    cy = r;
    end_h = a1 + 90;
    end_pt = [approach + r * cos(a1), cy + r * sin(a1)];
    post = [end_pt[0] + approach * cos(end_h), end_pt[1] + approach * sin(end_h)];
    difference() {
        union() {
            arc_track(approach, cy, r, a0, a1, n, 16);
            place_end(0, 0, 0) track_pin();
            place_end(post[0], post[1], end_h + 180) track_pin();
        }
        arc_void(approach, cy, r, a0, a1, n, 16);
        translate([28, -outer_w / 2 + 0.15, floor_t + 7])
            rotate([90, 0, 0])
                linear_extrude(0.9)
                    text_line("WH x2", 4.4);
    }
    place_end(0, 0, 0) ring_only();
    place_end(post[0], post[1], end_h + 180) ring_only();
}

module bumps(span) {
    difference() {
        union() {
            span_track(span, "ZZ");
            for (i = [0:4])
                translate([38 + i * 16, path_y - ch_w / 2 + 1.2, floor_t - 0.1])
                    cube([3.2, ch_w - 2.4, 2.7]);
        }
    }
}

module hopper(top_d, label, tangent=0) {
    h = max(20, top_d * 0.40);
    ring_x = top_d / 2 + 26;
    difference() {
        union() {
            cylinder(d1=30, d2=top_d, h=h, $fn=64);
            translate([0, tangent, 0]) {
                translate([6, -outer_w / 2, 0])
                    cube([ring_x - 28, outer_w, floor_t + wall_h]);
                place_end(ring_x, 0, 180) track_pin();
            }
        }
        translate([0, 0, 2.2])
            cylinder(d1=20, d2=top_d - 8, h=h, $fn=64);
        translate([0, tangent, 0])
            translate([-8, -ch_w / 2, floor_t])
                cube([ring_x - 24, ch_w, wall_h + 10]);
        translate([0, -top_d / 2 + wall + 0.2, h * 0.45])
            rotate([90, 0, 0])
                linear_extrude(0.9)
                    text_line(label, 6);
    }
    translate([0, tangent, 0])
        place_end(ring_x, 0, 180) ring_only();
}

module catch() {
    difference() {
        union() {
            translate([54, 0, 0])
                cylinder(d=58, h=20, $fn=48);
            straight_channel(lip, 42);
            place_end(0, 0, 0) track_pin();
        }
        translate([54, 0, 3])
            cylinder(d=48, h=20, $fn=48);
        translate([lip, -ch_w / 2, floor_t])
            cube([40, ch_w, wall_h + 4]);
        translate([54, 0, 18.2])
            linear_extrude(1.1)
                text_line("CB", 6);
    }
    place_end(0, 0, 0) ring_only();
}

module wye_body() {
    ang = 28;
    reach = 64;
    jx = 42;
    difference() {
        union() {
            straight_channel(lip, jx);
            translate([jx - 8, -22, 0])
                cube([30, 44, floor_t]);
            translate([jx - 8, -22, floor_t - 0.1])
                cube([30, wall, 12]);
            translate([jx - 8, 22 - wall, floor_t - 0.1])
                cube([30, wall, 12]);
            translate([jx + 6, 0, 0]) {
                rz(ang) straight_channel(-4, reach - 20);
                rz(-ang) straight_channel(-4, reach - 20);
                // Hinge on the outside of each branch so the two rings do not meet.
                rz(ang) translate([reach, 0, 0]) scale([-1, 1, 1]) track_pin();
                rz(-ang) place_end(reach, 0, 180) track_pin();
            }
            place_end(0, 0, 0) track_pin();
        }
        translate([jx - 4, -16, floor_t])
            cube([22, 32, 16]);
        translate([jx + 6, 0, 0]) {
            rz(ang) translate([0, -ch_w / 2, floor_t])
                cube([reach - 38, ch_w, 16]);
            rz(-ang) translate([0, -ch_w / 2, floor_t])
                cube([reach - 38, ch_w, 16]);
        }
    }
    hull() {
        translate([jx + 2, -0.5, floor_t - 0.3])
            cube([1, 1, 2.2]);
        translate([jx + 18, -2.4, floor_t - 0.3])
            cube([2.4, 4.8, 7]);
    }
}

module wye_rings() {
    ang = 28;
    reach = 64;
    jx = 42;
    place_end(0, 0, 0) ring_only();
    translate([jx + 6, 0, 0]) {
        rz(ang) translate([reach, 0, 0]) scale([-1, 1, 1]) ring_only();
        rz(-ang) place_end(reach, 0, 180) ring_only();
    }
}

module wye() {
    wye_body();
    wye_rings();
}

module split() {
    wye();
    translate([28, -outer_w / 2 + 0.2, floor_t + 5])
        rotate([90, 0, 0])
            linear_extrude(0.9)
                text_line("YS x2", 4.4);
}

module merge() {
    scale([-1, 1, 1]) wye();
    translate([-28, -outer_w / 2 + 0.2, floor_t + 5])
        rotate([90, 0, 0])
            linear_extrude(0.9)
                text_line("MG x2", 4.4);
}

module spinner() {
    difference() {
        union() {
            cylinder(d=60, h=4.2, $fn=48);
            translate([0, 0, 4.0])
                cylinder(d=56, h=14, $fn=48);
            straight_channel(18, 22);
            translate([-52, 0, 0]) straight_channel(0, 34);
            translate([30, 0, 0]) straight_channel(0, 28);
            translate([-52 - lip, 0, 0]) place_end(0, 0, 0) track_pin();
            translate([58 + lip, 0, 0]) place_end(0, 0, 180) track_pin();
            translate([0, 0, 3.4])
                cylinder(d=12, h=2.2, $fn=24);
            translate([0, 0, 3.6])
                cylinder(d=5.0, h=12, $fn=20);
            translate([0, 0, 14.6])
                cylinder(d=12, h=2.4, $fn=24);
        }
        translate([0, 0, 5.2])
            cylinder(d=48, h=16, $fn=48);
        translate([-46, -ch_w / 2, floor_t])
            cube([30, ch_w, wall_h + 4]);
        translate([16, -ch_w / 2, floor_t])
            cube([28, ch_w, wall_h + 4]);
        translate([0, 0, 15.6])
            linear_extrude(1.1)
                text_line("SN", 5);
    }
    // Captive paddle wheel. Clear of the axle and the bowl.
    translate([0, 0, 6.4]) {
        difference() {
            union() {
                cylinder(d=18, h=3.4, $fn=28);
                for (k = [0:3])
                    rz(k * 90)
                        translate([2, -1.5, 0])
                            cube([16, 3.0, 7.2]);
            }
            translate([0, 0, -0.4])
                cylinder(d=6.6, h=5, $fn=20);
        }
    }
    translate([-52 - lip, 0, 0]) place_end(0, 0, 0) ring_only();
    translate([58 + lip, 0, 0]) place_end(0, 0, 180) ring_only();
}

module gauge() {
    difference() {
        cube([88, 40, 3.2], center=false);
        translate([24, 20, -1]) cylinder(d=16.7, h=6, $fn=40);
        translate([62, 20, -1]) cylinder(d=15.5, h=6, $fn=40);
        translate([24, 8, 2.2])
            linear_extrude(1.2) text_line("GO", 5);
        translate([62, 8, 2.2])
            linear_extrude(1.2) text_line("NO", 5);
    }
}

module build() {
    if (part == "CN") connector();
    else if (part == "BF") foot();
    else if (part == "S") span_track(100, "S");
    else if (part == "M") span_track(128, "M");
    else if (part == "L") span_track(146, "L");
    else if (part == "CL") bend(1);
    else if (part == "CR") bend(-1);
    else if (part == "UT") uturn();
    else if (part == "SW") span_track(110, "SW", 14);
    else if (part == "ZZ") bumps(140);
    else if (part == "WH") vortex();
    else if (part == "CB") catch();
    else if (part == "YS") split();
    else if (part == "MG") merge();
    else if (part == "SN") spinner();
    else if (part == "SF") hopper(52, "SF");
    else if (part == "VF") hopper(78, "VF", 14);
    else if (part == "LG") gauge();
    else if (part == "DEMO") demo();
    else echo("UNKNOWN", part);
}

module demo() {
    z = foot_seat + shoulder_top + 0.55;
    color([0.62, 0.78, 0.86]) foot();
    color([0.75, 0.88, 0.94]) translate([0, 0, foot_seat]) connector();
    color([0.75, 0.88, 0.94]) translate([0, 0, foot_seat + seated]) connector();
    color([0.62, 0.78, 0.86]) translate([120, 0, 0]) foot();
    color([0.75, 0.88, 0.94]) translate([120, 0, foot_seat]) connector();
    color([0.75, 0.88, 0.94]) translate([120, 0, foot_seat + seated]) connector();
    color([0.93, 0.55, 0.22]) translate([0, 0, z]) span_track(120, "M");
}

// Ring seat height. Level 0 is the foot. Level 1 is the first connector.
function ring_z(level) =
    level <= 0 ? 4.85
    : foot_seat + shoulder_top + 0.55 + (level - 1) * seated;

function pin_run(span) = span - 2 * hinge_x;
function slope_angle(span, drop) = asin(drop / pin_run(span));
function post_gap(span, drop) = 2 * hinge_x + pin_run(span) * cos(slope_angle(span, drop));

module tower(levels) {
    color([0.55, 0.74, 0.82]) foot();
    for (i = [0:levels])
        color([0.62, 0.80, 0.88])
            translate([0, 0, foot_seat + i * seated])
                connector();
}

module chute_only(span, label, wh=wall_h) {
    difference() {
        union() {
            lane_body(span, wh);
            place_end(0, 0, 0) track_pin();
            translate([span, 0, 0]) scale([-1, 1, 1]) track_pin();
        }
        translate([span / 2, path_y - outer_w / 2 + 0.15, floor_t + wall_h / 2])
            rotate([90, 0, 0])
                linear_extrude(0.9)
                    text_line(str(label, " x", kit_qty(label)), 4.6);
    }
}

module sloped_chute(span, z_high, drop) {
    theta = slope_angle(span, drop);
    translate([hinge_x, hinge_y, z_high + pin_z])
        rotate([0, theta, 0])
            translate([-hinge_x, -hinge_y, -pin_z])
                children();
}

module marble_on_chute(span, sink=0) {
    zc = floor_t + marble_d / 2 + 0.35 - sink;
    for (x = [lip + 6 : 22 : span - lip - 6])
        translate([x, 0, zc])
            sphere(d=marble_d, $fn=16);
}

module run_world(span, high, low, label, wh=wall_h) {
    drop = ring_z(high) - ring_z(low);
    gap = post_gap(span, drop);
    echo(str(label, " drop ", drop, " angle ", slope_angle(span, drop), " post_gap ", gap));
    tower(high);
    translate([gap, 0, 0]) tower(low);
    color([0.93, 0.52, 0.18])
        sloped_chute(span, ring_z(high), drop)
            chute_only(span, label, wh);
    color([0.95, 0.75, 0.35]) {
        translate([0, 0, ring_z(high)]) ring_only();
        translate([gap, 0, ring_z(low)]) scale([-1, 1, 1]) ring_only();
    }
}

module run_balls(span, high, low, sink=0) {
    drop = ring_z(high) - ring_z(low);
    color([0.82, 0.12, 0.10])
        sloped_chute(span, ring_z(high), drop)
            marble_on_chute(span, sink);
}

module photo_run() {
    // A small build in the same arrangement as the clear column sets:
    // square feet, short segments, slim chutes stepping down.
    span = 100;
    drop = ring_z(2) - ring_z(1);
    gap = post_gap(span, drop);
    module one_tower(col) {
        color(col) {
            foot();
            for (i = [0:4])
                translate([0, 0, foot_seat + i * seated])
                    connector();
        }
    }
    one_tower([0.95, 0.35, 0.15]);
    translate([gap, 0, 0]) one_tower([0.15, 0.75, 0.35]);
    translate([gap * 2, 0, 0]) one_tower([0.25, 0.45, 0.95]);
    color([0.95, 0.75, 0.15])
        run_span_only(span, 4, 3, gap * 0);
    color([0.20, 0.85, 0.75])
        translate([gap, 0, 0])
            run_span_only(span, 2, 1, 0);
    color([0.85, 0.25, 0.55]) {
        run_balls(span, 4, 3);
        translate([gap, 0, 0])
            run_balls(span, 2, 1);
    }
}

module run_span_only(span, high, low, shift) {
    drop = ring_z(high) - ring_z(low);
    translate([shift, 0, 0]) {
        sloped_chute(span, ring_z(high), drop)
            chute_only(span, "S");
        translate([0, 0, ring_z(high)]) ring_only();
        translate([post_gap(span, drop), 0, ring_z(low)]) scale([-1, 1, 1]) ring_only();
    }
}

module run_straight(span, high, low, label, wh=wall_h) {
    run_world(span, high, low, label, wh);
    run_balls(span, high, low);
}

// High long chute into a lower continuation. The red balls on the second
// chute are the landing. Balls between the towers are the free flight.
module run_transfer() {
    span1 = 164;
    span2 = 156;
    drop1 = ring_z(3) - ring_z(2);
    drop2 = ring_z(1) - ring_z(0);
    gap1 = post_gap(span1, drop1);
    gap2 = post_gap(span2, drop2);
    echo(str("transfer L angle ", slope_angle(span1, drop1), " M angle ", slope_angle(span2, drop2)));
    tower(3);
    translate([gap1, 0, 0]) tower(2);
    translate([gap1 + gap2, 0, 0]) tower(0);
    color([0.93, 0.52, 0.18]) {
        sloped_chute(span1, ring_z(3), drop1) chute_only(span1, "L");
        translate([gap1, 0, 0])
            sloped_chute(span2, ring_z(1), drop2) chute_only(span2, "M");
    }
    color([0.95, 0.75, 0.35]) {
        translate([0, 0, ring_z(3)]) ring_only();
        translate([gap1, 0, ring_z(2)]) scale([-1, 1, 1]) ring_only();
        translate([gap1, 0, ring_z(1)]) ring_only();
        translate([gap1 + gap2, 0, ring_z(0)]) scale([-1, 1, 1]) ring_only();
    }
    color([0.82, 0.12, 0.10]) {
        sloped_chute(span1, ring_z(3), drop1) marble_on_chute(span1);
        translate([gap1, 0, 0])
            sloped_chute(span2, ring_z(1), drop2) marble_on_chute(span2);
    }
}

module track_end_solid() {
    straight_channel(lip, lip + 24);
    track_pin();
}

if (mode == "part") build();
else if (mode == "stack")
    intersection() {
        connector();
        translate([0, 0, seated]) connector();
    }
else if (mode == "ringfit")
    intersection() {
        connector();
        translate([0, 0, shoulder_top + 0.55]) ring_only();
    }
else if (mode == "clear")
    intersection() {
        ring_only();
        track_end_solid();
    }
else if (mode == "fit")
    intersection() {
        span_track(156, "M");
        for (x = [40:24:120])
            translate([x, 0, floor_t + marble_d / 2 + 0.45])
                sphere(d=marble_d, $fn=14);
    }
else if (mode == "footstack")
    intersection() {
        foot();
        translate([0, 0, foot_seat]) connector();
    }
else if (mode == "footring")
    intersection() {
        foot();
        translate([0, 0, 5.45]) ring_only();
    }
else if (mode == "ysfit")
    intersection() {
        wye();
        for (x = [30, 40])
            translate([x, 0, floor_t + marble_d / 2 + 0.4])
                sphere(d=marble_d, $fn=12);
        for (s = [-1, 1])
            translate([48, 0, 0]) rz(s * 28)
                for (x = [12, 28, 44])
                    translate([x, 0, floor_t + marble_d / 2 + 0.4])
                        sphere(d=marble_d, $fn=12);
    }
else if (mode == "hopfit")
    intersection() {
        hopper(52, "SF");
        translate([0, 0, 12]) sphere(d=marble_d, $fn=12);
        for (x = [14, 28, 42])
            translate([x, 0, floor_t + marble_d / 2 + 0.4])
                sphere(d=marble_d, $fn=12);
    }
else if (mode == "photo") photo_run();
else if (mode == "runL") run_straight(156, 3, 2, "L");
else if (mode == "runLclear")
    intersection() {
        run_world(164, 2, 1, "L");
        run_balls(164, 2, 1, 0);
    }
else if (mode == "runLsit")
    intersection() {
        run_world(164, 2, 1, "L");
        run_balls(164, 2, 1, 1.2);
    }
else if (mode == "runS") run_straight(132, 2, 1, "S");
else if (mode == "runSclear")
    intersection() {
        run_world(132, 2, 1, "S");
        run_balls(132, 2, 1, 0);
    }
else if (mode == "runSsit")
    intersection() {
        run_world(132, 2, 1, "S");
        run_balls(132, 2, 1, 1.2);
    }
else if (mode == "runSW") run_straight(150, 2, 0, "SW", 18);
else if (mode == "runSWclear")
    intersection() {
        run_world(150, 2, 0, "SW", 18);
        run_balls(150, 2, 0, 0);
    }
else if (mode == "runSWsit")
    intersection() {
        run_world(150, 2, 0, "SW", 18);
        run_balls(150, 2, 0, 1.2);
    }
else if (mode == "runT") run_transfer();
else if (mode == "runTland")
    intersection() {
        translate([post_gap(164, ring_z(3) - ring_z(2)), 0, 0])
            sloped_chute(156, ring_z(1), ring_z(1) - ring_z(0))
                chute_only(156, "M");
        translate([post_gap(164, ring_z(3) - ring_z(2)), 0, 0])
            sloped_chute(156, ring_z(1), ring_z(1) - ring_z(0))
                translate([18, path_y, floor_t + marble_d / 2 + 0.35])
                    sphere(d=marble_d, $fn=16);
    }
else if (mode == "runTlandsit")
    intersection() {
        translate([post_gap(164, ring_z(3) - ring_z(2)), 0, 0])
            sloped_chute(156, ring_z(1), ring_z(1) - ring_z(0))
                chute_only(156, "M");
        translate([post_gap(164, ring_z(3) - ring_z(2)), 0, 0])
            sloped_chute(156, ring_z(1), ring_z(1) - ring_z(0))
                translate([18, path_y, floor_t + marble_d / 2 - 0.85])
                    sphere(d=marble_d, $fn=16);
    }
else if (mode == "runLplastic")
    intersection() {
        tower(2);
        translate([post_gap(164, ring_z(2) - ring_z(1)), 0, 0]) tower(1);
        translate([0, 0, ring_z(2)]) ring_only();
        translate([post_gap(164, ring_z(2) - ring_z(1)), 0, ring_z(1)]) rz(180) ring_only();
        sloped_chute(164, ring_z(2), ring_z(2) - ring_z(1))
            chute_only(164, "L");
    }
else if (mode == "runLexit")
    intersection() {
        run_world(164, 2, 1, "L");
        sloped_chute(164, ring_z(2), ring_z(2) - ring_z(1))
            translate([164 - lip, 0, floor_t + marble_d / 2 + 0.35])
                sphere(d=marble_d, $fn=16);
    }
else if (mode == "runLand")
    intersection() {
        translate([post_gap(164, ring_z(2) - ring_z(1)), 0, 0])
            sloped_chute(156, ring_z(1), ring_z(1) - ring_z(0))
                chute_only(156, "M");
        translate([post_gap(164, ring_z(2) - ring_z(1)), 0, 0])
            sloped_chute(156, ring_z(1), ring_z(1) - ring_z(0))
                translate([-past + 6, path_y, floor_t + marble_d / 2 + 0.35])
                    sphere(d=marble_d, $fn=16);
    }
else if (mode == "runLandsit")
    intersection() {
        translate([post_gap(164, ring_z(2) - ring_z(1)), 0, 0])
            sloped_chute(156, ring_z(1), ring_z(1) - ring_z(0))
                chute_only(156, "M");
        translate([post_gap(164, ring_z(2) - ring_z(1)), 0, 0])
            sloped_chute(156, ring_z(1), ring_z(1) - ring_z(0))
                translate([-past + 6, path_y, floor_t + marble_d / 2 - 0.8])
                    sphere(d=marble_d, $fn=16);
    }
else if (mode == "runLandpost")
    intersection() {
        translate([post_gap(164, ring_z(2) - ring_z(1)), 0, 0]) tower(2);
        translate([post_gap(164, ring_z(2) - ring_z(1)), 0, 0])
            sloped_chute(156, ring_z(1), ring_z(1) - ring_z(0))
                translate([-past + 6, path_y, floor_t + marble_d / 2 + 0.35])
                    sphere(d=marble_d, $fn=16);
    }
else if (mode == "runSexit")
    intersection() {
        run_world(132, 2, 1, "S");
        sloped_chute(132, ring_z(2), ring_z(2) - ring_z(1))
            translate([132 - lip, 0, floor_t + marble_d / 2 + 0.35])
                sphere(d=marble_d, $fn=16);
    }
else if (mode == "runSWexit")
    intersection() {
        run_world(150, 2, 0, "SW", 18);
        sloped_chute(150, ring_z(2), ring_z(2) - ring_z(0))
            translate([150 - lip, 0, floor_t + marble_d / 2 + 0.35])
                sphere(d=marble_d, $fn=16);
    }
