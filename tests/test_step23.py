"""Step 23 tests (written before the run)."""
import numpy as np

from src.step1.bits import masks_up_to, popcount
from src.step1.models.iqp import IQPModel
from src.step1.walsh import parity_coefficients
from src.step23 import grid as Gd


def test_grid_masks():
    assert len(Gd.EDGES) == 24 and len(Gd.PLAQS) == 9 and len(Gd.TRIPLES) == 36
    assert len(Gd.TARGET_GENS) == 49 and len(Gd.LOCAL_GENS) == 85 and len(Gd.LOCAL_ME) == 76
    assert set(Gd.TARGET_GENS) <= set(Gd.LOCAL_GENS) and set(Gd.LOCAL_ME) <= set(Gd.LOCAL_GENS)
    assert popcount(Gd.LOCAL_ME).max() == 3
    assert 0b0011 in set(Gd.LOCAL_GENS.tolist()) and 0b0101 not in set(Gd.LOCAL_GENS.tolist())


def test_target_in_local_family_and_fit_from_truth():
    p = Gd.grid_iqp(920)
    m = IQPModel(16, gens=Gd.LOCAL_GENS)
    th = np.zeros(85)
    pos = {int(g): i for i, g in enumerate(Gd.LOCAL_GENS)}
    th[[pos[int(g)] for g in Gd.TARGET_GENS]] = Gd.grid_iqp_theta(920)
    assert np.abs(m.prob(th) - p).max() < 1e-12
    ops = masks_up_to(16, 3)
    f = m.fit_moments(parity_coefficients(p)[ops], ops, seed=0, n_restarts=1, theta0=th)
    assert f.train_residual < 1e-6


def test_me_local_matches_its_moments_and_completes_grid_ising():
    p = Gd.grid_ising(940)
    assert abs(p.sum() - 1) < 1e-12
    ops = masks_up_to(16, 3)
    fh = parity_coefficients(p)[ops]
    me = Gd.MaxEntOn(16, Gd.LOCAL_ME)
    q = me.prob(me.fit_moments(fh, ops).params)
    pos = {int(a): i for i, a in enumerate(ops)}
    own = parity_coefficients(q)[Gd.LOCAL_ME]
    assert np.abs(own - fh[[pos[int(a)] for a in Gd.LOCAL_ME]]).max() < 1e-6
    assert np.abs(q - p).max() < 1e-6   # grid Ising is in me_local's family
