#!/usr/bin/env python3
"""ESP32 Light-sleep vs Deep-sleep energy over a shared event timeline.

Synthetic charge bookkeeping, stdlib only.  Not esp_light_sleep_start() or
esp_deep_sleep_start() on a board, not a power-analyser capture, not the
FreeRTOS scheduler toy and not the ADC section.  Real ESP32: 本页未运行.
ESP-IDF Sleep Modes statements 以文档为准.

What the ESP-IDF Sleep Modes page says (and what this toy keeps):
  Light-sleep: digital peripherals, most RAM and the CPUs are clock-gated and
    their supply is reduced; on exit their internal state is preserved.
  Deep-sleep: CPUs, most RAM and APB-clocked digital peripherals are powered
    off; RTC controller, ULP, RTC FAST and RTC SLOW memory can stay on.  On a
    Deep-sleep wake the chip runs the wake stub and then loads the app.
  Wakeup sources can be combined.  ext0 / ext1 use RTC IOs only; GPIO wakeup
    from Light-sleep works on any IO; Deep-sleep GPIO wakeup is limited to
    RTC-domain pins.  Wi-Fi / Bluetooth connections are not maintained in
    either sleep mode.
The page body we read gives no sleep-current or wake-latency table, so every
current and wake cost below is a declared toy parameter, printed, and NOT a
datasheet value.

Common random numbers: one event timeline per (regime, seed), shared by every
arm.  Arms:
  A_active : never sleeps (I_ACTIVE the whole window)
  B_light  : Light-sleep whenever idle; T_WAKE_LIGHT wake cost; RAM kept;
             wake sources timer + any GPIO
  C_deep   : Deep-sleep whenever idle; T_BOOT_DEEP wake (stub + app load) at
             I_BOOT; RAM lost on every wake, RTC SLOW counter kept;
             wake sources timer + RTC-IO GPIO only
The arms differ only in the sleep mode (and its wake sources and costs).
An event that arrives while the chip is awake is queued and served; an event
on a source that is not enabled while the chip sleeps is missed.  Sleep is
entered immediately when idle (no entry overhead).  Wi-Fi is down in both
sleep arms: each wake counts one link drop, but reconnect energy is NOT
modelled.  No integration step: event-driven bookkeeping of I x t, no ODE.

Regimes and parameters were written before the first run:
  long_idle          : RTC timer wake every ~60 s, nothing else
                       - C consistent lowest energy vs A (and vs B); keep
  high_wake_rate     : RTC-IO GPIO events, mean gap 0.25 s (chosen below the
                       hand-calculated C-vs-A break-even before the run)
                       - C may near-tie or LOSE to A, and loses to B; keep
  missed_wake_source : timer every ~60 s plus events on a digital-only GPIO
                       - C consistent miss (not an enabled Deep-sleep wake
                       source); B catches them; keep
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared model parameters, written before the first run.  Toy values, not
# datasheet mA / uA, not measured here.
I_ACTIVE = 40.0       # mA, CPU awake (toy)
I_LIGHT = 0.8         # mA, Light-sleep floor (toy)
I_DEEP = 0.01         # mA, Deep-sleep floor (toy)
I_BOOT = 50.0         # mA, Deep-sleep wake: stub + app load + re-init (toy)
T_WAKE_LIGHT = 0.001  # s, Light-sleep wake cost at I_ACTIVE (toy)
T_BOOT_DEEP = 0.300   # s, Deep-sleep wake cost at I_BOOT (toy)
WORK = 0.050          # s, work per served event at I_ACTIVE
V_SUPPLY = 3.3        # V, only to convert charge to energy

ARMS = ("A_active", "B_light", "C_deep")
WAKE_SOURCES = {
    "A_active": ("timer", "rtc_gpio", "digital_gpio"),
    "B_light": ("timer", "rtc_gpio", "digital_gpio"),
    "C_deep": ("timer", "rtc_gpio"),
}
REGIMES = {
    "long_idle": {"window": 3600.0, "timer": 60.0, "gpio_gap": None, "gpio_src": None},
    "high_wake_rate": {"window": 600.0, "timer": 60.0, "gpio_gap": 0.25, "gpio_src": "rtc_gpio"},
    "missed_wake_source": {"window": 3600.0, "timer": 60.0, "gpio_gap": 30.0, "gpio_src": "digital_gpio"},
}
TIMER_JITTER = 0.5    # s, +/- uniform on each timer period


def shared_timeline(regime, seed):
    """Common random numbers: one event list used by every arm."""
    rng = random.Random(f"{regime}/{seed}")
    cfg = REGIMES[regime]
    ev = []
    t = 0.0
    while True:
        t += cfg["timer"] + rng.uniform(-TIMER_JITTER, TIMER_JITTER)
        if t >= cfg["window"]:
            break
        ev.append((t, "timer"))
    if cfg["gpio_gap"]:
        t = 0.0
        while True:
            t += rng.expovariate(1.0 / cfg["gpio_gap"])
            if t >= cfg["window"]:
                break
            ev.append((t, cfg["gpio_src"]))
    ev.sort()
    return ev


def simulate(arm, events, window, i_boot=I_BOOT, t_boot=T_BOOT_DEEP):
    charge = 0.0          # mA*s
    busy_until = 0.0      # chip awake until this time; idle afterwards
    served = missed = wakes = 0
    lat = []
    ram = rtc = 0         # RAM counter (lost in Deep-sleep) and RTC SLOW counter
    ram_ok = True
    if arm == "A_active":
        for t, _src in events:
            start = max(t, busy_until)
            lat.append(start - t)
            busy_until = start + WORK
            served += 1
            ram += 1
            rtc += 1
        charge = I_ACTIVE * max(window, busy_until)
        return {"charge": charge, "served": served, "missed": 0, "wakes": 0,
                "lat": sum(lat) / len(lat), "ram": ram, "rtc": rtc, "ram_ok": ram == served}
    i_sleep = I_LIGHT if arm == "B_light" else I_DEEP
    for t, src in events:
        if t > busy_until:  # strictly after the last work ended: the chip is asleep
            charge += i_sleep * (t - busy_until)
            if src not in WAKE_SOURCES[arm]:
                missed += 1
                busy_until = t  # still asleep; sleep charge already counted up to t
                continue
            wakes += 1
            if arm == "B_light":
                charge += I_ACTIVE * T_WAKE_LIGHT
                start = t + T_WAKE_LIGHT
            else:
                charge += i_boot * t_boot
                start = t + t_boot
                ram = 0  # RAM powered off in Deep-sleep
        else:              # awake (working or booting): queue, any source is seen
            start = busy_until
        lat.append(start - t)
        charge += I_ACTIVE * WORK
        busy_until = start + WORK
        served += 1
        ram += 1
        rtc += 1
    if busy_until < window:
        charge += i_sleep * (window - busy_until)
    ram_ok = (ram == served) if arm == "B_light" else (ram <= served)
    return {"charge": charge, "served": served, "missed": missed, "wakes": wakes,
            "lat": (sum(lat) / len(lat)) if lat else 0.0, "ram": ram, "rtc": rtc, "ram_ok": ram_ok}


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-4:
        return f"{x:.3e}"
    return f"{x:.4f}"


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
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def per_cycle_charge(arm, gap, i_boot=I_BOOT, t_boot=T_BOOT_DEEP):
    """Hand calculation: charge (mA*s) for one wake cycle of period gap."""
    if arm == "A_active":
        return I_ACTIVE * gap
    if arm == "B_light":
        return I_ACTIVE * (T_WAKE_LIGHT + WORK) + I_LIGHT * (gap - T_WAKE_LIGHT - WORK)
    return i_boot * t_boot + I_ACTIVE * WORK + I_DEEP * (gap - t_boot - WORK)


def breakeven(i_boot=I_BOOT, t_boot=T_BOOT_DEEP):
    # C < A  iff  gap > g_ca ;  C < B  iff  gap > g_cb  (strict; equality is a tie)
    g_ca = (i_boot * t_boot + I_ACTIVE * WORK - I_DEEP * (t_boot + WORK)) / (I_ACTIVE - I_DEEP)
    g_cb = ((i_boot * t_boot + I_ACTIVE * WORK - I_DEEP * (t_boot + WORK))
            - (I_ACTIVE * (T_WAKE_LIGHT + WORK) - I_LIGHT * (T_WAKE_LIGHT + WORK))) / (I_LIGHT - I_DEEP)
    return g_ca, g_cb


def run_regime(regime, i_boot=I_BOOT, t_boot=T_BOOT_DEEP):
    window = REGIMES[regime]["window"]
    res = {arm: [] for arm in ARMS}
    for seed in SEEDS:
        ev = shared_timeline(regime, seed)
        for arm in ARMS:
            r = simulate(arm, ev, window, i_boot, t_boot)
            r["avg_mA"] = r["charge"] / window
            r["n_events"] = len(ev)
            res[arm].append(r)
    return res


def col(res, arm, key):
    return [r[key] for r in res[arm]]


def main():
    print("Synthetic ESP32 Light-sleep vs Deep-sleep toy; shared event timeline; not a board measurement")
    print(f"seeds={len(SEEDS)} I_ACTIVE={I_ACTIVE:.1f} mA I_LIGHT={I_LIGHT:.2f} mA I_DEEP={I_DEEP:.2f} mA "
          f"I_BOOT={I_BOOT:.1f} mA (declared toy currents, not datasheet values)")
    print(f"T_WAKE_LIGHT={T_WAKE_LIGHT:.3f} s T_BOOT_DEEP={T_BOOT_DEEP:.3f} s WORK={WORK:.3f} s "
          f"V_SUPPLY={V_SUPPLY:.1f} V (declared toy wake costs, not a documented latency)")
    print("No integration step: event-driven I x t bookkeeping, no time-step criterion")
    print("Regimes and parameters were written before the first run")
    print("wake_sources: A all; B timer+rtc_gpio+digital_gpio (Light-sleep GPIO wakeup on any IO); "
          "C timer+rtc_gpio (Deep-sleep GPIO wakeup on RTC IOs only)")
    print("state_rule: Light-sleep keeps RAM; Deep-sleep loses RAM on every wake, RTC SLOW counter kept; "
          "Wi-Fi down in both sleep arms (one link drop per wake, reconnect energy not modelled)")
    g_ca, g_cb = breakeven()
    print(f"hand_calc per-cycle charge at gap g (mA*s): A={I_ACTIVE:.1f}*g; B={I_ACTIVE*(T_WAKE_LIGHT+WORK)-I_LIGHT*(T_WAKE_LIGHT+WORK):.4f}+{I_LIGHT:.2f}*g; "
          f"C={I_BOOT*T_BOOT_DEEP+I_ACTIVE*WORK-I_DEEP*(T_BOOT_DEEP+WORK):.4f}+{I_DEEP:.2f}*g (valid for g >= T_BOOT_DEEP+WORK={T_BOOT_DEEP+WORK:.3f} s)")
    print(f"hand_calc break-even: C<A iff g>{g_ca:.4f} s; C<B iff g>{g_cb:.4f} s (strict; equality is a tie)")
    for g in (60.0, 0.25):
        qa, qb, qc = (per_cycle_charge(a, g) for a in ARMS)
        valid = "valid" if g >= T_BOOT_DEEP + WORK else "below T_BOOT_DEEP+WORK: C cannot sleep between back-to-back events, formula not valid"
        print(f"hand_calc g={g:.2f} s: A={qa:.4f} B={qb:.4f} C={qc:.4f} mA*s per cycle ({valid})")
    for regime in REGIMES:
        cfg = REGIMES[regime]
        res = run_regime(regime)
        n_ev = col(res, "A_active", "n_events")
        gap = "none" if cfg["gpio_gap"] is None else f"{cfg['gpio_gap']:.2f} s on {cfg['gpio_src']}"
        print(f"{regime} (window={cfg['window']:.0f} s timer~{cfg['timer']:.0f} s gpio_mean_gap={gap}; "
              f"events/seed {min(n_ev)}..{max(n_ev)}):")
        for arm in ARMS:
            a, s = mean_sd(col(res, arm, "avg_mA"))
            mh = [r["charge"] / 3600.0 for r in res[arm]]
            ej = [r["charge"] * V_SUPPLY / 1000.0 for r in res[arm]]
            print(f"  {arm} avg_mA {fmt_pair(a, s)} mAh {fmt_pair(*mean_sd(mh))} J {fmt_pair(*mean_sd(ej))} "
                  f"missed {fmt_pair(*mean_sd(col(res, arm, 'missed')))} wakes {fmt_pair(*mean_sd(col(res, arm, 'wakes')))} "
                  f"latency_ms {fmt_pair(*mean_sd([1000.0 * x for x in col(res, arm, 'lat')]))}")
        ok_b = all(r["ram_ok"] and r["rtc"] == r["served"] for r in res["B_light"])
        ok_c = all(r["ram_ok"] and r["rtc"] == r["served"] for r in res["C_deep"])
        lost_c = all(r["ram"] < r["served"] for r in res["C_deep"])
        print(f"  state_check: B ram==served and rtc==served on every seed: {ok_b}; "
              f"C rtc==served on every seed: {ok_c}; C ram<served (RAM lost) on every seed: {lost_c}")
        print(f"  paired B-A avg_mA: {verdict(col(res, 'B_light', 'avg_mA'), col(res, 'A_active', 'avg_mA'))}")
        print(f"  paired C-A avg_mA: {verdict(col(res, 'C_deep', 'avg_mA'), col(res, 'A_active', 'avg_mA'))}")
        print(f"  paired C-B avg_mA: {verdict(col(res, 'C_deep', 'avg_mA'), col(res, 'B_light', 'avg_mA'))}")
        print(f"  paired C-B missed: {verdict(col(res, 'C_deep', 'missed'), col(res, 'B_light', 'missed'))}")
        print(f"  paired C-B latency_ms: {verdict([1000.0 * x for x in col(res, 'C_deep', 'lat')], [1000.0 * x for x in col(res, 'B_light', 'lat')])}")
    base = run_regime("high_wake_rate")
    for label, ib, tb in (("I_BOOT=40.0 mA (= I_ACTIVE)", 40.0, T_BOOT_DEEP), ("T_BOOT_DEEP=0.100 s", I_BOOT, 0.100)):
        alt = run_regime("high_wake_rate", ib, tb)
        g_ca2, _ = breakeven(ib, tb)
        print(f"alternative {label} on high_wake_rate (same seeds; C-vs-A break-even g>{g_ca2:.4f} s):")
        print(f"  C_deep avg_mA@alt {fmt_pair(*mean_sd(col(alt, 'C_deep', 'avg_mA')))} "
              f"(default {fmt_pair(*mean_sd(col(base, 'C_deep', 'avg_mA')))})")
        print(f"  paired C-A avg_mA@alt: {verdict(col(alt, 'C_deep', 'avg_mA'), col(alt, 'A_active', 'avg_mA'))}")
    print("No winner declared: long idle favours Deep-sleep, a high wake rate erodes or reverses it, "
          "and Deep-sleep misses events on a source it did not enable")
    print("Real ESP32: 本页未运行; ESP-IDF Sleep Modes statements 以文档为准")


if __name__ == "__main__":
    main()
