"""Step 26 tests (written before the run)."""
import numpy as np

from src.step1.walsh import parity_coefficients
from src.step23 import grid as Gd
from src.step26 import noise as Nz


def test_zero_noise_equals_ideal():
    p = Nz.noisy_grid_iqp(980, 0.0, n_traj=3)
    assert np.abs(p - Gd.grid_iqp(980)).max() < 1e-12


def test_z_error_before_final_h_is_a_bit_flip():
    # a Z on qubit j after the last gate equals a readout flip of bit j: check via the X/Z conventions
    N = 2**16
    th = Gd.grid_iqp_theta(981)
    u = np.exp(1j * (Nz._gate_signs() @ th))
    j = 5
    uz = u * (1.0 - 2.0 * ((Nz._Z >> j) & 1))
    from src.step1.bits import fwht
    a, az = fwht(u) / N, fwht(uz) / N
    p, pz = np.abs(a) ** 2, np.abs(az) ** 2
    assert np.abs(pz - p[Nz._Z ^ (1 << j)]).max() < 1e-14


def test_noise_is_normalised_and_damps_high_orders():
    p0 = Gd.grid_iqp(982)
    p = Nz.noisy_grid_iqp(982, 0.01, n_traj=200)
    assert abs(p.sum() - 1) < 1e-12 and p.min() >= 0
    f0, f = parity_coefficients(p0), parity_coefficients(p)
    from src.step1.bits import popcount
    w = popcount(np.arange(2**16))
    hi = (w >= 4) & (w <= 6)
    assert np.sum(f[hi] ** 2) < np.sum(f0[hi] ** 2)    # depolarizing shrinks correlations


def test_flipiqp_gradient_and_identity():
    from src.step1.bits import masks_up_to
    from src.step1.models.iqp import IQPModel
    from src.step26 import flipiqp as F
    ops = masks_up_to(16, 3)
    m = F.FlipIQP(16, Gd.LOCAL_GENS)
    m._B = F._bits(ops, 16)
    rng = np.random.default_rng(0)
    x = np.concatenate([rng.normal(0, .3, 85), rng.uniform(.8, 1, 16)])
    fh = rng.normal(0, .1, len(ops))
    L, g = m.loss_and_grad(x, fh, ops)
    for i in (0, 84, 85, 100):
        d = np.zeros_like(x); d[i] = 1e-6
        fd = (m.loss_and_grad(x + d, fh, ops)[0] - m.loss_and_grad(x - d, fh, ops)[0]) / 2e-6
        assert abs(fd - g[i]) < 1e-6 * max(1, abs(g[i]))
    th = x[:85]
    m.x = np.concatenate([th, np.ones(16)])
    assert np.abs(m.prob() - IQPModel(16, gens=Gd.LOCAL_GENS).prob(th)).max() < 1e-12
