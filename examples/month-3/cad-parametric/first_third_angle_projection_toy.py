#!/usr/bin/env python3
"""First-angle vs third-angle orthographic projection on one shared stepped block.

Synthetic, stdlib only.  Not a redo of the GD&T tolerance-stack toy, and not the
interference (press / shrink) fit toy.  MMC stays literacy-only and is not modelled.
Real Onshape / SolidWorks / a printed title block: 本页未运行.
Wikipedia "Multiview orthographic projection" statements, including the truncated-cone
symbol and the first- vs third-angle arrangement, are 以原文为准.  Named standards
(ISO 5456-2, ASME Y14.3, BS 8888, JIS B 0001, AS 1100) appear only as Wikipedia names,
not as opened standard formulas.

The six orthographic face drawings of one asymmetric object are shared.  First- and
third-angle projection arrange those same views differently.  The international
truncated-cone symbol tells the reader which convention a sheet uses:
  solid truncated cone, small end toward the viewer;
  front view: two concentric circles with a solid inner circle (front, not rear);
  side view: an isosceles trapezoid;
  first-angle: shortest trapezoid side away from the circles;
  third-angle: shortest trapezoid side towards the circles.

Placement (front at the centre; rear at the far right), 以原文为准:
  first-angle (unfolded from the interior): left of front = right view, right of
    front = left view, above = bottom view, below = top view.
  third-angle (unfolded from the exterior): left of front = left view, right of
    front = right view, above = top view, below = bottom view.

Arms (same object, same face drawings):
  A_first     place under first-angle rules, read as first-angle, first-angle symbol.
  B_third     place under third-angle rules, read as third-angle, third-angle symbol.
  C_cross     third-angle sheet read as first-angle (documented confusion mode).
  D_ignore    correctly marked first-angle sheet, symbol ignored, left/right swapped.

Common random numbers: for each seed the object (boss side and notch face) is drawn
once and reused by every arm.  Five seeds.  The layout rules themselves are
deterministic.

Metrics per seed: slot_match (1 if every slot holds the view the reader's convention
assigns to that slot on a correctly marked sheet of that convention, else 0);
boss_ok (1 if the reconstructed boss side matches the object, else 0);
notch_ok (1 if the reconstructed notch face matches the object, else 0).

Regimes and expectations, written before the first run:
  same_convention   A and B exact on slot_match, boss_ok and notch_ok (keep)
  cross_convention  C loses: left/right or top/bottom swap (keep)
  symbol_ignored    D loses on a correctly marked first-angle sheet (keep)

A hand_calc names the convention from a cone-symbol description before the table.
No integration step: each sheet is a static layout; there is no time stepping.
"""
from __future__ import annotations

import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

# Declared object envelope (mm), printed.  The boss and notch break L/R and T/B symmetry.
WIDTH = 40.0
DEPTH = 20.0
HEIGHT = 10.0
BOSS_H = 4.0
NOTCH_W = 6.0

SLOTS = ("left", "above", "centre", "below", "right", "far_right")
VIEWS = ("front", "top", "bottom", "left", "right", "rear")

# slot -> view under each convention (front at centre, rear at far right)
FIRST_ANGLE = {
    "left": "right",
    "above": "bottom",
    "centre": "front",
    "below": "top",
    "right": "left",
    "far_right": "rear",
}
THIRD_ANGLE = {
    "left": "left",
    "above": "top",
    "centre": "front",
    "below": "bottom",
    "right": "right",
    "far_right": "rear",
}

ARMS = ("A_first", "B_third", "C_cross", "D_ignore")
METRICS = ("slot_match", "boss_ok", "notch_ok")

# name: (kind, declared expectation); written before the first run
REGIMES = {
    "same_convention": (
        "same_convention",
        "A and B exact on slot identity and feature side - keep",
    ),
    "cross_convention": (
        "cross_convention",
        "C loses: third-angle sheet read as first-angle swaps left/right or top/bottom - keep",
    ),
    "symbol_ignored": (
        "symbol_ignored",
        "D loses: correctly marked first-angle sheet, symbol ignored, left/right swapped - keep",
    ),
}

# Named alternative, same objects, not adopted: invert the cone symbol (treat
# "away" as "towards") on an otherwise correctly placed first-angle sheet.
ALT_INVERT_SYMBOL = True


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-4:
        return format(Decimal(repr(x)), ".3e")
    s = format(Decimal(repr(x)), ".4f")
    return "0.0000" if s == "-0.0000" else s


