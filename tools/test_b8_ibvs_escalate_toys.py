#!/usr/bin/env python3
"""Independent numerical/contract tests for batch-8 PR2 toys; stdlib only."""
import importlib.util
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, slug):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'examples/month-9' / slug / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ibvs = load('ibvs_interaction_matrix_toy', 'visual-servoing')
esc = load('recovery_escalate_budget_toy', 'failure-recovery')
I3 = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


class IBVS(unittest.TestCase):
    def test_interaction_matrix_matches_finite_difference(self):
        # camera twist applied in the camera frame; compare s_dot with L v.
        Rw, tw = ibvs.rot_rpy(5.0, -4.0, 25.0), [0.03, -0.02, -0.7]
        base = ibvs.project(Rw, tw)
        h = 1e-6
        for j in range(6):
            v = [0.0] * 6
            v[j] = 1.0
            dv = ibvs.matvec(Rw, [h * v[i] for i in range(3)])
            R2 = ibvs.matmul(Rw, ibvs.expmap([h * v[i] for i in range(3, 6)]))
            moved = ibvs.project(R2, [tw[i] + dv[i] for i in range(3)])
            for (x, y, Z), (x2, y2, _) in zip(base, moved):
                L = ibvs.interaction(x, y, Z)
                self.assertAlmostEqual((x2 - x) / h, L[0][j], places=4)
                self.assertAlmostEqual((y2 - y) / h, L[1][j], places=4)

    def test_pose_estimate_and_scale(self):
        Rw, tw = ibvs.rot_rpy(4.0, -3.0, 40.0), [0.05, -0.04, -0.8]
        meas = [(x, y) for x, y, _ in ibvs.project(Rw, tw)]
        for k in (1.0, 1.5):
            R, t = ibvs.estimate_pose(meas, k)
            true_t = ibvs.matvec(ibvs.transpose(Rw), [-c for c in tw])
            for a, b in zip(t, true_t):
                self.assertAlmostEqual(a, k * b, places=6)
            for r1, r2 in zip(R, ibvs.transpose(Rw)):
                for a, b in zip(r1, r2):
                    self.assertAlmostEqual(a, b, places=6)

    def test_pinv_solves_normal_equations(self):
        pts = ibvs.project(ibvs.rot_rpy(3, 2, 10), [0.02, 0.01, -0.6])
        L = [row for x, y, Z in pts for row in ibvs.interaction(x, y, Z)]
        e = [0.01 * (i + 1) for i in range(8)]
        v = ibvs.pinv_apply(L, e)
        r = [a - b for a, b in zip(ibvs.matvec(L, v), e)]
        for g in ibvs.matvec(ibvs.transpose(L), r):
            self.assertAlmostEqual(g, 0.0, places=10)

    def test_wrong_scale_pbvs_final_depth_noise_free(self):
        old = ibvs.SIGMA
        ibvs.SIGMA = 0.0
        try:
            r = ibvs.run('PBVS', 'wrong_Z_k1.5', 0)
            self.assertAlmostEqual(r['t_err'], ibvs.Z_DES - ibvs.Z_DES / 1.5, places=3)
            r = ibvs.run('IBVS', 'wrong_Z_k1.5', 0)
            self.assertLess(r['sse'], 1e-4)
        finally:
            ibvs.SIGMA = old

    def test_two_point_rank_deficient(self):
        d = ibvs.project(I3, [0.0, 0.0, -ibvs.Z_DES])
        two = [row for x, y, Z in d[:2] for row in ibvs.interaction(x, y, Z)]
        ev = ibvs.jacobi_eigs(ibvs.matmul(ibvs.transpose(two), two))
        self.assertEqual(sum(1 for v in ev if abs(v) < 1e-9), 2)

    def test_shared_noise_stream_and_seeds(self):
        self.assertGreaterEqual(len(ibvs.SEEDS), 5)
        src = (ROOT / 'examples/month-9/visual-servoing/ibvs_interaction_matrix_toy.py').read_text()
        self.assertNotIn('true_pts[i][2]', src)  # no true-depth oracle in L


class Escalate(unittest.TestCase):
    def test_common_random_numbers(self):
        a, b = esc.make_stream(3), esc.make_stream(3)
        self.assertEqual([t['case'] for t in a], [t['case'] for t in b])
        self.assertEqual(a[5]['draws'], b[5]['draws'])

    def test_budget_zero_equals_retry_fallback(self):
        for s in esc.SEEDS:
            b, _ = esc.run_stream('B_retry_fallback', s)
            c, _ = esc.run_stream('C_escalate_ladder', s, 0)
            self.assertEqual(c.pop('budget_exhausted_aborts'), c['aborted'])  # every abort is budget-limited
            b.pop('budget_exhausted_aborts')
            self.assertEqual(b, c)

    def test_autonomy_not_only_path_and_budget_respected(self):
        for s in esc.SEEDS:
            b, _ = esc.run_stream('B_retry_fallback', s)
            c, rec = esc.run_stream('C_escalate_ladder', s)
            self.assertEqual(b['success'], c['auto_success'])
            self.assertGreater(c['auto_success'], c['success'] - c['auto_success'])
            self.assertLessEqual(c['operator_calls'], esc.OPERATOR_BUDGET)
            self.assertEqual(set(rec), {'escalate_reason', 'last_obs_summary', 'attempted_skills'})

    def test_infinite_retry_livelocks_only_where_primary_cannot_work(self):
        for s in esc.SEEDS:
            stream = esc.make_stream(s)
            for task in stream:
                r = esc.run_task('A_infinite_retry', task, 0)
                if esc.P_SUCCESS[task['case']][0] == 0.0:
                    self.assertTrue(r['livelock'])
                    self.assertLessEqual(r['time'], esc.DEADLINE_S)


if __name__ == '__main__':
    unittest.main(verbosity=1)
