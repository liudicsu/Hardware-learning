// Helpers for the handful of Python format specifications used by the sim models.

function padLeft(s: string, width: number): string {
  return s.length < width ? " ".repeat(width - s.length) + s : s;
}

// Python f"{x:{width}.{digits}f}" (format spec, no function behind it).
export function fixed(x: number, digits: number, width = 0): string {
  const s = Object.is(x, -0) ? "-" + Math.abs(x).toFixed(digits) : x.toFixed(digits);
  return padLeft(s, width);
}

// Python f"{x:{width}.{digits}e}" (format spec, no function behind it).
export function exp(x: number, digits: number, width = 0): string {
  const negativeZero = Object.is(x, -0);
  const raw = (negativeZero ? Math.abs(x) : x).toExponential(digits);
  const [mantissa, exponent] = raw.split("e");
  const n = Number(exponent);
  const sign = n < 0 ? "-" : "+";
  const s = (negativeZero ? "-" : "") + mantissa + "e" + sign + Math.abs(n).toString().padStart(2, "0");
  return padLeft(s, width);
}

// Python f"{x:{width}d}" (format spec, no function behind it).
export function int(x: number, width: number): string {
  return padLeft(Math.trunc(x).toString(), width);
}
