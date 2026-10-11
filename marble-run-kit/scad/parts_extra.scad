// Remaining marble-run parts. Included from marble_kit.scad.
// All modules are print-oriented: bed is z = 0, open channels face +z.

module label_of(id, qty, x, ang=0, size=4.4) {
    translate([x, 0, 0]) rz(ang)
        side_label(0, qty_lines(id, qty), size);
}

// ---------- zigzag brake ----------
module part_zz() {
    lead = 12;
    r = 18;
    n = 10;
    // Three straights joined by two tight U-turns.
    module uturn_at(x, y, a0, a1, cx, cy) {
        pts = arc_pts(cx, cy, r, a0, a1, n);
        angs = arc_angs(a0, a1, n);
        sweep(pts, angs, floor_top);
    }
    difference() {
        union() {
            channel_straight(46, floor_top, floor_top);
            // First U, left, centered so it leaves the straight at x=40
            uturn_at(0, 0, -90, 90, 40, r);
            // Return straight along heading 180 from the U end (40, 2r)
            translate([40, 2 * r, 0]) rz(180)
                translate([-2, 0, 0])
                    channel_straight(30, floor_top, floor_top, false);
            // Second U, continuing to +X
            uturn_at(0, 0, 90, -90, 14, 3 * r);
            translate([14, 4 * r, 0])
                translate([-2, 0, 0])
                    channel_straight(36, floor_top, floor_top, false);
        }
        inlet_chamfer_cut();
        inlet_step_cut();
        side_label(24, qty_lines("ZZ", mark_qty), 4.2);
    }
    hinge_female_at(0, 0, 0);
    translate([14 + 34, 4 * r, 0])
        hinge_male_at(0, 0, 0);
}

// ---------- split and merge ----------
module branch_clear() {
    translate([18, 0, floor_top - 0.2])
        cylinder(d=marble_d + 1.2, h=wall_h + 2, $fn=32);
}

module part_ys() {
    difference() {
        union() {
            channel_straight(26, floor_top, floor_top);
            translate([16, 0, 0]) rz(32)
                translate([-2, 0, 0])
                    channel_straight(38, floor_top, floor_top, false);
            translate([16, 0, 0]) rz(-32)
                translate([-2, 0, 0])
                    channel_straight(38, floor_top, floor_top, false);
            // Splitter nose
            translate([22, -1.15, floor_top])
                cube([9, 2.3, 9]);
        }
        branch_clear();
        inlet_chamfer_cut();
        inlet_step_cut();
        side_label(8, qty_lines("YS", mark_qty), 4.0);
    }
    hinge_female_at(0, 0, 0);
    translate([16, 0, 0]) rz(32) translate([36, 0, 0]) hinge_male_at(0, 0, 0);
    translate([16, 0, 0]) rz(-32) translate([36, 0, 0]) hinge_male_at(0, 0, 0);
}

module part_mg() {
    difference() {
        union() {
            translate([0, 0, 0]) rz(32)
                channel_straight(36, floor_top, floor_top);
            translate([0, 0, 0]) rz(-32)
                channel_straight(36, floor_top, floor_top);
            translate([28, 0, 0])
                translate([-6, 0, 0])
                    channel_straight(34, floor_top, floor_top, false);
            // Island that blocks a marble from crossing into the other inlet
            translate([18, -1.15, floor_top])
                cube([10, 2.3, 8]);
        }
        translate([30, 0, floor_top - 0.2])
            cylinder(d=marble_d + 1.2, h=wall_h + 2, $fn=32);
        side_label(40, ["MG", str("x", mark_qty)], 4.0);
    }
    translate([0, 0, 0]) rz(32) hinge_female_at(0, 0, 0);
    translate([0, 0, 0]) rz(-32) hinge_female_at(0, 0, 0);
    translate([56, 0, 0]) hinge_male_at(0, 0, 0);
}

