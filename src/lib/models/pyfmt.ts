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
