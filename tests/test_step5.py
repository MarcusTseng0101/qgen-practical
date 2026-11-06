"""Step 5 tests (specs/step5_iqp4_sigma_scan.md, section 7)."""
import math

import numpy as np
import pytest

from src.step2.sweep import sigma_target
from src.step4.targets import iqp4_layout
from src.step5.run import SIGMAS, default_out, q5_verdict, sigma_star, sign_changes
from src.step5.targets import TAU, iqp4_target, iqp4f_target


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_iqp4f_equals_iqp4_at_sigma_0_2_bit_for_bit(seed):
    a, b = iqp4f_target(0.2, seed), iqp4_target(0.2, seed)
    assert np.array_equal(a[0], b[0])          # p
    assert np.array_equal(a[1], b[1])          # masks
    assert np.array_equal(a[2], b[2])          # theta
    assert a[3] == b[3]                        # layout


@pytest.mark.parametrize("sigma", SIGMAS)
def test_iqp4f_weight4_angles_are_0_2_zprime_for_every_sigma(sigma):
    assert TAU == 0.2
    for seed in (0, 3):
        _, masks, theta, _ = iqp4f_target(sigma, seed)
        _, masks3, theta3, _, _ = sigma_target(sigma, seed)
        k = len(masks3)
        _, z4 = iqp4_layout(seed)
        assert np.array_equal(theta[k:], 0.2 * z4)          # weight-4: fixed, not sigma-scaled
        assert np.array_equal(theta[:k], theta3)              # weight-<=3: sigma * z, as iqp4
        assert np.array_equal(masks, iqp4_target(sigma, seed)[1])
        if sigma != 0.2:
            assert not np.array_equal(theta, iqp4_target(sigma, seed)[2])


def test_sigma_star_interpolation_on_synthetic_series():
    sig = [0.1, 0.125, 0.15, 0.175, 0.2, 0.25]
    # exact power law R = (sigma / 0.16)^-3.8: crossing at 0.16, between 0.15 and 0.175
    meds = [(s / 0.16) ** -3.8 for s in sig]
    assert sigma_star(sig, meds) == pytest.approx(0.16, rel=1e-12)
    assert sign_changes(meds) == 1
    # piecewise: crossing between the first >=1 / <1 pair, log-log linear
    meds2 = [2.0, 1.5, 0.5, 0.4, 2.0, 0.3]
    s_exp = math.exp(math.log(0.125) + (0 - math.log(1.5)) * (math.log(0.15) - math.log(0.125))
                     / (math.log(0.5) - math.log(1.5)))
    assert sigma_star(sig, meds2) == pytest.approx(s_exp, rel=1e-12)
    assert sign_changes(meds2) == 3
    # exactly 1 counts as >= 1
    assert sigma_star([0.1, 0.2], [1.0, 0.5]) == pytest.approx(0.1)
    # no >=1 -> <1 pair: undefined
    assert sigma_star(sig, [0.5] * 6) is None
    assert sigma_star(sig, [2.0] * 6) is None
    assert sigma_star(sig, [0.5, 0.6, 1.2, 2, 3, 4]) is None


def test_q5_undefined_sigma_star_rule():
    sig = [0.1, 0.125, 0.15, 0.175, 0.2, 0.25]
    # sigma*(1e4) undefined because R >= 1 everywhere -> PASS
    assert q5_verdict(0.16, None, [3, 2, 1.5, 1.2, 1.1, 1.0])["PASS"] is True
    # undefined because R < 1 everywhere -> FAIL
    assert q5_verdict(0.16, None, [0.9, 0.5, 0.4, 0.3, 0.2, 0.1])["PASS"] is False
    # both defined: compare
    assert q5_verdict(0.16, 0.18, [])["PASS"] is True
    assert q5_verdict(0.16, 0.15, [])["PASS"] is False
    assert q5_verdict(0.16, 0.16, [])["PASS"] is True
    # specs/step5_amendment1.md case 1: sigma*(inf) undefined -> FAIL whatever sigma*(1e4) is,
    # including when R >= 1 everywhere at 1e4 (case 1 takes precedence)
    for star_1e4, meds in ((0.18, []), (None, [3, 2, 1.5, 1.2, 1.1, 1.0]), (None, [0.5] * 6)):
        r = q5_verdict(None, star_1e4, meds)
        assert r["PASS"] is False and "amendment1" in r["rule"] and "case 1" in r["rule"]
    # amendment 1 case 2: sigma*(1e4) undefined with a sign change (upward crossing only) -> FAIL
    up = [0.5, 0.6, 1.2, 2, 3, 4]
    assert sigma_star(sig, up) is None and sign_changes(up) == 1
    r = q5_verdict(0.16, None, up)
    assert r["PASS"] is False and "case 2" in r["rule"]


def test_paths():
    assert default_out("iqp4f", 0.125, None, 3).as_posix().endswith("results/step5/iqp4f/sigma_0.125/N_inf/seed_3")
    assert default_out("iqp4", 0.25, 10000, 0).as_posix().endswith("results/step5/iqp4/sigma_0.25/N_10000/seed_0")