// ---------- funnel, landing, finish ----------
module part_fn() {
    difference() {
        union() {
            cylinder(d1=24, d2=70, h=26, $fn=64);
            translate([6, -outer_w / 2, 0])
                cube([22, outer_w, floor_top + wall_h]);
        }
        translate([0, 0, 2.4])
            cylinder(d1=14, d2=62, h=26, $fn=64);
        translate([2, -ch_w / 2, floor_top - 0.1])
            cube([30, ch_w, wall_h + 4]);
        translate([18, outer_w / 2 + 0.1, 8])
            rotate([90, 0, 0])
                linear_extrude(1.0)
                    text_line("FN", 5);
        translate([18, outer_w / 2 + 0.1, 4.2])
            rotate([90, 0, 0])
                linear_extrude(1.0)
                    text_line(str("x", mark_qty), 3.6);
    }
    translate([28, 0, 0]) hinge_male_at(0, 0, 0);
}

module part_ld() {
    // Wide mouth, no inlet hinge. Narrows to a male hinge.
    difference() {
        union() {
            hull() {
                translate([0, -36, 0]) cube([2, 72, 16]);
                translate([52, -outer_w / 2, 0]) cube([8, outer_w, floor_top + 2]);
            }
            translate([48, -outer_w / 2, 0])
                cube([16, outer_w, floor_top + wall_h]);
            // Tall mouth walls
            translate([0, -36, 0]) cube([28, 3.2, 26]);
            translate([0, 32.8, 0]) cube([28, 3.2, 26]);
            translate([0, -36, 0]) cube([3.2, 72, 26]);
        }
        hull() {
            translate([-0.2, -32, 3.2]) cube([2, 64, 24]);
            translate([50, -ch_w / 2, floor_top]) cube([8, ch_w, wall_h + 6]);
        }
        translate([14, -30, 18])
            linear_extrude(1.2)
                text_line("LD", 6);
    }
    translate([64, 0, 0]) hinge_male_at(0, 0, 0);
}

module part_bx() {
    difference() {
        union() {
            translate([10, -32, 0]) cube([70, 64, 28]);
            channel_straight(22, floor_top, floor_top);
        }
        translate([14, -28, 2.8]) cube([62, 56, 30]);
        // Finger scoops
        translate([48, -36, 20]) cube([18, 10, 12]);
        translate([48, 26, 20]) cube([18, 10, 12]);
        inlet_chamfer_cut();
        inlet_step_cut();
        side_label(6, qty_lines("BX", mark_qty), 4.0);
    }
    hinge_female_at(0, 0, 0);
}

// ---------- jump ----------
module part_jp() {
    z0 = 18; // underside of inlet floor
    difference() {
        union() {
            hull() {
                translate([0, -(outer_w / 2 + 10), 0]) cube([4, outer_w + 20, 2]);
                translate([8, -(outer_w / 2 + 10), z0]) cube([4, outer_w + 20, 2]);
                translate([84, -outer_w / 2, 0]) cube([6, outer_w, 2]);
            }
            hull() {
                translate([10, 0, z0]) profile_solid(floor_top);
                translate([78, 0, 5]) rotate([0, -12, 0]) profile_solid(floor_top);
            }
        }
        hull() {
            translate([10, 0, z0]) profile_void(floor_top);
            translate([78, 0, 5]) rotate([0, -12, 0]) profile_void(floor_top);
        }
        translate([36, 0, z0])
            side_label(0, qty_lines("JP", mark_qty), 4.2);
    }
    translate([0, 0, z0]) hinge_female_at(0, 0, 0);
}

// ---------- waterfall (prints flat; stand it up) ----------
module wf_channel() {
    // Inlet at high Y, travel toward -Y, then a left bend onto +X.
    // Stand the print so the engraved UP arrow points up.
    translate([0, 64, 0]) rz(-90)
        channel_straight(42, floor_top, floor_top);
    // a=-180 heading -Y at (0, 28); a=-90 heading +X at (18, 10)
    sweep(arc_pts(18, 28, 18, -180, -90, 8), arc_angs(-180, -90, 8), floor_top);
    translate([18, 10, 0]) rz(0)
        translate([-4, 0, 0])
            channel_straight(30, floor_top, floor_top, false);
}

