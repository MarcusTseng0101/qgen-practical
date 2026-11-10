"""Step 17 tests (written before the run; specs/step17_real_mnist16.md section 4)."""
import numpy as np

from src.step14 import run as r14
from src.step17 import data as D
from src.step17 import pilot as P
from src.step17 import run as r17


def test_corrected_gap_hand_example():
    n = P.n
    q_test = np.zeros(2**n); q_test[0] = 1.0           # all parities = +1, so the noise term is 0
    q_model = np.full(2**n, 2.0**-n)                     # all non-empty parities = 0
    g = P.corrected_gap(q_model, q_test, 100)
    assert abs(g["G"] - 1.0) < 1e-12 and abs(g["G_raw"] - 1.0) < 1e-12
    q_test = np.full(2**n, 2.0**-n)                      # parities 0: noise term 1/N per moment
    g = P.corrected_gap(q_test, q_test, 100)
    assert abs(g["G_raw"]) < 1e-20 and abs(g["G"] + 0.01) < 1e-12


def test_data_pinned():
    assert D.fetch() == r17.SHA
    b = D.bits()
    assert b.shape == (70_000, 16) and set(np.unique(b)) <= {0, 1}


def test_fresh_splits():
    assert r17.SEEDS == tuple(range(100, 120)) and not set(P.SEEDS) & set(r17.SEEDS)


def test_gate_is_step14s():
    assert P.floor_of is r14.floor_of and P.excess is r14.excess and P.TAU == 1e-2
