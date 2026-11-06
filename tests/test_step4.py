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


# ---------------- amendment 1 (specs/step4_amendment1.md, section 3) ----------------
import json

from src.step4.run import CALIB_AMEND1_FILE, target_p
from src.step4.targets import DELTAS_AMEND1, KS_AMEND1, mix_params


def _old_mix_params(seed, n=N):
    """The original (pre-amendment) K = 3 draws, written out literally."""
    rng = np.random.default_rng(5000 + seed)
    return rng.dirichlet(np.ones(3)), rng.uniform(-0.5, 0.5, (3, n))


def _old_mix_target(seed, delta, n=N):
    w, u = _old_mix_params(seed, n)
    q = 0.5 + delta * u
    X = ((np.arange(2**n)[:, None] >> np.arange(n)) & 1).astype(np.float64)
    p = np.exp(X @ np.log(q).T + (1.0 - X) @ np.log(1.0 - q).T) @ w
    return p / p.sum()


def test_mix_K3_bit_identical_to_original_draws():
    for s in range(5):
        w, u = mix_params(s, K=3)
        w0, u0 = _old_mix_params(s)
        assert np.array_equal(w, w0) and np.array_equal(u, u0)
        for dl in DELTAS:
            assert np.array_equal(mix_target(s, dl), _old_mix_target(s, dl))
            assert np.array_equal(mix_target(s, dl, K=3), mix_target(s, dl))
    # the original calibration is reproducible from the K = 3 default
    cal = json.loads((CALIB_AMEND1_FILE.parent / "calibration.json").read_text())
    from src.step2.sweep import d3
    assert d3(mix_target(0, 0.8))[0] == cal["D3_by_delta_per_seed"]["0.8"][0]


def test_grid_mix_uses_amend1_parameters():
    c = json.loads(CALIB_AMEND1_FILE.read_text())
    K, dl = c["chosen_K"], c["chosen_delta"]
    for s in (0, 3):
        tp = target_p("mix", None, s)
        assert tp["K"] == K and tp["delta"] == dl
        assert np.array_equal(tp["p"], mix_target(s, dl, K=K))


def test_calibration_amend1_has_every_candidate_and_no_completion_keys():
    c = json.loads(CALIB_AMEND1_FILE.read_text())
    for k in ("chosen_K", "chosen_delta", "D3_by_K_delta", "reference_D3"):
        assert k in c
    grid = c["D3_by_K_delta"]
    assert {int(K) for K in grid} == set(KS_AMEND1)
    for K in grid:
        assert {float(d) for d in grid[K]} == set(DELTAS_AMEND1)
        assert all(v > 0 for v in grid[K].values())
    assert (c["chosen_K"], c["chosen_delta"]) in [(K, d) for K in KS_AMEND1 for d in DELTAS_AMEND1]
    best = min(((int(K), float(d)) for K in grid for d in grid[K]),
               key=lambda x: abs(np.log(grid[str(x[0])][f"{x[1]:g}"]) - np.log(c["reference_D3"])))
    assert best == (c["chosen_K"], c["chosen_delta"])

    def keys(o):
        if isinstance(o, dict):
            for k, v in o.items():
                yield k
                yield from keys(v)
    bad = [k for k in keys(c) if k.startswith("R") or "G_" in k or "G_iqp" in k or "maxent" in k.lower()]
    assert not bad, bad
