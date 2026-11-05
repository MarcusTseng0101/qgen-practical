"""Step 3 tests (specs/step3_completion_vs_sigma.md, build order item 2)."""
import numpy as np
import pytest

from src.step1.bits import masks_up_to
from src.step1.models.iqp import IQPModel
from src.step1.walsh import parity_coefficients
from src.step3.run import (SIGMAS, best_restart, fit_restarts, make_pair, replay_inits,
                           run_instance)

_CACHE = {}


def pair_cached(sigma, seed):
    """make_pair is deterministic; build each pair once per test session."""
    if (sigma, seed) not in _CACHE:
        _CACHE[(sigma, seed)] = make_pair(sigma, seed)
    return _CACHE[(sigma, seed)]


@pytest.fixture(scope="module")
def o_pair_runs():
    pair = pair_cached(0.05, 0)
    return (run_instance("iqp", 0.05, 0, fits=("O",), pair=pair),
            run_instance("maxent_proj", 0.05, 0, fits=("O",), pair=pair))


@pytest.mark.parametrize("sigma", SIGMAS)
def test_maxent_proj_has_the_iqp_order3_moments(sigma):
    """maxent_proj(sigma, s) and iqp(sigma, s) agree on every parity of order <= 3, to 1e-10
    (sum of squared differences, the step-1 projection tolerance; also max |diff| <= 1e-10)."""
    pair = pair_cached(sigma, 0)
    ops = masks_up_to(12, 3)
    f_iqp = parity_coefficients(pair["p"]["iqp"])[ops]
    f_me = parity_coefficients(pair["p"]["maxent_proj"])[ops]
    assert np.sum((f_iqp - f_me) ** 2) <= 1e-10
    assert np.max(np.abs(f_iqp - f_me)) <= 1e-10, np.max(np.abs(f_iqp - f_me))
    assert pair["D3"] > 0.0
    assert abs(pair["p"]["maxent_proj"].sum() - 1) < 1e-12


def test_O_fit_identical_on_both_members_of_a_pair(o_pair_runs):
    """Same inputs and same seed: the O training residuals match to 1e-12 on the pair,
    restart by restart. Only G (against each member's own truth) may differ."""
    a, b = o_pair_runs
    assert abs(a["O_train_residual"] - b["O_train_residual"]) <= 1e-12
    assert np.max(np.abs(np.subtract(a["O_restart_residuals"], b["O_restart_residuals"]))) <= 1e-12
    assert a["O_best_restart"] == b["O_best_restart"]
    assert np.allclose(a["O_best_params"], b["O_best_params"], rtol=0, atol=1e-12)


def test_best_restart_is_lowest_residual_not_lowest_G():
    residuals = [3e-6, 1e-6, 2e-6, 1e-6]
    G = [1e-9, 5e-8, 1e-8, 1e-9]
    i = best_restart(residuals)
    assert i == 1                      # lowest residual, first on ties
    assert i != int(np.argmin(G))      # not the lowest G


@pytest.mark.parametrize("member", [0, 1])
def test_R_uses_the_lowest_residual_restart(o_pair_runs, member):
    out = o_pair_runs[member]
    res = np.array(out["O_restart_residuals"])
    G = np.array(out["O_restart_G"])
    i = int(np.argmin(res))
    assert out["O_best_restart"] == i
    assert out["O_train_residual"] == res[i] == res.min()
    assert out["O_G"] == G[i]
    assert out["O_R"] == G[i] / out["G_maxent"]
    assert len(res) == len(G) == 10


def test_replayed_restarts_match_fit_moments():
    """The per-restart replay uses fit_moments' own init draws, so its best residual equals
    fit_moments with 10 restarts."""
    pair = pair_cached(0.4, 1)
    ops, fhat = pair["ops"], pair["fhat"]
    m = IQPModel(12, gens=pair["masks"])
    r = fit_restarts(m, fhat, ops, 1, pair["p"]["iqp"], 12)
    ref = IQPModel(12, gens=pair["masks"]).fit_moments(fhat, ops, seed=1).train_residual
    assert r["rows"][r["best"]]["residual"] == ref
    inits = replay_inits(38, 1)
    assert np.array_equal(inits[0], np.random.default_rng(1).normal(0.0, 0.05, 38))
