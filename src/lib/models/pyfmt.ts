// Python str()/repr() of a float, for the few f-strings that print a bare {x}.
export function pyFloat(x: number): string {
  if (Number.isInteger(x)) return x.toFixed(1);
  const s = String(x);
  // JS switches to exponent form below 1e-6, Python below 1e-4: only the latter matters here.
  if (Math.abs(x) < 1e-4) {
    const [m, e] = x.toExponential().split("e");
    const n = Number(e);
    return m + "e" + (n < 0 ? "-" : "+") + String(Math.abs(n)).padStart(2, "0");
  }
  return s;
}

// Python f"{s:<w}" / f"{s:w}" for strings (left aligned) and f"{s:>w}".
export function ljust(s: string, w: number): string {
  return s.length < w ? s + " ".repeat(w - s.length) : s;
}
export function rjust(s: string, w: number): string {
  return s.length < w ? " ".repeat(w - s.length) + s : s;
}

// Python >= 3.12 sum() of floats: Neumaier compensated summation (CPython builtin_sum_impl).
export function pySum(xs: number[]): number {
  let f = 0.0;
  let c = 0.0;
  for (const x of xs) {
    const t = f + x;
    if (Math.abs(f) >= Math.abs(x)) c += f - t + x;
    else c += x - t + f;
    f = t;
  }
  return c !== 0 && Number.isFinite(c) ? f + c : f;
}