def sign_note(diffs, m):
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def fmt_pair(m, s):
    return f"{num(m)}+-{num(s)}"


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < SMALL_FRAC * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def shared_object(seed: int) -> dict:
    """Draw one asymmetric stepped block; reused by every arm at this seed."""
    rng = random.Random(seed)
    boss_side = rng.choice(("left", "right"))
    notch_face = rng.choice(("top", "bottom"))
    notch_y = rng.choice(("front", "rear"))
    return {
        "boss_side": boss_side,
        "notch_face": notch_face,
        "notch_y": notch_y,
        "width": WIDTH,
        "depth": DEPTH,
        "height": HEIGHT,
        "boss_h": BOSS_H,
        "notch_w": NOTCH_W,
    }


def face_drawings(obj: dict) -> dict:
    """Shared orthographic face drawings of the object (convention-independent)."""
    flip = {"left": "right", "right": "left", "top": "bottom", "bottom": "top",
            "front": "rear", "rear": "front"}
    return {view: {
        "view": view,
        "boss_side": obj["boss_side"] if view in ("front", "top", "bottom")
        else (flip[obj["boss_side"]] if view == "rear" else "this_face" if view == obj["boss_side"] else "other_face"),
        "notch_face": obj["notch_face"] if view == "front"
        else (flip[obj["notch_face"]] if view == "rear" else "this_face" if view == obj["notch_face"] else "other_face"),
        "notch_y": obj["notch_y"],
    } for view in VIEWS}


def place(drawings: dict, convention: str) -> dict:
    layout = FIRST_ANGLE if convention == "first" else THIRD_ANGLE
    return {slot: drawings[view] for slot, view in layout.items()}


def read_sheet(sheet: dict, reader: str, swap_lr: bool = False) -> dict:
    """Interpret occupied slots with a reader's convention (optionally swap L/R)."""
    layout = FIRST_ANGLE if reader == "first" else THIRD_ANGLE
    assigned = {}
    for slot, drawing in sheet.items():
        if swap_lr and slot in ("left", "right"):
            slot = "right" if slot == "left" else "left"
        assigned[layout[slot]] = drawing
    return assigned


def reconstruct(assigned: dict) -> dict:
    """Rebuild boss side and notch face from the side and plan views the reader named.

    The front view sits in the same centre slot under both conventions, so it does
    not itself swap.  A cross-convention reader mis-names the left/right and
    top/bottom views around that front, and can machine a feature on the wrong side.
    """
    if assigned["right"]["boss_side"] == "this_face":
        boss = "right"
    elif assigned["left"]["boss_side"] == "this_face":
        boss = "left"
    else:
        raise RuntimeError("boss face not found in the named left/right views")
    if assigned["top"]["notch_face"] == "this_face":
        notch = "top"
    elif assigned["bottom"]["notch_face"] == "this_face":
        notch = "bottom"
    else:
        raise RuntimeError("notch face not found in the named top/bottom views")
    return {
        "boss_side": boss,
        "notch_face": notch,
        "notch_y": assigned["front"]["notch_y"],
        "views": {view: assigned[view]["view"] for view in VIEWS},
    }


def slot_match(assigned: dict) -> float:
    return 1.0 if all(assigned[view]["view"] == view for view in VIEWS) else 0.0


def run_arm(obj: dict, arm: str) -> dict:
    drawings = face_drawings(obj)
    if arm == "A_first":
        sheet, reader, swap = place(drawings, "first"), "first", False
    elif arm == "B_third":
        sheet, reader, swap = place(drawings, "third"), "third", False
    elif arm == "C_cross":
        sheet, reader, swap = place(drawings, "third"), "first", False
    elif arm == "D_ignore":
        sheet, reader, swap = place(drawings, "first"), "first", True
    else:
        raise KeyError(arm)
    assigned = read_sheet(sheet, reader, swap_lr=swap)
    rec = reconstruct(assigned)
    return {
        "slot_match": slot_match(assigned),
        "boss_ok": 1.0 if rec["boss_side"] == obj["boss_side"] else 0.0,
        "notch_ok": 1.0 if rec["notch_face"] == obj["notch_face"] else 0.0,
        "rec_boss": rec["boss_side"],
        "rec_notch": rec["notch_face"],
        "true_boss": obj["boss_side"],
        "true_notch": obj["notch_face"],
        "views": rec["views"],
    }


def run_alt_invert_symbol(obj: dict) -> dict:
    """Named alternative: invert the symbol, then read a first-angle sheet as third."""
    drawings = face_drawings(obj)
    sheet = place(drawings, "first")
    assigned = read_sheet(sheet, "third", swap_lr=False)
    rec = reconstruct(assigned)
    return {
        "slot_match": slot_match(assigned),
        "boss_ok": 1.0 if rec["boss_side"] == obj["boss_side"] else 0.0,
        "notch_ok": 1.0 if rec["notch_face"] == obj["notch_face"] else 0.0,
    }