module part_wf() {
    difference() {
        wf_channel();
        translate([0, 64, 0]) rz(-90) {
            inlet_chamfer_cut();
            inlet_step_cut();
        }
        translate([-10, 48, 7])
            rotate([90, 0, 0])
                linear_extrude(1.0)
                    text_line("UP", 5);
        translate([-10, 42, 7])
            rotate([90, 0, 0])
                linear_extrude(1.0)
                    text_line("WF", 4);
    }
    translate([0, 64, 0]) rz(-90) hinge_female_at(0, 0, 0);
    translate([44, 10, 0]) hinge_male_at(0, 0, 0);
}

module part_wf_cover() {
    // One solid lid. Flip it onto WF; the rails drop over the outer walls.
    difference() {
        union() {
            hull() {
                translate([-16, 22, 0]) cube([14, 40, 2.4]);
                translate([-2, 6, 0]) cube([40, 18, 2.4]);
            }
            translate([-16, 22, 2.2]) cube([3.2, 40, 6]);
            translate([-6, 22, 2.2]) cube([3.2, 40, 6]);
            translate([-2, 6, 2.2]) cube([40, 3.2, 6]);
            translate([-2, 20.6, 2.2]) cube([40, 3.2, 6]);
        }
        translate([-12, 40, 2.6])
            linear_extrude(1.0)
                text_line("WF-C", 4);
    }
}

// ---------- spiral ----------
module part_sp() {
    R = 32;
    drop = 28;
    n = 20;
    lead = 18;
    a0s = -90;
    sweep_deg = 270;
    zlift = 1.2;
    cx = lead;
    cy = R;
    difference() {
        union() {
            translate([0, 0, drop + zlift])
                channel_straight(lead + 6, floor_top, floor_top);
            for (i = [0:n - 1]) {
                aa = a0s + sweep_deg * i / n;
                ab = a0s + sweep_deg * (i + 1) / n;
                z0 = drop * (1 - i / n) + zlift;
                z1 = drop * (1 - (i + 1) / n) + zlift;
                hull() {
                    translate([cx + R * cos(aa), cy + R * sin(aa), z0])
                        rz(aa + 90) profile_solid(floor_top);
                    translate([cx + R * cos(ab), cy + R * sin(ab), z1])
                        rz(ab + 90) profile_solid(floor_top);
                }
            }
            a_end = a0s + sweep_deg;
            translate([cx + R * cos(a_end), cy + R * sin(a_end), zlift])
                rz(a_end + 90)
                    translate([-5, 0, 0])
                        channel_straight(lead + 5, floor_top, floor_top, false);
            for (i = [0:n]) {
                aa = a0s + sweep_deg * i / n;
                z = drop * (1 - i / n) + zlift;
                translate([cx + R * cos(aa), cy + R * sin(aa), 0])
                    rz(aa + 90)
                        translate([-1.4, -outer_w / 2, 0])
                            cube([2.8, outer_w, z + floor_t]);
            }
        }
        translate([0, 0, drop + zlift]) {
            inlet_chamfer_cut();
            inlet_step_cut();
            side_label(8, qty_lines("SP", mark_qty), 4.2);
        }
        for (i = [0:n - 1]) {
            aa = a0s + sweep_deg * i / n;
            ab = a0s + sweep_deg * (i + 1) / n;
            z0 = drop * (1 - i / n) + zlift;
            z1 = drop * (1 - (i + 1) / n) + zlift;
            hull() {
                translate([cx + R * cos(aa), cy + R * sin(aa), z0])
                    rz(aa + 90) profile_void(floor_top);
                translate([cx + R * cos(ab), cy + R * sin(ab), z1])
                    rz(ab + 90) profile_void(floor_top);
            }
        }
        // Clip any sliver that a tilted profile pushed through the bed.
        translate([-20, -20, -30]) cube([160, 160, 30]);
    }
    translate([0, 0, drop + zlift]) hinge_female_at(0, 0, 0);
    a_end = a0s + sweep_deg;
    translate([cx + R * cos(a_end), cy + R * sin(a_end), zlift])
        rz(a_end + 90)
            translate([lead, 0, 0])
                hinge_male_at(0, 0, 0);
}

