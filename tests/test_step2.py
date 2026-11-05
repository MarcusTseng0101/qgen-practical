"""Step 2 tests (specs/step2_sigma_boundary.md, build order item 2)."""
import numpy as np
import pytest

from src.step1.bits import masks_up_to
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step1.targets import make_target
from src.step1.walsh import parity_coefficients
from src.step2.sweep import (SIGMAS, d3, fit_iqp, hi_order_frac, kl, pauli_path_tv,
                             sigma_target)


@pytest.mark.parametrize("seed", [0, 3])
def test_targets_reuse_z_across_sigma(seed):
    """Same layout and the same z at every sigma; theta = sigma * z exactly."""
    ref = sigma_target(SIGMAS[0], seed)
    for sg in SIGMAS[1:]:
        p, masks, theta, z, layout = sigma_target(sg, seed)
        assert layout == ref[4]
        assert np.array_equal(masks, ref[1])
        assert np.array_equal(z, ref[3])
        assert np.array_equal(theta, sg * z)


def test_sigma_04_is_step1_biased_target():
    """At sigma = 0.4 the path passes through step 1's `biased` target (same rng draws)."""
    p, *_ = sigma_target(0.4, 0)
    p1, _ = make_target("biased", 12, 0)
    assert np.max(np.abs(p - p1)) < 1e-15


def test_oracle_support_fit_reaches_1e10_at_sigma_005():
    n = 12
    p, masks, theta, z, layout = sigma_target(0.05, 0, n)
    ops = masks_up_to(n, 3)
    r = fit_iqp(IQPModel(n, gens=masks), parity_coefficients(p)[ops], ops, seed=0)
    assert r["n_params"] == 38
    assert r["best_residual"] <= 1e-10, r["best_residual"]
    assert r["success"] and r["n_success_restarts"] >= 1


def test_d3_is_zero_for_a_maxent3_target():
    """D3 = KL(p || MaxEnt3(p)) vanishes (to 1e-10) when p is itself MaxEnt(3)."""
    n = 12
    me = MaxEntModel(n, 3)
    lam = np.random.default_rng(7).normal(0.0, 0.1, me.n_params)
    p = me.prob(lam)
    D3, q, resid = d3(p, n)
    assert abs(D3) < 1e-10, D3
    assert resid < 1e-12


def test_d3_positive_and_hi_order_frac_in_range_for_iqp_target():
    p, *_ = sigma_target(0.4, 0)
    D3, _, _ = d3(p)
    assert D3 > 1e-6
    h = hi_order_frac(p)
    assert 0.0 < h < 1.0


def test_kl_basics():
    p = np.array([0.5, 0.5, 0.0, 0.0])
    assert kl(p, p) == 0.0
    assert abs(kl(p, np.full(4, 0.25)) - np.log(2)) < 1e-15


def test_pauli_path_tv_is_a_stub():
    with pytest.raises(NotImplementedError):
        pauli_path_tv(np.zeros(3), np.array([1, 2, 4]), 2)
