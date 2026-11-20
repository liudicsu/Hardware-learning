#!/usr/bin/env python3
"""Synthetic CoBoVLA paraphrase-robust code stand-in.

Stdlib only. Shared tasks, shared canonical instructions, shared paraphrases
and shared scenes (common random numbers). Not a real LIBERO / LIBERO-Para
run and not VLA weights.

This is not RDT2's residual VQ action codebook, not VQ-BeT, not CoT-VLA,
not MolmoAct, not InternVLA-M1, not SmolVLA async inference, and not LIBERO-X.

Arms:
  A_coupled -- language-coupled stand-in: the action path can change when
    the wording changes, even if the intent is the same. The actor scores
    character 2-grams against the canonical sentences only.
  B_codes -- codebook-decoupled stand-in: a synonym table maps paraphrases
    of the same instruction to the same discrete step codes; the actor
    never sees the words, so those paraphrases produce the same behaviour.
  C_foreign -- broken codes: the actor is given the step codes of a
    different task.

A named alternative on the same seeds, not adopted, replaces the discrete
step code with a continuous pre-quantization mixture of the correct code
and a neighbouring task code.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.

Paper figures 91 %, 27.2 %, 91.4 %, 82.8 %, 81.1 %, 36.5 % and 17 ms stay
以论文为准 and are not toy outputs. Real LIBERO / LIBERO-Para / GPU: 本页未运行.
"""
import collections
import math
import random
import re
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000
NGRAM = 2
# Named alternative, not adopted: use the wording-sensitive 2-gram scores
# as a continuous pre-quantization vector and pick the nearest task code,
# instead of a discrete synonym-table code or a foreign discrete code.

TASKS = ("pick_cup", "open_drawer", "place_bowl")
# Canonical wording and official unseen paraphrases, written before the first run.
# Stop-words are ignored by the coupled 2-gram scorer.
CANONICAL = {
    "pick_cup": "pick the red cup",
    "open_drawer": "open the drawer",
    "place_bowl": "place the bowl on the plate",
}
PARAPHRASES = {
    "pick_cup": ("grab the crimson mug", "lift the scarlet tumbler"),
    "open_drawer": ("pull the cupboard open", "slide the bin out"),
    "place_bowl": ("set the dish on the saucer", "rest the basin on the saucer"),
}
STOP = frozenset("the a an to on of in out up please could you that this".split())

# Foreign-code derangement: each task is sent the next task's step code.
FOREIGN = {
    "pick_cup": "open_drawer",
    "open_drawer": "place_bowl",
    "place_bowl": "pick_cup",
}

ARMS = ("A_coupled", "B_codes", "C_foreign")
METRICS = ("success",)
PAIRS = (("B", "A"), ("B", "C"), ("C", "A"))
ARM_FROM_LETTER = {"A": "A_coupled", "B": "B_codes", "C": "C_foreign"}

REGIMES = {
    "canonical": (
        "canonical",
        "A and B may near-tie on task success - keep",
    ),
    "paraphrase": (
        "paraphrase",
        "B consistent more stable behaviour / higher stand-in success than A - keep",
    ),
}


def content_text(text):
    tokens = [t for t in re.findall(r"[a-z]+", text.lower()) if t not in STOP]
    return " ".join(tokens)


def char_ngrams(text, n=NGRAM):
    s = content_text(text)
    grams = [s[i : i + n] for i in range(max(0, len(s) - n + 1))]
    return collections.Counter(grams)


def cosine(a, b):
    keys = set(a) | set(b)
    num = sum(a[k] * b[k] for k in keys)
    da = math.sqrt(sum(v * v for v in a.values()))
    db = math.sqrt(sum(v * v for v in b.values()))
    return num / (da * db) if da and db else 0.0


CANON_GRAMS = {task: char_ngrams(text) for task, text in CANONICAL.items()}
# B's synonym table: every official wording of a task shares one discrete code.
SYNONYM = {}
for task, text in CANONICAL.items():
    SYNONYM[text] = task
for task, texts in PARAPHRASES.items():
    for text in texts:
        SYNONYM[text] = task


def coupled_scores(text):
    grams = char_ngrams(text)
    return {task: cosine(grams, CANON_GRAMS[task]) for task in TASKS}


def coupled_choice(text):
    scores = coupled_scores(text)
    best = max(scores.values())
    # Deterministic tie-break in TASKS order; no hidden seed retune.
    for task in TASKS:
        if scores[task] == best:
            return task, scores
    return TASKS[0], scores


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


def actor(step_code, scene_task):
    # The actor never sees the words; it only acts on the discrete code.
    # The scene is shared and does not override a wrong code.
    del scene_task
    return step_code


def continuous_code(text):
    # Stand-in pre-quantization vector: wording-sensitive 2-gram scores,
    # used in place of a discrete step code, then nearest-task quantization.
    # Not a paper percentage, and not the official C arm.
    chosen, _ = coupled_choice(text)
    return chosen


def items_for(kind):
    out = []
    for task in TASKS:
        if kind == "canonical":
            out.append((task, CANONICAL[task]))
        else:
            for text in PARAPHRASES[task]:
                out.append((task, text))
    return out


def evaluate_item(arm, task, text, mode="official"):
    if arm == "A_coupled":
        chosen, _ = coupled_choice(text)
    elif arm == "B_codes":
        chosen = actor(SYNONYM[text], task)
    elif mode == "continuous":
        chosen = actor(continuous_code(text), task)
    else:
        chosen = actor(FOREIGN[task], task)
    return 1.0 if chosen == task else 0.0