// ---------- supports ----------
module part_st_post() {
    difference() {
        union() {
            translate([-17, -17, 0]) cube([34, 34, 20]);
            translate([0, 0, 20]) cylinder(d=12, h=5.4, $fn=32);
            translate([-23, -5, 12]) cube([46, 10, 8]);
            translate([0, 0, 16.2])
                rotate([0, 90, 0])
                    cylinder(d=axle_d, h=46, center=true, $fn=32);
        }
        translate([0, 0, -0.2]) cylinder(d=12.7, h=6.2, $fn=32);
        translate([0, -16, 8])
            rotate([90, 0, 0])
                linear_extrude(1.0)
                    text_line("ST", 5);
    }
}

module part_st_yoke() {
    // U-clip for a track. The round foot drops onto an ST post peg.
    difference() {
        union() {
            translate([-outer_w / 2 - 3.4, -12, 5])
                cube([outer_w + 6.8, 24, 14]);
            cylinder(d=22, h=8, $fn=32);
            // Lips are part of the solid so they stay attached.
            translate([-outer_w / 2 - 3.4, -12, 16.2])
                cube([2.2, 24, 2.2]);
            translate([outer_w / 2 + 1.2, -12, 16.2])
                cube([2.2, 24, 2.2]);
        }
        translate([-outer_w / 2 - 0.4, -14, 7.6])
            cube([outer_w + 0.8, 28, 12]);
        translate([0, 0, -0.2]) cylinder(d=12.7, h=6.4, $fn=32);
        translate([-6, -4, 17.2])
            linear_extrude(1.0)
                text_line("ST-Y", 3.4);
    }
}

// ---------- seesaw ----------
module part_sw_base() {
    difference() {
        union() {
            translate([-28, -16, 0]) cube([70, 32, 8]);
            // Inlet chute
            translate([-46, -outer_w / 2, 6])
                cube([22, outer_w, floor_top + wall_h]);
            // Outlet chute, lower
            translate([36, -outer_w / 2, 0])
                cube([22, outer_w, floor_top + wall_h]);
            // Saddle walls
            translate([-6, -18, 0]) cube([12, 4, 16]);
            translate([-6, 14, 0]) cube([12, 4, 16]);
        }
        translate([-46, -ch_w / 2, 6 + floor_top])
            cube([24, ch_w, wall_h + 2]);
        translate([34, -ch_w / 2, floor_top])
            cube([28, ch_w, wall_h + 2]);
        // Axle saddles, loose
        translate([-20, 0, 11])
            rotate([-90, 0, 0])
                cylinder(d=6.6, h=44, center=true, $fn=24);
        translate([-4.2, -20, 11]) cube([8.4, 40, 12]);
        side_label(-20, ["SW", str("x", mark_qty)], 3.6);
    }
    translate([-46, 0, 6]) hinge_female_at(0, 0, 0);
    translate([58, 0, 0]) hinge_male_at(0, 0, 0);
}

module part_sw_beam() {
    // Printed with the axle just above the bed. In use it sits in SW-B.
    translate([0, 0, -6.6])
    difference() {
        union() {
            translate([-30, -11, 8]) cube([24, 22, 3]);
            translate([-30, -11, 8]) cube([3, 22, 12]);
            translate([-30, -11, 8]) cube([24, 3, 12]);
            translate([-30, 8, 8]) cube([24, 3, 12]);
            translate([-9, -11, 8]) cube([3, 22, 8]);
            translate([6, -8, 8]) cube([28, 16, 10]);
            // Extra tail mass so an empty beam returns, and one glass marble still tips it.
            translate([24, -6, 8]) cube([12, 12, 9]);
            translate([-6, -10, 7]) cube([16, 20, 10]);
            translate([0, 0, 11])
                rotate([-90, 0, 0])
                    cylinder(d=5.7, h=40, center=true, $fn=24);
        }
        translate([16, 0, 14]) cylinder(d=marble_d + 0.8, h=8, $fn=32);
        translate([-8, -6, 16])
            linear_extrude(1)
                text_line("SW-A", 3.4);
    }
}

