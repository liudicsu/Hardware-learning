"""debounce_sim.py: why one button press can look like several, and how a time-based debounce fixes it."""
import random

STEP_MS = 0.1  # simulate in 0.1 ms steps


def bouncy_button(presses, seed=1):
    """Return a list of (time_ms, level) samples. 1 = released (pull-up), 0 = pressed."""
    rng = random.Random(seed)
    events = []  # (time_ms, new_level)
    for start, hold in presses:
        for edge_time, final in ((start, 0), (start + hold, 1)):
            t = edge_time
            level = final
            # contacts chatter for up to ~8 ms before settling
            while t < edge_time + rng.uniform(3, 8):
                events.append((t, level))
                level = 1 - level
                t += rng.uniform(0.2, 3.0)
            events.append((t, final))
    samples, level, i = [], 1, 0
    t = 0.0
    end = max(e[0] for e in events) + 50
    while t < end:
        while i < len(events) and events[i][0] <= t:
            level = events[i][1]
            i += 1
        samples.append((round(t, 1), level))
        t += STEP_MS
    return samples


def naive_presses(samples):
    """Count every HIGH->LOW transition."""
    count, last = 0, 1
    for _, level in samples:
        if last == 1 and level == 0:
            count += 1
        last = level
    return count


def debounced_presses(samples, debounce_ms):
    """Accept a new state only after the raw input has been stable for debounce_ms."""
    count, stable, last_raw, changed_at = 0, 1, 1, 0.0
    for t, level in samples:
        if level != last_raw:
            last_raw, changed_at = level, t
        if last_raw != stable and t - changed_at >= debounce_ms:
            stable = last_raw
            if stable == 0:
                count += 1
    return count


if __name__ == "__main__":
    presses = [(100, 300), (700, 150), (1200, 400), (2000, 80), (2500, 250)]  # (start ms, hold ms)
    samples = bouncy_button(presses)
    print(f"real presses:        {len(presses)}")
    print(f"naive edge count:    {naive_presses(samples)}")
    for d in (2, 10, 20, 50):
        print(f"debounced, {d:>2} ms:   {debounced_presses(samples, d)}")
