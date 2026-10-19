// servo_bracket.scad: a parametric L-bracket for an SG90-class micro servo.
// Every size is a named parameter. Measure YOUR servo with calipers and change
// the numbers at the top; never trust one datasheet drawing.
//   Render:  openscad -o servo_bracket.stl servo_bracket.scad
//   Change one value from the command line:  openscad -D clearance=0.4 -o b.stl servo_bracket.scad

// --- the servo (common SG90 drawing: body 22.2 x 11.8 mm, 32.2 mm across the tabs) ---
servo_l      = 22.2;   // body length, mm
servo_w      = 11.8;   // body width, mm
tab_span     = 32.2;   // length across both mounting tabs, mm
hole_pitch   = 27.5;   // tab screw spacing: not on that drawing; sources say 27-28, measure it
hole_d       = 2.0;    // tab hole for an M2 / self-tapping screw, mm

// --- the printer and the bracket ---
clearance    = 0.3;    // gap on each side of the body (from your tolerance gauge, Lesson 2)
wall         = 3.0;    // plate thickness, mm
margin       = 4.0;    // material left around the cut-out, mm
base_depth   = 26.0;   // how far the foot sticks out, mm (servo body hangs ~16 mm behind the plate)
mount_d      = 3.4;    // foot holes for M3 screws (3 mm + clearance), mm

// --- derived sizes: computed, never typed in twice ---
cut_l   = servo_l + 2 * clearance;
cut_w   = servo_w + 2 * clearance;
plate_l = tab_span + 2 * margin;
plate_h = cut_w + 2 * margin;

echo("cut-out (mm)", cut_l, "x", cut_w);
echo("plate (mm)", plate_l, "x", plate_h, "x", wall);
echo("screw pitch (mm)", hole_pitch, "tab overhang each side (mm)", (tab_span - servo_l) / 2);
assert(hole_pitch > cut_l + hole_d, "screw holes would cut into the body opening");
assert(hole_pitch < tab_span - hole_d, "screw holes would fall off the tabs");

$fn = 32;

module plate() {                       // upright plate that the servo tabs screw onto
  difference() {
    cube([plate_l, wall, plate_h]);
    translate([(plate_l - cut_l) / 2, -1, margin])
      cube([cut_l, wall + 2, cut_w]);
    for (s = [-1, 1])
      translate([plate_l / 2 + s * hole_pitch / 2, -1, plate_h / 2])
        rotate([-90, 0, 0]) cylinder(d = hole_d, h = wall + 2);
  }
}

module foot() {                        // horizontal foot that bolts to the robot
  difference() {
    cube([plate_l, base_depth, wall]);
    for (s = [-1, 1])
      translate([plate_l / 2 + s * 10, base_depth - 5, -1])   // in front of the servo body
        cylinder(d = mount_d, h = wall + 2);
  }
}

module gusset() {                      // triangular rib: stops the plate flexing
  rotate([90, 0, 90]) linear_extrude(wall)
    polygon([[wall, wall], [base_depth, wall], [wall, plate_h * 0.6]]);
}

plate();
foot();
gusset();
translate([plate_l - wall, 0, 0]) gusset();