module part_sw_pin() {
    cylinder(d=5.6, h=34, $fn=24);
    translate([0, 0, 34]) cylinder(d=9, h=2.4, $fn=24);
}

// ---------- spinner ----------
module part_sn_base() {
    difference() {
        union() {
            cylinder(d=64, h=4, $fn=64);
            translate([0, 0, 4]) cylinder(d1=58, d2=64, h=7, $fn=64);
            translate([-58, -outer_w / 2, 0])
                cube([30, outer_w, floor_top + wall_h]);
            translate([26, -outer_w / 2, 0])
                cube([24, outer_w, floor_top + wall_h]);
        }
        translate([0, 0, 5.2]) cylinder(d1=48, d2=58, h=8, $fn=64);
        // Exit gate
        translate([20, -ch_w / 2, floor_top])
            cube([34, ch_w, wall_h + 4]);
        translate([-60, -ch_w / 2, floor_top])
            cube([36, ch_w, wall_h + 4]);
        translate([-46, 0, 0])
            side_label(0, qty_lines("SN", mark_qty), 3.8);
    }
    translate([0, 0, 4]) cylinder(d=6, h=14, $fn=24);
    translate([-58, 0, 0]) hinge_female_at(0, 0, 0);
    translate([50, 0, 0]) hinge_male_at(0, 0, 0);
}

module part_sn_wheel() {
    difference() {
        union() {
            cylinder(d=34, h=5, $fn=40);
            for (i = [0:4])
                rotate([0, 0, i * 72])
                    translate([4, -1.4, 5])
                        cube([12, 2.8, 8]);
        }
        translate([0, 0, -0.2]) cylinder(d=6.8, h=8, $fn=24);
    }
}

module part_sn_cap() {
    difference() {
        cylinder(d=12, h=3.2, $fn=24);
        translate([0, 0, -0.2]) cylinder(d=5.6, h=2.2, $fn=20);
    }
}

// ---------- loop ----------
module lp_groove_segment(a0, a1, R) {
    hull() {
        translate([R * cos(a0), R * sin(a0), 0]) rz(a0 + 90) profile_solid(floor_top);
        translate([R * cos(a1), R * sin(a1), 0]) rz(a1 + 90) profile_solid(floor_top);
    }
}

module lp_body(with_pegs) {
    R = 40;
    n = 24;
    a0 = 210;
    a1 = 210 + 300; // long way around, ends 60° apart at the bottom
    difference() {
        union() {
            for (i = [0:n - 1]) {
                t0 = a0 + (a1 - a0) * i / n;
                t1 = a0 + (a1 - a0) * (i + 1) / n;
                lp_groove_segment(t0, t1, R);
            }
            // Tenons at the ends, along the tangent
            for (t = [a0, a1]) {
                translate([R * cos(t), R * sin(t), 0]) rz(t + 90)
                    translate([0, -6, 0])
                        cube([12, 12, 9]);
            }
            if (with_pegs)
                for (i = [1:5]) {
                    t = a0 + (a1 - a0) * i / 6;
                    translate([R * cos(t), R * sin(t), floor_top + wall_h])
                        rz(t)
                            translate([0, R > 0 ? -(ch_w / 2 + wall / 2) : 0, 0])
                                cylinder(d=3.6, h=4, $fn=16);
                    translate([R * cos(t), R * sin(t), floor_top + wall_h])
                        rz(t)
                            translate([0, ch_w / 2 + wall / 2, 0])
                                cylinder(d=3.6, h=4, $fn=16);
                }
        }
        for (i = [0:n - 1]) {
            t0 = a0 + (a1 - a0) * i / n;
            t1 = a0 + (a1 - a0) * (i + 1) / n;
            hull() {
                translate([R * cos(t0), R * sin(t0), 0]) rz(t0 + 90) profile_void(floor_top);
                translate([R * cos(t1), R * sin(t1), 0]) rz(t1 + 90) profile_void(floor_top);
            }
        }
        if (!with_pegs)
            for (i = [1:5]) {
                t = a0 + (a1 - a0) * i / 6;
                translate([R * cos(t), R * sin(t), floor_top + wall_h - 0.4])
                    rz(t) {
                        translate([0, -(ch_w / 2 + wall / 2), 0])
                            cylinder(d=4.1, h=6, $fn=16);
                        translate([0, ch_w / 2 + wall / 2, 0])
                            cylinder(d=4.1, h=6, $fn=16);
                    }
            }
    }
}

