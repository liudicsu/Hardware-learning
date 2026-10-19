// esp32_case.scad: a two-part snap-fit case for an ESP32-S3-DevKitC-1 (headers pins down).
// Board size from Espressif's v1.1 drawing (62.74 x 25.40 mm); measure your own board,
// clones differ. The snap arms use the numbers checked by snap_fit.py (L 10, t 1.2, hook 0.8).
//   Render both parts:  openscad -o esp32_case.stl esp32_case.scad
//   Only one part:      openscad -D 'part="base"' -o base.stl esp32_case.scad
//   Interference check: openscad -D 'part="clash"' -o clash.stl esp32_case.scad
//                       (closes the lid on the base; "top level object is empty" = no clash)

part      = "both";   // "base", "lid", "both" (side by side for printing) or "clash"

// --- the board ---
board_l   = 62.74;
board_w   = 25.40;
pins_h    = 9.0;      // header pins below the board, plus a little air
above_h   = 6.0;      // tallest part on top (buttons, module shield) plus air
usb_w     = 12.0;     // opening at one end for the USB cable(s)
usb_h     = 7.0;

// --- the printer ---
clearance = 0.3;      // board-to-wall gap on each side: use your tolerance-gauge result
fit       = 0.2;      // gap between the snap arm and the base wall

// --- the case ---
wall      = 2.0;
floor_t   = 2.0;
lid_t     = 2.0;
ledge     = 2.5;      // the board rests on two ledges at the short ends (pins are on the long edges)
arm_L     = 10.0;     // snap arm length  } keep these in step with snap_fit.py
arm_t     = 1.2;      // snap arm thickness }
hook      = 0.8;      // hook depth        }
arm_b     = 6.0;      // snap arm width

in_l  = board_l + 2 * clearance;
in_w  = board_w + 2 * clearance;
in_h  = pins_h + 1.6 + above_h;           // 1.6 mm board
out_l = in_l + 2 * wall;
out_w = in_w + 2 * wall;
out_h = floor_t + in_h;
win_z = out_h - arm_L - 0.2;              // window in the base wall that the hook clicks into

echo("inside (mm)", in_l, "x", in_w, "x", in_h);
echo("outside, closed (mm)", out_l, "x", out_w, "x", out_h + lid_t);
assert(hook < wall, "the hook must be shallower than the wall it clicks into");

module base() {
  difference() {
    cube([out_l, out_w, out_h]);
    translate([wall, wall, floor_t]) cube([in_l, in_w, in_h + 1]);
    translate([-1, (out_w - usb_w) / 2, floor_t + pins_h]) cube([wall + 2, usb_w, usb_h]);
    for (y = [-1, out_w - wall - 1])                       // windows for the two hooks
      translate([(out_l - arm_b - 1) / 2, y, win_z]) cube([arm_b + 1, wall + 2, 2.2]);
  }
  for (x = [wall, out_l - wall - ledge])                   // ledges at the short ends
    translate([x, wall, floor_t]) cube([ledge, in_w, pins_h]);
}

module lid() {
  cube([out_l, out_w, lid_t]);
  translate([wall + fit, wall + fit, lid_t]) difference() {   // locating lip
    cube([in_l - 2 * fit, in_w - 2 * fit, 1.5]);
    translate([1.2, 1.2, -1]) cube([in_l - 2 * fit - 2.4, in_w - 2 * fit - 2.4, 4]);
  }
}

// The lid prints flat with the arms standing up, so they bend ACROSS the layers (the weak
// direction). If an arm snaps, print the lid on its side or switch to PETG (see the lesson).
module lid_with_arms() {                                  // modelled upside down, as it prints
  lid();
  x0 = (out_l - arm_b) / 2;
  translate([x0, wall + fit, lid_t]) mirror([0, 1, 0]) translate([0, -arm_t, 0]) snap_arm_up();
  translate([x0, out_w - wall - fit - arm_t, lid_t]) snap_arm_up();
}

module snap_arm_up() {                                    // arm along +z, hook on the +y face at the tip
  cube([arm_b, arm_t, arm_L]);
  // hook: 0.4 mm catch face, then a 30 degree lead-in (0.8 / tan 30 = 1.4 mm) down to the tip
  translate([0, arm_t, arm_L - 1.8])
    rotate([90, 0, 90]) linear_extrude(arm_b) polygon([[0, 0], [hook, 0.4], [0, 1.8]]);
}

if (part == "base" || part == "both") base();
if (part == "lid") lid_with_arms();
if (part == "both") translate([0, out_w + 8, 0]) lid_with_arms();
if (part == "clash") intersection() {                     // what the closed lid and base share
  base();
  translate([0, out_w, out_h + lid_t]) rotate([180, 0, 0]) lid_with_arms();
}
