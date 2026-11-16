"""Step 33 tests (written before the run)."""
import itertools
from math import exp

import numpy as np

from src.step1 import metrics as M1
from src.step23 import grid as Gd
from src.step33 import run as R

EARLIER_TEST_RANGES = [(920, 934), (940, 954), (960, 974), (980, 994), (1000, 1014), (1020, 1034), (1040, 1054),
                       (1060, 1074), (1080, 1094), (1100, 1114)]


def test_seeds_are_fresh():
    assert R.TEST == tuple(range(1120, 1134)) and R.SPENT_BELOW == 1114
    for a, b in EARLIER_TEST_RANGES:
        assert not set(R.TEST) & set(range(a, b))
    assert len(R.jobs()) == 56 and R.N_SHOTS == 10_000


def test_walsh_matches_brute_force():
    rng = np.random.default_rng(0)
    n = 5
    v = rng.random(1 << n)
    w = R.walsh(v)
    for S in range(1 << n):
        direct = sum(v[x] * (-1) ** bin(S & x).count("1") for x in range(1 << n))
        assert abs(w[S] - direct) < 1e-12


def test_mmd_identity_matches_direct_kernel_sum():
    rng = np.random.default_rng(1)
    n = 6
    p, q = rng.random(1 << n), rng.random(1 << n)
    p, q = p / p.sum(), q / q.sum()
    met = R.dist_metrics(p, q, n)
    d = p - q
    for s in R.SIGMAS:
        c = exp(-1 / (2 * s * s))
        K = np.array([[c ** bin(x ^ y).count("1") for y in range(1 << n)] for x in range(1 << n)])
        assert abs(d @ K @ d - met[f"mmd_{s}"]) < 1e-12


def test_G_from_orders_equals_completion_gap():
    rng = np.random.default_rng(2)
    n = Gd.N_BITS
    p, q = rng.random(1 << n), rng.random(1 << n)
    p, q = p / p.sum(), q / q.sum()
    met = R.dist_metrics(p, q, n)
    assert abs(met["G"] / M1.completion_gap(q, p, n)["G"] - 1) < 1e-10


def test_tvd_kl_fid():
    p = np.array([0.5, 0.5, 0.0, 0.0])
    q = np.array([0.25, 0.25, 0.25, 0.25])
    m = R.dist_metrics(p, q, 2)
    assert abs(m["tvd"] - 0.5) < 1e-12
    assert abs(m["kl"] - np.log(2)) < 1e-12
    assert abs(m["fid"] - 0.5) < 1e-12


def test_conditions_call_source_steps_with_source_parameters(monkeypatch):
    from src.step26 import noise as Nz26
    from src.step29 import noise as Nz29
    from src.step24 import conds as C24
    calls = []
    monkeypatch.setattr(Nz26, "noisy_grid_iqp", lambda *a, **k: calls.append(("n26", a, k)) or np.ones(4))
    monkeypatch.setattr(Nz29, "coherent_grid_iqp", lambda *a, **k: calls.append(("n29", a, k)) or np.ones(4))
    monkeypatch.setattr(Gd, "grid_iqp", lambda *a, **k: calls.append(("g23", a, k)) or np.ones(4))
    _, g, me = R.data("id", 1120)
    assert np.array_equal(g, Gd.LOCAL_GENS) and np.array_equal(me, Gd.LOCAL_ME)
    _, g, me = R.data("g01", 1121)
    assert np.array_equal(g, Gd.LOCAL_GENS) and np.array_equal(me, Gd.LOCAL_ME)
    _, g, me = R.data("mg01", 1122)
    g24, me24 = C24.model_masks("miss", 1122)
    assert np.array_equal(g, g24) and np.array_equal(me, me24) and len(g) < len(Gd.LOCAL_GENS)
    _, g, me = R.data("xf02", 1123)
    assert np.array_equal(g, Gd.LOCAL_GENS) and np.array_equal(me, Gd.LOCAL_ME)
    assert calls == [("g23", (1120,), {}), ("n26", (1121, 0.01, 0.02), {}), ("n26", (1122, 0.01, 0.02), {}),
                     ("n29", (1123, 0.2, 0.02), {})]


def test_recipe_threshold_is_step27s():
    from src.step27 import run as R27
    assert R27.THRESH == 0.75 and R27.flow_choice(0.76) == "enl" and R27.flow_choice(0.74) == "given"


def _rec(model, me3, e1m=1.0, e1e=2.0, mm=1.0, me=2.0):
    return {"model": {"tvd": model, "kl": model, "E": [e1m], "mmd_2.0": mm},
            "me3": {"tvd": me3, "kl": me3, "E": [e1e], "mmd_2.0": me}}


def test_counting_strict_missing_and_losses():
    seeds = list(R.TEST)
    X = {s: _rec(1.0, 2.0) for s in seeds[:11]}           # 11 wins
    X[seeds[11]] = _rec(2.0, 2.0)                           # tie: not a win
    # seeds 12, 13 missing: failures
    V = R.verdicts(loader=lambda c: X if c == "id" else {})
    assert V["S1"]["count"] == 11 and V["S1"]["verdict"] == "PASS"
    assert V["S2"]["count"] == 0 and V["S2"]["verdict"] == "FAIL"
    X[seeds[0]] = _rec(3.0, 2.0)
    V = R.verdicts(loader=lambda c: X if c == "id" else {})
    assert V["S1"]["count"] == 10 and V["S1"]["verdict"] == "FAIL"
    Y = {s: _rec(1.0, 2.0, e1m=3.0, e1e=2.0, mm=3.0, me=2.0) for s in seeds}   # model loses E_1 and MMD_2
    V = R.verdicts(loader=lambda c: Y if c == "xf02" else {})
    assert V["W1"]["count"] == 14 and V["W1"]["verdict"] == "PASS"
    assert V["W2"]["count"] == 14 and V["W2"]["verdict"] == "PASS"
    assert V["S4"]["count"] == 14