module lp_adapter(female) {
    difference() {
        union() {
            translate([-2, -16, 0]) cube([20, 32, 12]);
            translate([12, 0, 0]) channel_straight(20, floor_top, floor_top, false);
        }
        translate([-0.2, -6.4, -0.3]) cube([13, 12.8, 9.8]);
        translate([2, -8, 12.2])
            linear_extrude(1)
                text_line(female ? "LP-C" : "LP-D", 3.4);
    }
    if (female)
        hinge_female_at(0, 0, 0);
    else
        translate([32, 0, 0]) hinge_male_at(0, 0, 0);
}

module part_lp_cover() {
    R = 40;
    n = 24;
    a0 = 210;
    a1 = 210 + 300;
    difference() {
        for (i = [0:n - 1]) {
            t0 = a0 + (a1 - a0) * i / n;
            t1 = a0 + (a1 - a0) * (i + 1) / n;
            hull() {
                translate([R * cos(t0), R * sin(t0), 0])
                    rz(t0 + 90)
                        translate([-1, -outer_w / 2 - 1, 0])
                            cube([2, outer_w + 2, 2.4]);
                translate([R * cos(t1), R * sin(t1), 0])
                    rz(t1 + 90)
                        translate([-1, -outer_w / 2 - 1, 0])
                            cube([2, outer_w + 2, 2.4]);
            }
        }
        for (i = [1:5]) {
            t = a0 + (a1 - a0) * i / 6;
            translate([R * cos(t), R * sin(t), -0.2]) rz(t) {
                translate([0, -(ch_w / 2 + wall / 2), 0])
                    cylinder(d=4.2, h=4, $fn=16);
                translate([0, ch_w / 2 + wall / 2, 0])
                    cylinder(d=4.2, h=4, $fn=16);
            }
        }
        translate([R * cos(270), R * sin(270) - 8, 2.5])
            linear_extrude(1)
                text_line("LP-B", 4);
    }
}

// ---------- elevator ----------
module part_el_wheel() {
    // Disk on the bed. A flat in the bore matches the crank shaft.
    difference() {
        cylinder(d=70, h=18, $fn=64);
        translate([0, 0, -0.4]) cylinder(d=8.6, h=20, $fn=28);
        translate([2.4, -2.2, -0.4]) cube([4, 4.4, 20]);
        for (i = [0:5]) {
            rotate([0, 0, i * 60])
                translate([18, -8.6, 4])
                    cube([20, 17.2, 16]);
        }
    }
}

module part_el_base() {
    // Standing print. Inlet on the bed, outlet braced at 45°.
    difference() {
        union() {
            translate([-40, -28, 0]) cube([80, 56, 4]);
            // Towers
            translate([-8, -30, 0]) cube([16, 8, 58]);
            translate([-8, 22, 0]) cube([16, 8, 58]);
            // Shroud on +X
            translate([28, -24, 0]) cube([4, 48, 70]);
            // Inlet chute
            translate([-36, -outer_w / 2, 0])
                cube([20, outer_w, floor_top + wall_h]);
            // Outlet chute high, with a 45° spine
            hull() {
                translate([6, -outer_w / 2, 0]) cube([4, outer_w, 4]);
                translate([6, -outer_w / 2, 70]) cube([30, outer_w, 4]);
            }
            translate([22, -outer_w / 2, 70])
                cube([26, outer_w, floor_top + wall_h]);
        }
        // Loose saddles for the 8 mm axle at z=40
        translate([-20, 0, 46])
            rotate([-90, 0, 0])
                cylinder(d=9.0, h=70, center=true, $fn=28);
        translate([-6, -36, 46]) cube([12, 72, 20]);
        // Inlet void
        translate([-40, -ch_w / 2, floor_top])
            cube([24, ch_w, wall_h + 2]);
        // Outlet void
        translate([20, -ch_w / 2, 70 + floor_top])
            cube([32, ch_w, wall_h + 2]);
        translate([26, -10, 10]) cube([8, 20, 16]);
        translate([26, -10, 56]) cube([8, 20, 16]);
        translate([-20, -26, 20])
            rotate([90, 0, 0])
                linear_extrude(1)
                    text_line("EL", 6);
    }
    translate([-36, 0, 0]) hinge_female_at(0, 0, 0);
    translate([48, 0, 70]) hinge_male_at(0, 0, 0);
}

