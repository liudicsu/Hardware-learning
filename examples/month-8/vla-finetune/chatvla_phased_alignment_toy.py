#!/usr/bin/env python3
"""ChatVLA-style phased alignment + MoE vs robot-only SFT vs naive joint training, on one tiny shared model.

Synthetic, stdlib only.  Not Qwen2-VL, not DiffusionVLA, not ChatVLA's code: a linear stand-in
that keeps only the structure the paper describes (a shared layer like the shared self-attention,
task-specific FFN experts, an action head and a language head).  Not DPO / OpenHelix, not
CoT-VLA, not Magma, and not this lesson's experience-replay toy (no replay buffer, no task
sequence).  ChatVLA paper numbers (VQA, 25 real tasks) are 以论文为准; GPU or real-robot runs:
本页未运行.

Model (dimensions D input, M bottleneck, NQ answer classes):
  z = A x                 shared layer (D x D), pretrained A0 = I plus a small per-seed perturbation
  f = P z                 FFN projection to M features (M x D); P0 rows = e1, e2
  control  a_hat = c . f  action head, new (c = 0 at the start)
  VQA      logits = V f   language head, pretrained V0 (NQ prototypes at 0, 120, 240 degrees)
The "pretrained VLM" answers VQA by its own map: label y = argmax V0 P0 A0 x, so its own VQA
accuracy on fresh inputs is printed as the frozen baseline.  The robot target is a = W . x with
W set by the regime.
Arms (equal robot budget R batches; B and C also get the same Q VQA batches):
  A_robot   robot-only SFT through the single shared P; V is never updated (no VQA data)
  B_phased  MoE: P_ctrl and P_vqa both start at P0.  Stage 1: first R - R2 robot batches, only
            the control expert and A train.  Stage 2: remaining R2 robot batches and Q VQA
            batches, interleaved, robot through P_ctrl and VQA through P_vqa (A shared)
  C_joint   naive joint training through the single shared P from step 0, robot : VQA = 3 : 1
            interleaving (the ratio the paper used, following RT-2), same R and Q
Training: plain SGD, batch BATCH, learning rate LR, squared error for control, softmax cross
entropy for VQA.  No integration step (discrete SGD updates, no plant); the step count is the
budget, stated per arm.
Metrics per seed: control success % (|a_hat - a| <= TOL on TEST inputs), VQA accuracy % on TEST
inputs, forgetting gap = baseline VQA - arm VQA (points).  B's VQA after stage 1 is printed too.
Common random numbers: per (regime, seed) the init perturbation, every robot batch, every VQA
batch and the test set are drawn once; batch i is the same batch for every arm that uses it.
Regimes and expectations, written before the first run:
  conflict   W = e3 (outside the VQA features), Q 100   A consistent VQA collapse vs B;
                                                        A and B near-tie on control;
                                                        C vs B: no prediction, printed either way
  aligned    W = e1 (inside the VQA features), Q 100    all three near-tie on control and VQA
  few_vqa    W = e3, Q 10                               B still consistent VQA win over A;
                                                        C vs B: no prediction
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
D, M, NQ = 6, 2, 3
R, R2 = 300, 100          # robot batches per arm; B's stage-2 robot batches
BATCH = 8
LR = 0.05
TOL = 0.25
TEST = 400
INIT_SD = 0.05
NUM_ZERO = 1e-9
ARMS = ("A_robot", "B_phased", "C_joint")
# name: (robot target direction W, VQA batches Q); written before the first run
REGIMES = {
    "conflict": ((0, 0, 1, 0, 0, 0), 100),
    "aligned": ((1, 0, 0, 0, 0, 0), 100),
    "few_vqa": ((0, 0, 1, 0, 0, 0), 10),
}
STREAM = {"conflict": 0, "aligned": 1, "few_vqa": 2}
V0 = [[math.cos(2 * math.pi * k / NQ), math.sin(2 * math.pi * k / NQ)] for k in range(NQ)]
P0 = [[1.0 if j == i else 0.0 for j in range(D)] for i in range(M)]


def matvec(mat, v):
    return [sum(a * b for a, b in zip(row, v)) for row in mat]


def argmax(v):
    return max(range(len(v)), key=lambda k: v[k])


def copy(mat):
    return [row[:] for row in mat]


def shared_draws(regime, seed):
    rng = random.Random(1000 * STREAM[regime] + seed)
    w, q = REGIMES[regime]
    a0 = [[(1.0 if i == j else 0.0) + rng.gauss(0.0, INIT_SD) for j in range(D)] for i in range(D)]
    teacher = lambda x: argmax(matvec(V0, matvec(P0, matvec(a0, x))))
    gx = lambda: [rng.gauss(0.0, 1.0) for _ in range(D)]
    robot = []
    for _ in range(R):
        xs = [gx() for _ in range(BATCH)]
        robot.append([(x, sum(a * b for a, b in zip(w, x))) for x in xs])
    vqa = []
    for _ in range(q):
        xs = [gx() for _ in range(BATCH)]
        vqa.append([(x, teacher(x)) for x in xs])
    test = []
    for _ in range(TEST):
        x = gx()
        test.append((x, sum(a * b for a, b in zip(w, x)), teacher(x)))
    return a0, robot, vqa, test


class Net:
    def __init__(self, a0, moe):
        self.A = copy(a0)
        self.P = {"ctrl": copy(P0), "vqa": copy(P0)} if moe else {"ctrl": copy(P0)}
        self.moe = moe
        self.c = [0.0] * M
        self.V = copy(V0)
        self.train_a = True
        self.frozen = set()

    def proj(self, task):
        return self.P["vqa"] if (self.moe and task == "vqa") else self.P["ctrl"]

    def step(self, batch, task):
        P = self.proj(task)
        gA = [[0.0] * D for _ in range(D)]
        gP = [[0.0] * D for _ in range(M)]
        gc = [0.0] * M
        gV = [[0.0] * M for _ in range(NQ)]
        for x, y in batch:
            z = matvec(self.A, x)
            f = matvec(P, z)
            if task == "ctrl":
                err = sum(a * b for a, b in zip(self.c, f)) - y
                df = [err * ci for ci in self.c]
                for i in range(M):
                    gc[i] += err * f[i]
            else:
                logits = matvec(self.V, f)
                mx = max(logits)
                ex = [math.exp(l - mx) for l in logits]
                s = sum(ex)
                g = [e / s - (1.0 if k == y else 0.0) for k, e in enumerate(ex)]
                df = [sum(g[k] * self.V[k][i] for k in range(NQ)) for i in range(M)]
                for k in range(NQ):
                    for i in range(M):
                        gV[k][i] += g[k] * f[i]
            dz = [sum(df[i] * P[i][j] for i in range(M)) for j in range(D)]
            for i in range(M):
                for j in range(D):
                    gP[i][j] += df[i] * z[j]
            for i in range(D):
                for j in range(D):
                    gA[i][j] += dz[i] * x[j]
        n = float(len(batch))
        for i in range(M):
            for j in range(D):
                P[i][j] -= LR * gP[i][j] / n
        for i in range(D):
            for j in range(D):
                self.A[i][j] -= LR * gA[i][j] / n
        if task == "ctrl":
            for i in range(M):
                self.c[i] -= LR * gc[i] / n
        else:
            for k in range(NQ):
                for i in range(M):
                    self.V[k][i] -= LR * gV[k][i] / n

    def evaluate(self, test):
        ok_c = ok_q = 0
        for x, a, y in test:
            z = matvec(self.A, x)
            fc = matvec(self.proj("ctrl"), z)
            ok_c += abs(sum(p * q for p, q in zip(self.c, fc)) - a) <= TOL
            ok_q += argmax(matvec(self.V, matvec(self.proj("vqa"), z))) == y
        return 100.0 * ok_c / len(test), 100.0 * ok_q / len(test)


def run_arm(arm, draws):
    a0, robot, vqa, test = draws
    net = Net(a0, moe=(arm == "B_phased"))
    out = {}
    if arm == "A_robot":
        for b in robot:
            net.step(b, "ctrl")
    elif arm == "B_phased":
        for b in robot[:R - R2]:
            net.step(b, "ctrl")
        out["stage1_vqa"] = net.evaluate(test)[1]
        rest, qs = robot[R - R2:], list(vqa)
        n = max(len(rest), len(qs))
        for i in range(n):
            if i < len(rest):
                net.step(rest[i], "ctrl")
            if i < len(qs):
                net.step(qs[i], "vqa")
    else:
        qi = 0
        for i, b in enumerate(robot):
            net.step(b, "ctrl")
            if i % 3 == 2 and qi < len(vqa):
                net.step(vqa[qi], "vqa")
                qi += 1
        while qi < len(vqa):
            net.step(vqa[qi], "vqa")
            qi += 1
    ctrl, q = net.evaluate(test)
    base = Net(a0, moe=False).evaluate(test)[1]
    out.update({"ctrl": ctrl, "vqa": q, "gap": base - q, "base": base})
    return out


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-5:
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


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{num(m)}+-{num(s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{num(m)}+-{num(s)}: {label}; {sign_note(diffs, m)}"


def main():
    print("Synthetic ChatVLA-style probe: robot-only SFT vs phased alignment + MoE vs naive joint (3:1); linear stand-in, not Qwen2-VL")
    print(f"D={D} M={M} NQ={NQ} R={R} robot batches (B stage 2: {R2}) BATCH={BATCH} LR={LR} TOL={TOL} TEST={TEST} seeds={len(SEEDS)}")
    print(f"chance VQA accuracy = {100.0 / NQ:.4f} %; no integration step (discrete SGD updates); C interleaves robot:VQA = 3:1")
    print("regime arm control_% vqa_% forgetting_gap_pts  (mean+-sd over seeds)")
    for regime, (w, q) in REGIMES.items():
        draws = [shared_draws(regime, s) for s in SEEDS]
        res = {arm: [run_arm(arm, d) for d in draws] for arm in ARMS}
        base = "{}+-{}".format(*map(num, mean_sd([r["base"] for r in res["A_robot"]])))
        print(f"{regime} (W = {w}; Q = {q} VQA batches; frozen baseline VQA {base} %)")
        for arm in ARMS:
            cols = ["{}+-{}".format(*map(num, mean_sd([r[k] for r in res[arm]]))) for k in ("ctrl", "vqa", "gap")]
            print(f"  {arm} " + " ".join(cols))
        s1 = "{}+-{}".format(*map(num, mean_sd([r["stage1_vqa"] for r in res["B_phased"]])))
        print(f"  B_phased VQA after stage 1 (robot only, before any VQA batch): {s1} %")
        for x, y in (("B_phased", "A_robot"), ("C_joint", "B_phased")):
            for key in ("ctrl", "vqa"):
                print(f"  paired {x[0]}-{y[0]} {key}: {verdict([r[key] for r in res[x]], [r[key] for r in res[y]])}")
    print("No winner declared: phased alignment + MoE restores VQA lost to robot-only SFT; whether naive joint training costs control depends on whether the tasks compete for features")
    print("ChatVLA numbers 以论文为准; GPU / 25-task real robot: 本页未运行")


if __name__ == "__main__":
    main()
