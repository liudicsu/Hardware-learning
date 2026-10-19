// finray_finger.scad: a parametric fin-ray style finger to print in TPU.
// Two thin flanks meet at the tip; thin ribs join them. Press the front flank and the
// ribs make the finger curl AROUND the object instead of pushing it away.
//   Render:  openscad -o finray_finger.stl finray_finger.scad
// The mounting base is generic: measure the jaw you bolt it to and change mount_*.

length     = 60;     // base to tip, mm
base_w     = 22;     // finger depth at the base (front flank to back flank), mm
height     = 18;     // extrusion = finger width across the object, mm
flank      = 1.2;    // flank thickness: thinner = softer
ribs       = 6;      // number of internal ribs
rib_t      = 0.9;    // rib thickness
rib_tilt   = 10;     // deg: ribs leaning toward the base make the tip wrap more

base_t     = 5;      // solid mounting block, mm
mount_d    = 3.2;    // M3 holes
mount_pitch= 10;     // distance between the two holes: MEASURE YOUR JAW

echo("finger (mm)", length + base_t, "x", base_w, "x", height);
assert(flank >= 0.8, "flanks thinner than two 0.4 mm lines will not print cleanly");
assert(mount_pitch + mount_d < height, "mount holes do not fit across the finger width");

// front flank runs from (0,0) to the tip (length, 0); back flank from (0, base_w) to the tip
function back_y(x) = base_w * (1 - x / length);

module outline() {
  polygon([[0, 0], [length, 0], [0, base_w]]);
}

module hollow() {                        // the triangle minus its insides = two flanks
  difference() {
    outline();
    offset(delta = -flank) outline();
  }
}

module rib(i) {                          // a rib from the front flank to the back flank
  x = length * i / (ribs + 1);
  dx = back_y(x) * tan(rib_tilt);        // lean toward the base
  hull() {
    translate([x, 0]) square([rib_t, 0.01]);
    translate([max(0, x - dx), back_y(max(0, x - dx)) - 0.01]) square([rib_t, 0.01]);
  }
}

linear_extrude(height) {
  hollow();
  intersection() {
    outline();
    union() for (i = [1 : ribs]) rib(i);
  }
}
difference() {                           // mounting block behind the base of the finger
  translate([-base_t, 0, 0]) cube([base_t, base_w, height]);
  for (s = [-1, 1])
    translate([-base_t - 1, base_w / 2, height / 2 + s * mount_pitch / 2])
      rotate([0, 90, 0]) cylinder(d = mount_d, h = base_t + 2, $fn = 24);
}
