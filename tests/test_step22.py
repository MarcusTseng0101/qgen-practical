"""Step 22 tests (written before the run)."""
import numpy as np

from src.step1.bits import masks_up_to
from src.step1.models.iqp import IQPModel
from src.step1.walsh import parity_coefficients
from src.step19 import data as D19
from src.step20 import pilot as P20
from src.step21 import run as R21
from src.step22 import run as R22
from src.step22 import xor as X


def test_xor_prob_matches_parity_formula():
    n, E = 6, masks_up_to(6, 3)
    w = np.where(np.random.default_rng(0).random(len(E)) < 0.3, 0.2, 0.0)
    f = parity_coefficients(X.prob(w, E, n))
    assert np.abs(f[1:] - X.parities(w, np.arange(1, 2**n), E)).max() < 1e-12


def _iqp_vs_xor(gens):
    m = IQPModel(4, gens=np.array(gens))
    th = np.array([0.3, 0.45, 0.25, 0.5][:len(gens)])
    return np.abs(m.prob(th) - X.prob(-np.log(np.cos(2 * th)), gens, 4)).max()


def test_iqp_equals_xor_without_even_cycles_and_differs_on_a_4_cycle():
    assert _iqp_vs_xor([0b0011, 0b0110, 0b1100]) < 1e-12      # independent
    assert _iqp_vs_xor([0b0011, 0b0110, 0b0101]) < 1e-12      # 3-cycle
    assert _iqp_vs_xor([0b0011, 0b1100, 0b0101, 0b1010]) > 1e-3  # 4-cycle: interference


def test_fit_recovers_exact_moments():
    n, E = 6, masks_up_to(6, 3)
    w = np.where(np.random.default_rng(1).random(len(E)) < 0.2, np.random.default_rng(2).uniform(0, .3, len(E)), 0.0)
    p = X.prob(w, E, n)
    r = X.fit(parity_coefficients(p)[E], E, E)
    assert r["residual"] < 1e-20 and np.abs(X.prob(r["w"], E, n) - p).max() < 1e-9


def test_r07_shape_and_disjoint_from_spent_runs():
    b = P20.qec_bits(R22.RUNS_B[0])
    assert b.shape == (D19.SHOTS, 16)
    spent = set(R21.RUNS) | set(D19.RUNS)
    assert not spent & set(R22.RUNS_B) and all("_r07_" in r for r in R22.RUNS_B)