def run_seed(kind, seed, mode="official"):
    # Shared item list and scene order under CRN; the score itself is
    # deterministic given the declared wording table.
    items = list(items_for(kind))
    rng = random.Random(f"{kind}/{mode}/{seed}")
    rng.shuffle(items)
    scores = {arm: [] for arm in ARMS}
    for task, text in items:
        for arm in ARMS:
            scores[arm].append(evaluate_item(arm, task, text, mode=mode))
    return {arm: sum(vals) / len(vals) for arm, vals in scores.items()}


def run_regime(kind, mode="official"):
    per_arm = {arm: {metric: [] for metric in METRICS} for arm in ARMS}
    for seed in SEEDS:
        row = run_seed(kind, seed, mode=mode)
        for arm in ARMS:
            per_arm[arm]["success"].append(row[arm])
    return per_arm


def print_regime(label, kind, declared, mode="official"):
    res = run_regime(kind, mode=mode)
    print(f"declared expectation {label}: {declared}")
    print(f"regime {label}  (mean+-sd over seeds)")
    for arm in ARMS:
        m, s = mean_sd(res[arm]["success"])
        print(f"  {arm} success {fmt_pair(m, s)}")
    for left, right in PAIRS:
        la, ra = ARM_FROM_LETTER[left], ARM_FROM_LETTER[right]
        print(f"  paired {left}-{right} success: {verdict(res[la]['success'], res[ra]['success'])}")
    return res


def hand_calc_lines():
    print(f"hand_calc 20 percent small-vs-clear factor = {num(SMALL_FRAC)}")
    print(f"hand_calc NGRAM={NGRAM}")
    print("hand_calc alternative: continuous pre-quantization uses 2-gram scores in place of a discrete code (not adopted)")
    print(f"hand_calc tasks={','.join(TASKS)}")
    for task in TASKS:
        print(f"hand_calc canonical {task}: {CANONICAL[task]!r}")
        for text in PARAPHRASES[task]:
            scores = coupled_scores(text)
            chosen, _ = coupled_choice(text)
            parts = ", ".join(f"{t}={num(scores[t])}" for t in TASKS)
            print(f"hand_calc 2-gram cosine {text!r}: {parts}; coupled_choice={chosen}")


def main():
    print("Synthetic CoBoVLA paraphrase-code stand-in; not a LIBERO or GPU VLA run")
    print(
        "declared "
        f"NGRAM={NGRAM} SMALL_FRAC={num(SMALL_FRAC)} "
        f"seeds={','.join(str(s) for s in SEEDS)}"
    )
    hand_calc_lines()
    print("declared arms: A_coupled scores char 2-grams against canonical wording only; B_codes uses a synonym table then an actor that never sees the words; C_foreign feeds a different task's step codes")
    print("paper_authors=Mehul Arora, Dhruv Agarwal, Ambuj Agrawal (abs / title-page order; 以论文为准)")
    print("paper_title_page=no equal-contribution or corresponding typography; prose contributions list is not a footnote mark (以论文为准)")
    print("paper_version=arXiv 2611.22395 v1, submitted 2026-11-17")
    print("paper_figures=success 91 % when correctly encoded and 27.2 % otherwise; 91.4 % on LIBERO-Goal vs 82.8 % SmolVLA; 81.1 % on LIBERO-Para (4,092 unseen paraphrases) vs 36.5 % paraphrase-fine-tuned SmolVLA LoRA; 17 ms per control step (arXiv 2611.22395 v1; 以论文为准, not toy outputs)")
    print("Regimes and parameters were written before the first run")
    print("Common random numbers: the tasks, canonical instructions, official paraphrases and scene order are shared across arms at each regime and seed")
    print("Assumptions: character 2-gram cosine is a wording-sensitive stand-in, not a trained text encoder; B's synonym table is the stand-in for paraphrase-shared step codes; the actor never sees the words; C uses a fixed foreign-code derangement; success is whether the acted task matches the intended task")
    print("Paper figures 以论文为准")
    print("Real LIBERO / LIBERO-Para / GPU: 本页未运行")
    print("declared canonical: A and B may near-tie on task success - keep")
    print("declared paraphrase: B consistent more stable behaviour / higher stand-in success than A - keep")
    print("declared C_foreign: C loses because it is given step codes from a different task - lose kept")
    for name, (kind, declared) in REGIMES.items():
        print_regime(name, kind, declared)
    print("alternative same seeds continuous pre-quantization vector (not adopted)")
    print("hand_calc official C uses foreign discrete codes vs alternative continuous pre-quantization vector")
    # Report the alternative on both official regimes, same seeds.
    print_regime(
        "canonical_continuous",
        "canonical",
        "alternative continuous pre-quantization vector, same seeds, not adopted",
        mode="continuous",
    )
    print_regime(
        "paraphrase_continuous",
        "paraphrase",
        "alternative continuous pre-quantization vector, same seeds, not adopted",
        mode="continuous",
    )
    print("No real LIBERO, LIBERO-Para, or GPU VLA was started")
    print("No winner is universal: canonical wording may near-tie; unseen paraphrases are where discrete shared step codes matter, and foreign or pre-quantization-replaced codes leave that robustness unearned")


if __name__ == "__main__":
    main()
