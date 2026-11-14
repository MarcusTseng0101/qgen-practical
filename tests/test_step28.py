"""Step 28 tests (written before the run)."""
import numpy as np

from src.step23 import grid as Gd
from src.step27 import run as R27
from src.step28 import noise as Nz
from src.step28 import run as R


def test_zero_noise_equals_ideal():
    p = Nz.correlated_grid_iqp(980, 0.0, n_traj=3)
    assert np.abs(p - Gd.grid_iqp(980)).max() < 1e-12


def test_normalised():
    p = Nz.correlated_grid_iqp(981, 0.01, n_traj=50, eta=0.02)
    assert abs(p.sum() - 1) < 1e-12 and p.min() >= 0


def test_marginal_rate_matches_p():
    for k in (1, 2, 4):
        marg = 3 * 4 ** (k - 1) / (4**k - 1)          # P(a given qubit is non-identity | non-identity string)
        assert abs(Nz.q_of_k(0.01, k) * marg - 0.01) < 1e-15
    # empirical check of the string sampler for k = 2
    rng = np.random.default_rng(0)
    codes = rng.integers(1, 16, 200_000)
    assert abs(np.mean((codes & 3) != 0) - 0.8) < 0.005


def test_recipe_is_step27():
    assert R.THRESH == R27.THRESH == 0.75
    assert R.flow_choice is R27.flow_choice and R.given_graph is R27.given_graph and R.raw_floor is R27.raw_floor


def test_seeds_fresh():
    assert min(R.TEST) >= R.SPENT_BELOW >= 1034 and len(R.jobs()) == 42
