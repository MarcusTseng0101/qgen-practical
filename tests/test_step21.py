"""Step 21 tests (written before the run)."""
import numpy as np

from src.step1.walsh import coefficients_by_order, empirical_distribution
from src.step17.pilot import LEVELS, corrected_gap
from src.step21 import run as r21


def test_runs_are_the_16_spent_runs():
    assert len(r21.RUNS) == 16 and len(set(r21.RUNS)) == 16 and r21.SPLITS == (100, 101)


def test_gap_terms_match_step17_corrected_gap():
    rng = np.random.default_rng(0)
    qa, qb = rng.dirichlet(np.ones(2**16)), rng.dirichlet(np.ones(2**16))
    rows = rng.integers(0, 2**16, 3000)
    qt = empirical_distribution(rows, 16)
    ft = coefficients_by_order(qt, 16, LEVELS)
    fa = coefficients_by_order(qa, 16, LEVELS)
    assert abs(r21.gap_terms(fa, ft, 3000, LEVELS) - corrected_gap(qa, qt, 3000)["G"]) < 1e-12


def test_bootstrap_ci_contains_point_for_identical_models(monkeypatch):
    monkeypatch.setattr(r21, "B", 20)
    rng = np.random.default_rng(1)
    qa = rng.dirichlet(np.ones(2**16))
    fa = coefficients_by_order(qa, 16, (4,))
    ci = r21.boot_ci(fa, fa, rng.integers(0, 2**16, 2000), (4,), 0)
    assert ci["point"] == 0 and ci["lo"] == 0 and ci["hi"] == 0
