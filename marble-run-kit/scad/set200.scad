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
wall_h = 12;
outer_w = ch_w + 2 * wall;

// 1.5 in stack pitch, 1 in cylinder. Ring rides on the 1 in neck.
seated = 38.1;
cyl_d = 25.4;
flange_d = 34;
air = 0.30;
trap_h = 6.8;
ring_h = 4.8;
shoulder_top = seated - trap_h;
neck_top = seated - air;
peg_d = 14.0;
peg_h = 7.4;
socket_d = peg_d + 0.40 + fit_extra;
rib_d = peg_d + 0.90;
groove_d = socket_d + 1.8;

ring_id = cyl_d + 0.90 + fit_extra;
ring_od = 40;

lip = 18.5;
hinge_x = 24;
hinge_y = 28;
pin_d = 5.0;
pin_hole = 6.4 + fit_extra;
pin_z = 6.2;

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

foot_seat = 4.2 + trap_h;

module foot() {
    difference() {
        union() {
            cylinder(d=72, h=4.4, $fn=64);
            neck_and_peg(foot_seat);
        }
        peg_slot(foot_seat);
    }
    translate([0, 24, 4.05])
        linear_extrude(1.0)
            text_line("BF", 7);
}

// ---------- captive ring and hinge ----------
// The ring and the track must not touch. The pin bridges the gap.

module ring_only() {
    difference() {
        union() {
            cylinder(d=ring_od, h=ring_h, $fn=48);
            translate([7, 6, 0])
                cube([8, 26, ring_h]);
            translate([7, 25.4, 0])
                cube([22, 5.2, ring_h]);
            translate([hinge_x, hinge_y, pin_z])
                rotate([-90, 0, 0])
                    cylinder(d=knuckle_d(), h=5.6, center=true, $fn=24);
        }
        translate([0, 0, -0.4])
            cylinder(d=ring_id, h=ring_h + 0.8, $fn=48);
        // Open the cap toward the chute so the floor can reach the post.
        translate([16.2, -14, -0.6])
            cube([12, 28, ring_h + 1.2]);
        translate([hinge_x, hinge_y, pin_z])
            rotate([-90, 0, 0])
                cylinder(d=pin_hole, h=16, center=true, $fn=20);
    }
}

function knuckle_d() = pin_hole + 3.6;

module track_pin() {
    // Pin runs through the inner cheek, the knuckle, and the outer cheek.
    translate([hinge_x, 26.6, pin_z])
        rotate([-90, 0, 0])
            cylinder(d=pin_d, h=23.2, center=true, $fn=18);
    translate([19, 9.5, 0])
        cube([12, 7.2, 9.6]);
    translate([17, 14.0, 0])
        cube([14, 10.2, 10]);
    translate([17, 31.8, 0])
        cube([14, 8.0, 10]);
}

module place_end(x, y, ang) {
    translate([x, y, 0]) rz(ang) children();
}

// ---------- channels ----------

module straight_channel(x0, x1, wh=wall_h) {
    translate([x0, -outer_w / 2, 0])
        cube([x1 - x0, outer_w, floor_t]);
    for (s = [-1, 1])
        translate([x0, s * outer_w / 2 - (s > 0 ? wall : 0), floor_t - 0.12])
            cube([x1 - x0, wall, wh]);
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
            straight_channel(lip, span - lip, wh);
            flare(0, 1);
            flare(span, -1);
            place_end(0, 0, 0) track_pin();
            place_end(span, 0, 180) track_pin();
        }
        mark_wall(span / 2, str(label, " x", kit_qty(label)));
    }
    place_end(0, 0, 0) ring_only();
    place_end(span, 0, 180) ring_only();
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
    cy = r;
    end_h = a1 + 90;
    end_pt = [lip + r * cos(a1), cy + r * sin(a1)];
    post = [end_pt[0] + lip * cos(end_h), end_pt[1] + lip * sin(end_h)];
    difference() {
        union() {
            arc_track(lip, cy, r, a0, a1, n, 16);
            place_end(0, 0, 0) track_pin();
            place_end(post[0], post[1], end_h + 180) track_pin();
        }
        arc_void(lip, cy, r, a0, a1, n, 16);
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
                translate([38 + i * 16, -ch_w / 2 + 1.2, floor_t - 0.1])
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
            translate([46, 0, 0])
                cylinder(d=58, h=20, $fn=48);
            straight_channel(lip, 36);
            place_end(0, 0, 0) track_pin();
        }
        translate([46, 0, 3])
            cylinder(d=48, h=20, $fn=48);
        translate([lip, -ch_w / 2, floor_t])
            cube([40, ch_w, wall_h + 4]);
        translate([46, 0, 18.2])
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
    else if (part == "S") span_track(86, "S");
    else if (part == "M") span_track(120, "M");
    else if (part == "L") span_track(156, "L");
    else if (part == "CL") bend(1);
    else if (part == "CR") bend(-1);
    else if (part == "UT") uturn();
    else if (part == "SW") span_track(92, "SW", 18);
    else if (part == "ZZ") bumps(124);
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

module track_end_solid() {
    straight_channel(lip, lip + 28);
    flare(0, 1);
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
        span_track(120, "M");
        for (x = [36:12:84])
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
        translate([0, 0, 4.7]) ring_only();
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