def col(rows, metric):
    return [row[metric] for row in rows]


def symbol_hand_calc():
    # Shortest trapezoid side away from the circles => first-angle; towards => third-angle.
    first = "first-angle"
    third = "third-angle"
    return first, third


def main():
    print("Synthetic first- vs third-angle projection stand-in; not a real CAD sheet")
    print(
        f"declared WIDTH={num(WIDTH)} mm DEPTH={num(DEPTH)} mm HEIGHT={num(HEIGHT)} mm "
        f"BOSS_H={num(BOSS_H)} mm NOTCH_W={num(NOTCH_W)} mm SMALL_FRAC={num(SMALL_FRAC)} "
        f"seeds={','.join(str(s) for s in SEEDS)}"
    )
    print("hand_calc 20 percent small-vs-clear factor = " + num(SMALL_FRAC))
    first_name, third_name = symbol_hand_calc()
    print(
        "hand_calc symbol: two concentric circles (solid inner) + isosceles trapezoid, "
        f"shortest side away from the circles => {first_name}"
    )
    print(
        "hand_calc symbol: two concentric circles (solid inner) + isosceles trapezoid, "
        f"shortest side towards the circles => {third_name}"
    )
    print("declared arms: A_first place+read first-angle; B_third place+read third-angle; "
          "C_cross third-angle sheet read as first-angle; D_ignore first-angle sheet, symbol ignored, L/R swapped")
    print("Regimes and parameters were written before the first run")
    print("Common random numbers: the object (boss side, notch face) is shared across arms at each seed")
    print("Assumptions: same six face drawings; only the arrangement and the reader convention change")
    print("Wikipedia figures and territorial lists 以原文为准")
    print("Real Onshape / SolidWorks / printed title block: 本页未运行")
    for name, (_kind, expl) in REGIMES.items():
        print(f"declared {name}: {expl}")

    objects = {seed: shared_object(seed) for seed in SEEDS}
    rows = {arm: [] for arm in ARMS}
    print("shared layouts (deterministic placement rules; seeds only change the object)")
    for seed in SEEDS:
        obj = objects[seed]
        print(
            f"  seed {seed} object: boss={obj['boss_side']} notch={obj['notch_face']} "
            f"notch_y={obj['notch_y']}"
        )
        for arm in ARMS:
            rec = run_arm(obj, arm)
            rows[arm].append(rec)
            print(
                f"    {arm}: slot_match={num(rec['slot_match'])} "
                f"boss_ok={num(rec['boss_ok'])} notch_ok={num(rec['notch_ok'])} "
                f"rec_boss={rec['rec_boss']} rec_notch={rec['rec_notch']}"
            )
    for arm in ARMS:
        for metric in METRICS:
            xs = col(rows[arm], metric)
            m, s = mean_sd(xs)
            print(f"  {arm} {metric} {fmt_pair(m, s)}")
    for metric in METRICS:
        print(f"  paired B-A {metric}: {verdict(col(rows['B_third'], metric), col(rows['A_first'], metric))}")
        print(f"  paired C-A {metric}: {verdict(col(rows['C_cross'], metric), col(rows['A_first'], metric))}")
        print(f"  paired C-B {metric}: {verdict(col(rows['C_cross'], metric), col(rows['B_third'], metric))}")
        print(f"  paired D-A {metric}: {verdict(col(rows['D_ignore'], metric), col(rows['A_first'], metric))}")
    print("declared expectation same_convention: A and B exact on slot identity and feature side - keep")
    print("declared expectation cross_convention: C loses: third-angle sheet read as first-angle swaps left/right or top/bottom - keep")
    print("declared expectation symbol_ignored: D loses: correctly marked first-angle sheet, symbol ignored, left/right swapped - keep")

    print("named alternative invert_symbol (first-angle sheet read as third-angle) - not adopted")
    alt_rows = []
    a_rows = []
    for seed in SEEDS:
        obj = objects[seed]
        alt_rows.append(run_alt_invert_symbol(obj))
        a_rows.append(run_arm(obj, "A_first"))
    for metric in METRICS:
        print(f"  alt invert {metric} {fmt_pair(*mean_sd(col(alt_rows, metric)))}")
        print(f"  paired alt-A {metric}: {verdict(col(alt_rows, metric), col(a_rows, metric))}")
    print("no integration step: static view layouts, no plant, no time step")
    print("No winner declared")


if __name__ == "__main__":
    main()