module part_el_crank() {
    // Shaft prints vertical. A flat along it keys into the wheel.
    difference() {
        union() {
            cylinder(d=7.7, h=72, $fn=28);
            translate([-4, -4, 72]) cube([28, 8, 6]);
            translate([24, 0, 72]) cylinder(d=12, h=14, $fn=24);
        }
        translate([2.3, -2.2, -0.2]) cube([3, 4.4, 74]);
    }
}

// ---------- legend / gauge ----------
module part_legend() {
    difference() {
        union() {
            cube([168, 48, 2.6]);
            translate([148, 10, 0]) cylinder(d=18, h=8, $fn=32);
            translate([148, 34, 0]) cylinder(d=18, h=8, $fn=32);
        }
        translate([148, 10, -0.2]) cylinder(d=16.7, h=10, $fn=40);
        translate([148, 34, -0.2]) cylinder(d=15.5, h=10, $fn=40);
        translate([6, 36, 1.5])
            linear_extrude(1.3)
                text("16 mm  GO", size=4.2, font="Liberation Sans:style=Bold", $fn=12);
        translate([6, 28, 1.5])
            linear_extrude(1.3)
                text("15.5 NO-GO", size=4.2, font="Liberation Sans:style=Bold", $fn=12);
        translate([6, 16, 1.5])
            linear_extrude(1.2)
                text("T3 x6   T2 x4   T1 x4   ST x8", size=3.4, font="Liberation Sans:style=Bold", $fn=12);
        translate([6, 8, 1.5])
            linear_extrude(1.2)
                text("CL x2  CR x2  CU x1  others x1", size=3.4, font="Liberation Sans:style=Bold", $fn=12);
        translate([6, 42, 1.5])
            linear_extrude(1.2)
                text("MARBLE KIT", size=4.4, font="Liberation Sans:style=Bold", $fn=12);
    }
}

module extra_part() {
    if (part == "ZZ") part_zz();
    else if (part == "YS") part_ys();
    else if (part == "MG") part_mg();
    else if (part == "FN") part_fn();
    else if (part == "LD") part_ld();
    else if (part == "BX") part_bx();
    else if (part == "JP") part_jp();
    else if (part == "WF") part_wf();
    else if (part == "WF-C") part_wf_cover();
    else if (part == "SP") part_sp();
    else if (part == "ST-P") part_st_post();
    else if (part == "ST-Y") part_st_yoke();
    else if (part == "SW-B") part_sw_base();
    else if (part == "SW-A") part_sw_beam();
    else if (part == "SW-P") part_sw_pin();
    else if (part == "SN-B") part_sn_base();
    else if (part == "SN-W") part_sn_wheel();
    else if (part == "SN-C") part_sn_cap();
    else if (part == "LP-A") lp_body(true);
    else if (part == "LP-B") part_lp_cover();
    else if (part == "LP-C") lp_adapter(true);
    else if (part == "LP-D") lp_adapter(false);
    else if (part == "EL-W") part_el_wheel();
    else if (part == "EL-B") part_el_base();
    else if (part == "EL-C") part_el_crank();
    else if (part == "LG") part_legend();
    else echo("UNKNOWN", part);
}
