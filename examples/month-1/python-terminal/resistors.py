"""resistors.py — dataclass Resistor, series/parallel helpers."""

from dataclasses import dataclass


@dataclass
class Resistor:
    """A resistor with a nominal value and a tolerance (0.05 = 5 %)."""

    ohms: float
    tolerance: float = 0.05

    def min(self) -> float:
        """Lowest value within tolerance."""
        return self.ohms * (1 - self.tolerance)

    def max(self) -> float:
        """Highest value within tolerance."""
        return self.ohms * (1 + self.tolerance)


def series(*rs: Resistor) -> Resistor:
    """Resistors in series: values add up, tolerances add too."""
    if not rs:
        raise ValueError("series() needs at least one resistor")
    tolerance = sum(r.tolerance for r in rs)
    return Resistor(ohms=sum(r.ohms for r in rs), tolerance=tolerance)


def parallel(*rs: Resistor) -> Resistor:
    """Resistors in parallel: conductances add up."""
    if not rs:
        raise ValueError("parallel() needs at least one resistor")
    conductance = sum(1 / r.ohms for r in rs)
    return Resistor(ohms=1 / conductance)


if __name__ == "__main__":
    r2k2 = Resistor(2_200)
    print(r2k2)
    print(f"range: {r2k2.min():.0f}–{r2k2.max():.0f} Ω")

    result = parallel(Resistor(10_000), Resistor(10_000))
    print(f"parallel: {result.ohms:.0f} Ω")

    chain = series(Resistor(1_000), Resistor(4_700))
    print(f"series: {chain.ohms:.0f} Ω")
