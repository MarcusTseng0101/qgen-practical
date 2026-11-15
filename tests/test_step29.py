"""Step 29 tests (written before the run)."""
import numpy as np

from src.step1.bits import fwht
from src.step23 import grid as Gd
from src.step26 import noise as N26
from src.step27 import run as R27
from src.step29 import noise as Nz
from src.step29 import run as R


def test_zero_eps_equals_ideal():
    assert np.abs(Nz.coherent_grid_iqp(980, 0.0) - Gd.grid_iqp(980)).max() < 1e-12


def test_normalised():
    p = Nz.coherent_grid_iqp(981, 0.2, eta=0.02)
    assert abs(p.sum() - 1) < 1e-12 and p.min() >= 0


def test_rx_pi_is_a_bit_flip():
    # RX(pi) = -i X: on the Z-basis state between the H layers, u -> -i u[z ^ e_j]; output p is p[x ^ e_j]?
    # X before the final H layer becomes Z after it, so it is a phase on the output: p unchanged.
    # Instead check the conjugate statement: the update rule with eps = pi equals -i * (X_j u).
    N = 2**16
    rng = np.random.default_rng(0)
    u = np.exp(1j * rng.uniform(0, 2 * np.pi, N))
    j, eps = 3, np.pi
    v = np.cos(eps / 2) * u - 1j * np.sin(eps / 2) * u[N26._Z ^ (1 << j)]
    assert np.abs(v - (-1j) * u[N26._Z ^ (1 << j)]).max() < 1e-12
    a, b = fwht(u) / N, fwht(u[N26._Z ^ (1 << j)]) / N
    sgn = 1.0 - 2.0 * ((N26._Z >> j) & 1)
    assert np.abs(np.abs(b) ** 2 - np.abs(a) ** 2).max() < 1e-14 and np.abs(b - sgn * a).max() < 1e-12


def test_recipe_is_step27():
    assert R.THRESH == R27.THRESH == 0.75
    assert R.flow_choice is R27.flow_choice and R.given_graph is R27.given_graph and R.raw_floor is R27.raw_floor


def test_seeds_fresh():
    assert min(R.TEST) >= R.SPENT_BELOW >= 1054 and len(R.jobs()) == 42
