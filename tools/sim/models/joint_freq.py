"""joint_freq.py: model the Month 3 arm joint, then read its loop in the frequency domain.

The joint is the one from pid_sim.py (J = 0.004 kg*m^2, B = 0.05 N*m per rad/s, gravity
0.4 N*m * cos(angle)), with gravity cancelled by a feedforward term so that what is left
is linear: torque -> J*q'' + B*q'. The controller runs at 200 Hz, holds its torque for one
period (zero-order hold) and, like most real firmware, applies the torque computed from a
reading one period later (one sample of delay). Units are SI: angles in rad, gains in
N*m per rad and N*m per rad/s (Month 3's 0.05 N*m per degree is 2.86 N*m per rad).
"""
import cmath
import math

J, B, GRAV, T = 0.004, 0.05, 0.4, 0.005
A = B / J                                    # 12.5 1/s, so the time constant J/B is 0.08 s
E = math.exp(-A * T)
# exact discretisation of J*q'' + B*q' = u with the torque held over each period
PHI = ((1.0, (1 - E) / A), (0.0, E))
GAM = ((T - (1 - E) / A) / (A * J), (1 - E) / (A * J))


def step(q, w, u):
    return (q + PHI[0][1] * w + GAM[0] * u, E * w + GAM[1] * u)


def identify():
    """Open-loop test: hold 0.2 N*m (plus gravity feedforward) and log the speed."""
    print("Open-loop step: 0.2 N*m from rest, speed logged at 200 Hz")
    q, w, log = 0.0, 0.0, []
    for k in range(101):
        log.append((k * T, w))
        q, w = step(q, w, 0.2)
    for t, s in log[::8][:8]:
        print(f"  t = {t:4.2f} s   speed {s:5.2f} rad/s")
    final = log[-1][1]
    t63 = next(t for t, s in log if s >= 0.632 * final)
    b = 0.2 / final
    print(f"  final speed {final:.2f} rad/s -> B = 0.2 / {final:.2f} = {b:.3f} N*m per rad/s")
    print(f"  63 % of it at t = {t63:.3f} s -> J = B x tau = {b * t63:.4f} kg*m^2")


def loop(kp, kd, w):
    """Loop gain L = C * P at angular frequency w (rad/s), with z = e^(jwT)."""
    z = cmath.exp(1j * w * T)
    det = (z - PHI[0][0]) * (z - PHI[1][1]) - PHI[0][1] * PHI[1][0]
    plant = ((z - PHI[1][1]) * GAM[0] + PHI[0][1] * GAM[1]) / det   # angle / torque
    pd = kp + kd * (1 - 1 / z) / T
    return pd * plant / z                                           # one sample of delay


def margins(kp, kd):
    """Gain and phase margins from a fine logarithmic sweep up to the Nyquist frequency."""
    ws = [10 ** (k / 2000) for k in range(-2000, int(2000 * math.log10(math.pi / T)))]
    wc = pm = wpc = gm = None
    last_ph, unwrap, prev = None, 0.0, None
    for w in ws:
        l = loop(kp, kd, w)
        ph = math.degrees(cmath.phase(l))
        if last_ph is not None and ph - last_ph > 180:
            unwrap -= 360                     # keep the phase continuous
        last_ph = ph
        ph += unwrap
        if prev is not None:
            if wc is None and abs(prev[1]) >= 1 > abs(l):
                wc, pm = w, 180 + ph
            if wpc is None and prev[2] > -180 >= ph:
                wpc, gm = w, -20 * math.log10(abs(l))
        prev = (w, l, ph)
    return wc, pm, wpc, gm


def bode(kp, kd):
    print(f"Loop gain, kp = {kp} N*m/rad, kd = {kd} N*m/(rad/s)")
    print("   w (rad/s)  |L| (dB)  phase (deg)")
    for w in (1, 3, 10, 30, 100, 300):
        l = loop(kp, kd, w)
        ph = math.degrees(cmath.phase(l))
        ph = ph - 360 if ph > 0 else ph
        print(f"  {w:9.0f}  {20 * math.log10(abs(l)):8.1f}  {ph:11.1f}")
    wc, pm, wpc, gm = margins(kp, kd)
    print(f"  gain crossover {wc:.1f} rad/s, phase margin {pm:.0f} deg")
    print(f"  phase crossover {wpc:.1f} rad/s, gain margin {gm:.1f} dB (x {10 ** (gm / 20):.1f})")


def closed(kp, kd, target=0.1, seconds=2.0):
    """Closed-loop step of 0.1 rad (about 6 degrees), small enough to stay linear."""
    q, w, u, prev = 0.0, 0.0, 0.0, 0.0
    peak, hist = 0.0, []
    for k in range(int(seconds / T)):
        rate = (q - prev) / T
        prev = q
        nxt = kp * (target - q) - kd * rate      # computed now, applied next period
        q, w = step(q, w, u)
        u = nxt
        peak = max(peak, q)
        hist.append(q - target)
    early, late = hist[100:200], hist[-100:]     # 0.5-1.0 s and the last 0.5 s
    size = lambda h: max(h) - min(h)
    ups = [k for k in range(len(hist) - 100, len(hist) - 1) if hist[k] < 0 <= hist[k + 1]]
    freq = 2 * math.pi * (len(ups) - 1) / ((ups[-1] - ups[0]) * T) if len(ups) > 2 else None
    return 100 * max(0.0, peak - target) / target, size(early), size(late), freq


def sweep():
    _, _, wpc, gm = margins(1.0, 0.0)
    print(f"P only, kp = 1.0: gain margin {gm:.1f} dB, so the loop should ring at {wpc:.1f} rad/s")
    print(f"and turn unstable near kp = 1.0 x {10 ** (gm / 20):.2f} = {10 ** (gm / 20):.2f}. Check it on 0.1 rad steps:")
    print("     kp     kd   PM (deg)  overshoot  swing 0.5-1 s  swing 1.5-2 s  ringing at")
    for kp, kd in ((0.5, 0), (1.0, 0), (2.0, 0), (2.86, 0), (6.5, 0), (7.0, 0), (2.86, 0.115)):
        _, pm, _, _ = margins(kp, kd)
        over, early, late, freq = closed(kp, kd)
        f = f"{freq:.1f} rad/s" if freq and late > 1e-4 else "-"
        o = f"{over:6.0f} %" if late < early else "  grows"
        print(f"  {kp:5.2f}  {kd:5.3f}  {pm:8.0f}   {o}   {1000 * early:8.2f} mrad  {1000 * late:9.2f} mrad  {f}")


if __name__ == "__main__":
    identify()
    print()
    bode(2.86, 0.115)
    print()
    sweep()
