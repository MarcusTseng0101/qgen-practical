"""Step 25 tests (written before the run)."""
import numpy as np

from src.step1.bits import masks_up_to
from src.step1.walsh import parity_coefficients
from src.step23 import grid as Gd
from src.step25 import run as R


def test_enlarged_graph():
    assert len(R.ENLARGED) == 103
    assert set(Gd.LOCAL_GENS.tolist()) <= set(R.ENLARGED.tolist())
    for s in (980, 993):
        g, _ = R.given_graph("miss", s)
        assert set(g.tolist()) < set(R.ENLARGED.tolist())   # enlargement restores the missing couplers


def test_mitigated_floor_reduces_at_eta0():
    p = Gd.grid_iqp(980)
    ops = masks_up_to(16, 3)
    f = parity_coefficients(p)[ops]
    assert abs(R.mitigated_floor(f, ops, 0.0, 10_000) - float(np.sum(1 - f**2) / 10_000)) < 1e-15


def test_pipeline_from_truth_no_flag():
    p = Gd.grid_iqp(980)
    ops = masks_up_to(16, 3)
    th = np.zeros(85)
    pos = {int(g): i for i, g in enumerate(Gd.LOCAL_GENS)}
    th[[pos[int(g)] for g in Gd.TARGET_GENS]] = Gd.grid_iqp_theta(980)
    out = R.pipeline(parity_coefficients(p)[ops], ops, 0.0, None, Gd.LOCAL_GENS, 0, restarts=1, theta0=th)
    assert out["resid1"] < 1e-6 and not out["flag"]
    assert np.abs(out["q"] - p).max() < 1e-8
