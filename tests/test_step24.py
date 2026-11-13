"""Step 24 tests (written before the run)."""
import numpy as np

from src.step1.bits import masks_up_to, popcount
from src.step1.walsh import parity_coefficients
from src.step23 import grid as Gd
from src.step24 import conds as C


def test_candidate_counts():
    g, m = C.model_masks("extra", 960)
    assert len(C.DIAGS) == 18 and len(g) == 103 and len(m) == 94
    for c in ("noise02", "noise05"):
        g, m = C.model_masks(c, 960)
        assert len(g) == 85 and len(m) == 76
    for s in (960, 973):
        g, m = C.model_masks("miss", s)
        assert len(g) < 85 and len(m) < 76
        assert set(g.tolist()) <= set(Gd.LOCAL_GENS.tolist())


def test_dropped_edges_are_true_generators_and_absent():
    tg = set(Gd.TARGET_GENS.tolist())
    for s in range(960, 974):
        d = C.dropped_edges(s)
        assert len(d) == 2 and len(set(d)) == 2
        g, m = C.model_masks("miss", s)
        for a, b in d:
            e = (1 << a) | (1 << b)
            assert e in tg
            assert e not in set(g.tolist()) and e not in set(m.tolist())
            assert all((x & e) != e for x in g.tolist())   # no candidate contains both endpoints


def test_readout_channel():
    p = Gd.grid_iqp(960)
    q = C.readout_channel(p, 0.02)
    assert abs(q.sum() - 1) < 1e-12 and q.min() >= 0
    fp, fq = parity_coefficients(p), parity_coefficients(q)
    k = popcount(np.arange(len(p)))
    assert np.abs(fq - fp * 0.96 ** k).max() < 1e-10
    assert np.abs(C.readout_channel(p, 0.0) - p).max() < 1e-14


def test_mitigation_inverts_channel_on_moments():
    p = Gd.grid_iqp(961)
    ops = masks_up_to(16, 3)
    fq = parity_coefficients(C.readout_channel(p, 0.02))[ops]
    assert np.abs(C.mitigate(fq, ops, 0.02) - parity_coefficients(p)[ops]).max() < 1e-10
