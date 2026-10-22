# Task 3 progress — Months 1–3 math entries and the link checker

Branch `opencode/math-m1-3-links`.

## Math quick reference, Months 1–3 (`src/lib/mathRef.ts`)
Seven new entries sit at the start of the list: `hex`, `twos-complement`, `bitwise`, `trig-components`, `radians`,
`rate-accumulation` and `stddev-rms`. opencode (deepseek-v4.1-flash-free) drafted them, and I reviewed each one
against the lesson it cites. Every number is recomputed by `docs/notes/math-m1-3-verify.py`.

Hand corrections:
- `stddev-rms`: the draft used four resistor readings (996, 221, 10120, 46 Ω) that are not in `log.py`; the script
  logs only R1 = 4688 Ω. The example was rewritten on the real `filter_sim.py` numbers (bias 1.5 °/s, σ 0.3 °/s,
  offset_flat 0.72°, noise_flat 0.07°), and lessons were reduced to `sensors-fusion`.
- `trig-components`: "the two differ by about 0.006 N·m and the joint settles there" was not an equilibrium.
  It now solves 0.2 × (60 − θ) = 0.4 cos θ → 58.97° (printed as 59.0°).
- `rate-accumulation`: the I-term numbers are stated as "if the error stays at 60° for 0.1 s", and the 40 ms window is tied to the 25 Hz outer loop.

`radians` and `trig-components` overlap the existing `radians-trig` entry on purpose. They are the Months 1–3 primers
with Months 1–3 examples, and `radians-trig` keeps its Month 5 example.

## Link checker
`tools/check_links.py` is new and was reviewed line by line. My notes do not record whether opencode drafted it, so count it as hand-written. It is documented in the README and its run is recorded in `links-check.md`.

## Review fixes
- `trig-components`: the cos θ comes from the horizontal lever arm l cos θ, or equivalently from the component of gravity perpendicular to the arm. The wrong "vertical component" wording is removed in both zh and en.
- `rate-accumulation`: the windup numbers now come from `pid_sim.run(0.05, ki=0.4, kd=0.002, anti_windup=False)` stopped at t = 0.1 s:
  - integral 4.97 °·s and I term 1.99 N·m, with the motor saturated the whole time;
  - with anti-windup the integral is 0.52 °·s;
  - overshoot is 39.0° without anti-windup and 8.9° with it.

  `docs/notes/math-m1-3-verify.py` recomputes these numbers.
- `radians` and `trig-components` cross-link with `radians-trig` in both directions. They were not merged into one entry, because #19 edits the `radians-trig` example.
