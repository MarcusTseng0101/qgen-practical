"""Step 4 tests (specs/step4_misspec_finite_n.md, build order item 2)."""
import numpy as np
import pytest

from src.step1.bits import masks_up_to, popcount
from src.step1.models.iqp import IQPModel
from src.step1.targets import sample_indices
from src.step1.walsh import parity_coefficients
from src.step2.sweep import sigma_target
from src.step4.run import default_out, noise_floor, training_moments
from src.step4.targets import DELTAS, fit_mixture_moments, iqp4_layout, iqp4_target, mix_target

N = 12


def test_iqp4_adds_six_new_weight4_generators():
    p, masks, theta, layout = iqp4_target(0.2, 0)
    _, masks3, theta3, _, _ = sigma_target(0.2, 0)
    w4 = masks[len(masks3):]
    assert len(w4) == 6 and np.all(popcount(w4) == 4)
    assert len(set(w4.tolist())) == 6 and not set(w4.tolist()) & set(masks3.tolist())
    assert np.array_equal(masks[:len(masks3)], masks3) and np.array_equal(theta[:len(theta3)], theta3)
    assert np.all(theta[len(masks3):] != 0)
    # z' reused across sigma
    _, _, th1, _ = iqp4_target(0.1, 0)
    assert np.allclose(th1[len(masks3):] * 2.0, theta[len(masks3):], rtol=0, atol=1e-15)
    assert abs(p.sum() - 1) < 1e-12
    assert iqp4_layout(0)[0] != iqp4_layout(1)[0]


def test_iqp4_weight4_content_not_reproducible_by_G():
    """Spec: G's best residual on iqp4's exact moments is > 1e-8 at sigma = 0.2, seed 0
    (3 restarts, as in the grid)."""
    p, _, _, _ = iqp4_target(0.2, 0)
    fhat, ops = training_moments(p, None, 0)
    fit = IQPModel(N).fit_moments(fhat, ops, seed=0, n_restarts=3)
    assert fit.train_residual > 1e-8, fit.train_residual
    # and the weight-4 generators change the order-<=3 moments (nonzero content)
    p3 = sigma_target(0.2, 0)[0]
    assert np.max(np.abs(parity_coefficients(p)[ops] - parity_coefficients(p3)[ops])) > 1e-3


@pytest.mark.parametrize("delta", DELTAS)
def test_mix_sums_to_one(delta):
    for s in range(5):
        p = mix_target(s, delta)
        assert abs(p.sum() - 1) < 1e-12 and np.all(p > 0)


def test_mix_is_a_product_mixture():
    """Single-bit marginals equal sum_k w_k q_kj (direct check of the construction)."""
    from src.step4.targets import mix_params
    w, u = mix_params(0)
    q = 0.5 + 0.8 * u
    p = mix_target(0, 0.8)
    idx = np.arange(2**N)
    for j in range(N):
        assert abs(p[(idx >> j) & 1 == 1].sum() - w @ q[:, j]) < 1e-12
    with pytest.raises(NotImplementedError):
        fit_mixture_moments()


@pytest.mark.parametrize("Nsamp", [1000, 100000])
def test_finite_N_moments_match_sample_indices_exactly(Nsamp):
    p = sigma_target(0.2, 3)[0]
    fhat, ops = training_moments(p, Nsamp, 3)
    idx = sample_indices(p, Nsamp, 3)
    bits = (idx[:, None] >> np.arange(N)) & 1
    ref = np.array([np.mean((-1.0) ** (bits @ ((m >> np.arange(N)) & 1))) for m in ops])
    assert np.max(np.abs(fhat - ref)) <= 1e-15
    assert np.array_equal(ops, masks_up_to(N, 3))


def test_noise_floor_and_paths():
    p = sigma_target(0.1, 0)[0]
    f = parity_coefficients(p)[masks_up_to(N, 3)]
    assert noise_floor(p, None) == 0.0
    assert noise_floor(p, 1000) == pytest.approx(np.mean(1 - f**2) / 1000, rel=1e-12)
    assert default_out("mix", None, 1000, 2).as_posix().endswith("results/step4/mix/none/N_1000/seed_2")
    assert default_out("iqp4", 0.2, None, 0).as_posix().endswith("results/step4/iqp4/sigma_0.2/N_inf/seed_0")
